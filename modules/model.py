import re
import sqlite3
from typing import ClassVar

import instructor
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam
from pydantic import BaseModel, Field, field_validator

# from modules.database.custom_db_schema import CustomDBSchema
from modules.database.db import get_db_schema
from modules.settings import DB_FILE, MODEL, OLLAMA_BASE_URL, OLLAMA_CONTEXT_WINDOW


class TranslatorResponse(BaseModel):
    """Structured response returned by the SQL translator."""

    sql_query: str = Field(description="A valid SQLite query using only filters explicitly stated by the user.")

    @field_validator("sql_query")
    @classmethod
    def validate_sql_query(cls, value: str) -> str:
        """Reject non-read-only or non-compiling SQL before it reaches the UI."""
        query = value.strip()
        if not query:
            print("field_validator: sql_query: SQL query is empty.")
            raise ValueError("sql_query cannot be empty")

        print(f"field_validator: sql_query: Validating SQL query:\\n{query}")
        if "```" in query:
            print("field_validator: sql_query: SQL query contains markdown fences.")
            raise ValueError("sql_query must not contain markdown fences")

        if re.search(
            r"\bdate\s*=\s*['\"](?:\d{8}|\d{4}[-.]\d{2}[-.]\d{2})['\"]",
            query,
            re.IGNORECASE,
        ):
            print("field_validator: sql_query: Date must be an unquoted YYYYMMDD integer.")
            raise ValueError("date filters must use an unquoted YYYYMMDD integer")

        if re.search(r"\bdescription\s*=\s*(?:NULL|'NULL'|\"NULL\")", query, re.IGNORECASE):
            print("field_validator: sql_query: SQL query contains an invented NULL description filter.")
            raise ValueError("description must not be filtered with NULL unless explicitly requested")

        first_keyword = re.match(r"^([A-Za-z]+)\b", query)
        if first_keyword is None or first_keyword.group(1).upper() not in {"SELECT", "WITH"}:
            print("field_validator: sql_query: SQL query is not read-only.")
            raise ValueError("sql_query must be a read-only SELECT or WITH query")

        if re.search(
            r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|REPLACE|TRUNCATE|ATTACH|DETACH|PRAGMA|VACUUM)\b",
            query,
            re.IGNORECASE,
        ):
            print("field_validator: sql_query: SQL query contains a forbidden write or database command.")
            raise ValueError("sql_query contains a forbidden write or database command")

        try:
            with sqlite3.connect(DB_FILE) as connection:
                connection.execute(f"EXPLAIN {query}")
        except sqlite3.Error as error:
            print(f"field_validator: sql_query: SQL query failed to compile. Error: {error}")
            raise ValueError(f"sql_query is not valid for the database: {error}") from error

        return query


class DetectiveResponse(BaseModel):
    """Structured response returned by the detective."""

    answer: str = Field(description="Concise conclusion based only on the context.")
    next_step: str = Field(description="The next logical investigation step.")
    thinking: str = Field(description="Brief reasoning behind the conclusion.")
    rules_followed: str = Field(description="Rules followed while generating the response.")


class Model:
    """Base class for all models."""

    response_model: ClassVar[type[BaseModel]]

    def __init__(self, user_input, context=None):
        self.user_input = user_input
        self.context = context
        self.full_response = self.get_model_response()
        self.sql_query = self.get_field("sql_query")
        self.answer = self.get_field("answer")
        self.next_step = self.get_field("next_step")
        self.thinking = self.get_field("thinking")
        self.rules = self.get_field("rules_followed")

    def get_model_response(self):
        """Ask Ollama for a response validated by the model's Pydantic schema."""
        try:
            client = instructor.from_openai(
                OpenAI(base_url=OLLAMA_BASE_URL, api_key="ollama"),
                mode=instructor.Mode.JSON,
            )
        except Exception as error:
            return f"Model Connection error. Make sure Ollama is running and {MODEL} is installed.\n{error}"

        retry_feedback = None

        for attempt in range(2):
            messages: list[ChatCompletionMessageParam] = [
                {"role": "system", "content": self.prompt()},
                {"role": "user", "content": self.user_input},
            ]
            if retry_feedback:
                messages.append(
                    {
                        "role": "system",
                        "content": (
                            "The previous response failed validation. Correct only the reported problem "
                            f"and return the complete response again. Validation error: {retry_feedback}"
                        ),
                    }
                )

            try:
                return client.chat.completions.create(
                    model=MODEL,
                    response_model=self.response_model,
                    messages=messages,
                    max_retries=0,
                    extra_body={"options": {"num_ctx": OLLAMA_CONTEXT_WINDOW}},
                    temperature=0,
                    max_tokens=1024,
                )
            except Exception as error:
                retry_feedback = str(error)

        return f"Model Connection error. Make sure Ollama is running and {MODEL} is installed.\n{retry_feedback}"

    def get_field(self, field=None):
        """Get a field from the validated response model."""
        if field is not None and isinstance(self.full_response, BaseModel):
            return getattr(self.full_response, field, None)
        return None

    def get_thinking_process(self):
        """Get the model's brief reasoning."""
        return self.get_field("thinking")


class Translator(Model):
    """SQL Translator model class."""

    response_model = TranslatorResponse

    def model_input(self):
        return {"input": self.user_input, "question": self.user_input}

    def prompt(self) -> str:
        """Build the SQL translation prompt."""
        return f"""
        **ROLE:** You are a SQL Translator. Your task is to translate the following question into a valid SQL query. Use SQLite dialect.

                **Table selection priority:**
                - Questions about a crime, murder, police report, case file, crime date, or crime city MUST use only the `crime_scene_report` table unless the user explicitly asks for a different table.
                - Never use `person`, `income`, or a person relationship for that question. `crime_scene_report` has no `person_id` column and is not joined to those tables.

        **Rules:**
        1. Ensure the output contains a valid SQL query.
        2. The query must strictly follow the provided database schema and use only the available tables and columns.
        3. First identify the table whose row meaning matches the question; do not guess a table from a similar-sounding column.
        4. Avoid unnecessary complexity—only join tables or include conditions that are directly relevant to the user's question.
        5. Fetch all columns by default using 'SELECT *', unless a specific column is mentioned in the input.
        6. Use only the join_hints in the schema. Never invent a join between unrelated ID columns.
        7. Use person.id to connect a person to interviews, events, and gym memberships. Use person.license_id = drivers_license.id for licenses.
        8. Use person.ssn = income.ssn for income. This is a logical match, not person.id = income.ssn.
        9. Be flexible in interpreting incomplete input, but do not assume facts or columns not present in the schema.
        10. If the user asks for first, last, largest, or smallest, use ORDER BY with LIMIT or MAX/MIN.
        11. All dates are INTEGER values in YYYYMMDD format, without quotes. Convert dates written as YYYY.MM.DD or YYYY-MM-DD to YYYYMMDD.
        12. Gym check-in and check-out times are INTEGER minutes after midnight, not HHMM. Compare them numerically.
        13. Search free text with LIKE and percent wildcards, for example transcript LIKE '%keyword%'.
        14. When the user asks about a crime, murder, police report, or case file, use crime_scene_report. Its columns are date, crime_type, description, and city; use crime_type = 'murder' for murder reports.
        15. When a date is provided, put the converted integer directly in SQL, for example date = 20180203, never date = '2018-02-03'.
        16. Use only facts explicitly stated by the user as WHERE conditions. Do not add inferred or default filters, even if they seem likely.
        17. A request to show a report or information does not filter the description. Never add description = NULL, description = 'NULL', or an exact description condition unless the user explicitly supplied that description as a filter.
        18. NULL means a missing database value, not text to search for. Never invent NULL conditions.
        19. Return one query that helps answer the user's current question; do not invent a multi-step solution to the game.
        20. Return exactly one JSON object matching the response schema. Put the complete SQLite query in the 'sql_query' field. Do not return markdown, explanations, comments, or additional fields.

        **Database schema:**
        {get_db_schema()}
"""
        # {CustomDBSchema.get_table_info()}


class Detective(Model):
    """Detective model for analyzing case data and providing conclusions."""

    response_model = DetectiveResponse

    def model_input(self):
        return {"user_input": self.user_input, "context": self.context}

    def prompt(self) -> str:
        """Build the detective analysis prompt."""
        return f"""
ROLE: You are a detective solving a case. Analyze the context in relation to the user's question.

Rules:
1. Base the answer only on the provided context.
2. Suggest the next logical investigation step.
3. Keep the reasoning brief and fact-based.
4. Use exact column names from the query results.
5. Treat dates as integers in YYYYMMDD format.
6. If no relevant data is found, answer exactly: No relevant data available.

User question:
{self.user_input}

Context:
{self.context}
"""
