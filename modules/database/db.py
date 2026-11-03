import sqlite3

from langchain_community.utilities import SQLDatabase

from modules.settings import DB_FILE


def execute_sql_query(extracted_query):
    """Connect to database and execute SQL query"""
    with sqlite3.connect(DB_FILE) as db_connection:
        cursor = db_connection.cursor()
        cursor.execute(extracted_query)
        results = cursor.fetchall()

        column_names = [description[0] for description in cursor.description]

        return convert_results_to_dict(results, column_names)


def convert_results_to_dict(records, column_names):
    """Convert list of tuples to a list of dictionaries."""
    return [dict(zip(column_names, row)) for row in records]


def database_connect():
    """Establishes a connection to the SQL database using the provided URI."""
    db = SQLDatabase.from_uri(f"sqlite:///{DB_FILE}")
    return db


def db_without_solution():
    """Connects to SQL database. Solution table is excluded."""
    return SQLDatabase.from_uri(f"sqlite:///{DB_FILE}", ignore_tables=["solution"])
