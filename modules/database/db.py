import sqlite3

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
    """Establish a direct SQLite connection."""
    return sqlite3.connect(DB_FILE)


def db_without_solution():
    """Establish a direct SQLite connection for the investigation database."""
    return sqlite3.connect(DB_FILE)
