from typing import ClassVar

import instructor
from openai import OpenAI
from pydantic import BaseModel, Field

from modules.database.custom_db_schema import CustomDBSchema
from modules.settings import MODEL, OLLAMA_BASE_URL


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
                temperature=0,
                max_tokens=1024,
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
        3. Keep the thinking process brief, ensuring it logically aligns with the user input.
        4. Avoid unnecessary complexity—only join tables or include conditions that are directly relevant to the user's question.
        5. Fetch all columns by default using 'SELECT *', unless a specific column is mentioned in the input.
        6. Be flexible in interpreting imprecise or incomplete user input while providing a valid SQL query.
        7. Do not use your own knowledge or external sources.
        8. Do not assume anything that is not explicitly present in the schema.
        9. ONLY return the SQL query, no additional explanations or text.
        10. If the user is asking about the order of items (first, last etc.), use an ORDER BY clause based on the relevant column.
        11. While using columns from multiple tables, ensure you call proper tables.
        12. All dates should be treated as integers in YYYYMMDD format. Example: December 09, 1993 should be represented as 19931209.
        13. If the user is asking about police cases or reports, use the 'crime_scene_report' table.


        **Examples:**
        user_input: "find all theft cases from SQL City that happened on June 7, 2018"
        "sql_query": "SELECT * FROM crime_scene_report WHERE type = 'theft' AND city = 'SQL City' AND date = 20180607;"


        
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
