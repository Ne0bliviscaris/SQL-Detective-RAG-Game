import json

from langchain.chains.sql_database.query import create_sql_query_chain
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_ollama import ChatOllama

from modules.database.custom_db_schema import CustomDBSchema
from modules.settings import MODEL
from modules.tools import model_answer_regex


class Model:
    """Base class for all models."""

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
        """Get response using instance attributes."""
        try:
            langchain = self.build_langchain()
            response_str = langchain.invoke(self.model_input())
            try:
                parsed_response = json.loads(response_str)
                return parsed_response
            except:
                return response_str
        except Exception as e:
            return f"Model Connection error. Make sure Ollama is running and {MODEL} is installed.\n{e}"

    def get_field(self, field=None):
        """Get SQL query from parsed_response."""
        if isinstance(self.full_response, dict):
            requested_field = self.full_response.get(field)
            return requested_field.replace("\\'", "'") if requested_field else None

        if isinstance(self.full_response, str):
            return model_answer_regex(self.full_response, field)
        return None

    def get_thinking_process(self):
        """Get thinking process from parsed_response."""
        return self.response_json.get("thinking")


class Translator(Model):
    """SQL Translator model class."""

    def model_input(self):
        return {
            "input": self.user_input,
            "question": self.user_input,
        }

    def prompt(self) -> str:
        """Prompt template to translate text instructions into SQL query"""
        translator = """
        **ROLE:** You are a SQL Translator. Your task is to translate the following question into a valid SQL query. Use {dialect} dialect.

        **Database Schema:**
        {table_info}

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

        
        **Input:** 
        {input}

        **Examples:**
        "user_input": "find all theft cases from SQL City"
        "sql_query": "SELECT * FROM crime_scene_report WHERE type = 'theft' AND city = 'SQL City';"
        "thinking": "Identified 'theft' as the type of crime and 'SQL City' as the location."
        "rules_followed": "1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11"
        
        "user_input": "Find who lives in the first house in Northwestern Dr"
        "sql_query": "SELECT * FROM person WHERE address_street_name = 'Northwestern Dr' ORDER BY address_number ASC LIMIT 1;"
        "thinking": "Identified 'Northwestern Dr' as the street and used ORDER BY address_number ASC LIMIT 1; to get only house with the highest number."
        "rules_followed": "1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11"

        "user_input": "find all drivers with blue eyes"
        "sql_query": "SELECT * FROM drivers_license WHERE eye_color = 'blue';"
        "thinking": "Identified 'blue' as the eye color found in drivers_license table."
        "rules_followed": "1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11"

        "user_input": "Find a person named John living in Northwestern Dr"
        "sql_query": "SELECT * FROM person WHERE name LIKE '%John%' AND address_street_name = 'Northwestern Dr';"
        "thinking": address_street_name identified as 'Northwestern Dr'. Name is not exact, so used LIKE operator."
        "rules_followed": "1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11"
        
        **Output:**
        ```json
        {{
            "user_input": "{input}",
            "sql_query": "SELECT * FROM table_name WHERE condition;"
            "thinking": "Thinking process.",
            "rules_followed": "Rules followed while generating answer."
        }}
        top_k: {top_k}
        ```
        """
        return PromptTemplate(
            template=translator,
            input_variables=["input"],
            partial_variables={
                "dialect": "sqlite",
                "table_info": CustomDBSchema.get_table_info(),
            },
        )

    def build_langchain(self):
        """Builds and returns a language chain with database and Ollama connections."""
        db = CustomDBSchema()
        llm = ChatOllama(
            temperature=0,
            seed=1,
            model=MODEL,
            num_predict=512,  # Output tokens limit
            top_p=0.95,
            format="json",
            mirostat=2,
            mirostat_eta=2,
            mirostat_tau=1,
            tfs_z=50,  # reduce the impact of less probable tokens
            repeat_penalty=1.5,
            top_k=2,
        )
        prompt = self.prompt()
        return create_sql_query_chain(llm, db, prompt)


class Detective(Model):
    """Detective model for analyzing case data and providing conclusions."""

    def model_input(self):
        return {
            "user_input": self.user_input,
            "context": self.context,
        }

    def prompt(self) -> str:
        """Prompt template to translate text instructions into SQL query"""
        detective = """
        **ROLE:** You are a detective solving a case. Analyze the provided information in reference to the user's question. Your response must be concise, fact-based, and logically structured.

        **Rules:**
        1. Provide an "answer" based only on the given context.
        2. Suggest a "next_step" that logically follows from the answer.
        3. Keep "thinking" brief but clear, explaining how the answer was derived.
        4. Use only the received data—do not assume or use external knowledge.
        5. Use exact column names from the query results in responses.
        6. For **last, highest, or largest values**, return the maximum in the relevant column.
        7. For **first, lowest, or smallest values**, return the minimum in the relevant column.
        8. For **specific persons, objects, or events**, find an exact match in the data.
        9. For **patterns, summaries, or trends**, analyze and summarize the provided data.
        10. Dates are stored in the database as integers in the format YYYYMMDD. Make sure you read them properly.
        11. If query results contain relevant data, extract and summarize key information.
        12. If multiple records match, summarize them concisely.
        13. If no relevant data is found, return `"answer": "No relevant data available."`
        14. If the user input is ambiguous, provide a response based on the most likely interpretation.
        15. Ensure the answer is correct—scan the received context carefully.

        **User_input:** {{user_input}}

        **Context:** {{context}}

        **Output:**
        ```json
        {{
            "answer": "Your conclusion here.",
            "next_step": "Logical next step based on the answer.",
            "thinking": "Reasoning behind the answer and next step.",
            "user_input": "{user_input}",
            "rules_followed": "[List rules followed while generating answer.]"
        }}
        ```
        """
        return PromptTemplate(
            template=detective,
            input_variables=["user_input", "context"],
            partial_variables={
                "top_k": 1,
            },
        )

    def build_langchain(self):
        """Builds and returns a language chain with database and Ollama connections."""
        llm = ChatOllama(
            temperature=0,
            seed=1,
            model=MODEL,
            num_predict=1024,  # Output tokens limit
            top_p=0.95,
            format="json",
            mirostat=2,
            mirostat_eta=2,
            mirostat_tau=1,
            tfs_z=50,  # reduce the impact of less probable tokens
            repeat_penalty=1.5,
        )
        prompt = self.prompt()

        return (
            {"user_input": RunnablePassthrough(), "context": lambda x: self.context} | prompt | llm | StrOutputParser()
        )
