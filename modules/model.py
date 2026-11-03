from typing import ClassVar

import instructor
from openai import OpenAI
from pydantic import BaseModel, Field

from modules.database.custom_db_schema import CustomDBSchema
from modules.settings import MODEL, OLLAMA_BASE_URL, OLLAMA_CONTEXT_WINDOW


class TranslatorResponse(BaseModel):
    """Structured response returned by the SQL translator."""

    sql_query: str = Field(description="A valid SQLite query matching the user's request.")
    # thinking: str = Field(description="Brief reasoning behind the SQL query.")
    # rules_followed: str = Field(description="Comma-separated rule numbers followed.")


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
            return client.chat.completions.create(
                model=MODEL,
                response_model=self.response_model,
                messages=[
                    {"role": "system", "content": self.prompt()},
                    {"role": "user", "content": self.user_input},
                ],
                extra_body={"options": {"num_ctx": OLLAMA_CONTEXT_WINDOW}},
                temperature=0,
                max_tokens=2048,
            )
        except Exception as error:
            return f"Model Connection error. Make sure Ollama is running and {MODEL} is installed.\n{error}"

    def get_field(self, field=None):
        """Get a field from the validated response model."""
        if isinstance(self.full_response, BaseModel):
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
        14. When the user asks about a crime, murder, police report, or case file, use crime_scene_report. This table has only date, type, description, and city; never use person_id with it.
        15. When a date is provided, put the converted integer directly in SQL, for example date = 20180203, never date = '2018-02-03'.
        16. Use the facts stated by the user as filters. Do not add a default crime, date, city, suspect, or solution that the user did not ask for.
        17. Return one query that helps answer the user's current question; do not invent a multi-step solution to the game.
        18. ONLY return the SQL query, no explanations or markdown.

        **Database schema:**
        {CustomDBSchema.get_table_info()}
"""


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
