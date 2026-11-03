import os
import subprocess

import streamlit as st

from modules.chatbot import chatbot

st.set_page_config(
    page_title="Local SQL RAG",
    page_icon="🤖",
    menu_items={"About": "https://github.com/Ne0bliviscaris/Ollama-SQLite-RAG"},
)


def title_screen():
    st.title("SQL RAG - local Ollama - Instructor")
    st.markdown(
        """
        ### 🔍 Welcome, Detective
        
        A murder has been committed in SQL City, and you've been called to solve the case. 
        
        Your only lead is that the crime occurred on **January 15, 2018**, but the crime scene report has gone missing.
        Using your detective skills and SQL knowledge, you must:
        
        1. Query the police database to find relevant information
        2. Follow leads by asking the right questions
        3. Connect the dots to identify the killer
        
        Type your investigation queries in natural language, and the system will:
        - Translate your questions to SQL
        - Search the database
        - Help you analyze the results
        
        Can you solve the mystery before the trail goes cold?
        """
    )


def main():
    if not st.session_state:
        title_screen()
    chatbot()


if __name__ == "__main__":  # Poprawiono cudzysłowy
    # Launch streamlit and check if it's not already running
    if not os.environ.get("RUNNING_IN_STREAMLIT"):
        # Mark streamlit as running
        os.environ["RUNNING_IN_STREAMLIT"] = "1"
        file_path = os.path.abspath(__file__)
        # Run streamlit with correct command list
        subprocess.run(["streamlit", "run", file_path], check=True)
    else:
        main()
