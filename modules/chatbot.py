import pandas as pd
import streamlit as st

from modules.database.db import execute_sql_query
from modules.model import Detective, Translator


def chatbot():
    """Main chatbot function."""
    game_rules_sidebar()
    initialize_chat_session()
    display_chat_input()
    with st.container():
        show_chat_history()
    rag_pipeline()


def initialize_chat_session():
    """Initialize chat session state variables."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "index" not in st.session_state:
        st.session_state.index = 0
    if "context" not in st.session_state:
        st.session_state.context = {
            "user_inputs": [],
            "sql_queries": [],
            "query_results": [],
            "detective_answers": [],
            "detective_thinking": [],
        }
    if "current_state" not in st.session_state:
        st.session_state.current_state = None


def display_chat_input():
    if prompt := st.chat_input("Ask about the case..."):
        fixed_prompt = prompt.replace('"', "'")
        index = st.session_state.index
        st.session_state.current_state = "translator"
        prefill_context()
        update_context("user_inputs", fixed_prompt, index)
        update_messages("user", fixed_prompt, index)
        st.session_state.index += 1
        st.rerun()


def prefill_context():
    """Prefill context with empty messages."""
    for key in st.session_state.context:
        st.session_state.context[key].append(None)


def show_chat_history():
    """Display chat history with synchronized context data."""
    for index, message_group in enumerate(st.session_state.messages):
        if not message_group:
            continue

        for message in message_group:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

                if message["role"] == "database":
                    show_query_results(index)
                if message["role"] == "assistant":
                    show_thinking_process(index)


def rag_pipeline():
    """Main RAG pipeline."""
    if st.session_state.current_state == "translator":
        translate_question()
    if st.session_state.current_state == "database":
        execute_query()
    if st.session_state.current_state == "detective":
        detective_conclusion()


def translate_question():
    """Translate the natural question to SQL query"""
    with st.spinner("Translating to SQL..."):
        current_index = st.session_state.index - 1

        user_input = st.session_state.context["user_inputs"][current_index]
        translation = Translator(user_input)

        update_context("sql_queries", translation.sql_query, current_index)
        update_messages("database", translation.sql_query, current_index)

        st.session_state.current_state = "database"
        st.rerun()


def execute_query():
    """Execute SQL query and return results."""
    with st.spinner("Executing SQL query..."):
        current_index = st.session_state.index - 1
        query = st.session_state.context["sql_queries"][current_index]
        try:
            query_results = execute_sql_query(query)
            update_context("query_results", query_results, current_index)
            st.session_state.current_state = "detective"
        except Exception as e:
            print(f"Error executing translated query.\nRephrase the question and try again.\nError message: {e}")
            st.session_state.current_state = None

        st.rerun()


def detective_conclusion():
    """Detective's conclusion."""
    with st.spinner("Detective is analyzing the results..."):
        current_index = st.session_state.index - 1

        user_input = st.session_state.context["user_inputs"][current_index]
        query_results = st.session_state.context["query_results"][current_index]

        detective = Detective(user_input=user_input, context=query_results)

        update_context("detective_answers", detective.answer, current_index)
        update_context("detective_thinking", detective.thinking, current_index)
        update_messages("assistant", detective.answer, current_index)

        st.session_state.current_state = None
        st.rerun()


def update_context(key, value, index):
    """ "Update context value at specific index."""
    context = st.session_state.context[key]
    while len(context) <= index:
        context.append(None)
    context[index] = value


def update_messages(role, content, index):
    messages = st.session_state.messages
    while len(messages) <= index:
        messages.append([])

    messages[index].append({"role": role, "content": content})


def show_query_results(index):
    """Display query results for given message index."""
    query_results = st.session_state.context["query_results"][index]

    # Validate index
    if not query_results:
        st.warning("No results found for this query.")
        return

    with st.expander("Query Results"):
        df = convert_results_to_dataframe(query_results)
        st.dataframe(df)


def convert_results_to_dataframe(results):
    """Convert query results to DataFrame."""
    return pd.DataFrame(results)


def show_thinking_process(index):
    """Display detective's thinking process in expandable section."""
    with st.expander("Detective's Thinking Process"):
        st.write(st.session_state.context["detective_thinking"][index])


def game_rules_sidebar():
    """Displays game rules, hints and tools in the sidebar."""
    with st.sidebar:
        st.title("Detective's Handbook")

        with st.expander("Case Brief", expanded=True):
            st.markdown(
                """
                **THE CASE**
                
                - Crime: Murder
                - Date: January 15, 2018
                - Location: SQL City
                - Status: Unsolved
                
                Begin by finding the crime scene report.
            """
            )

        with st.expander("Investigation Tips"):
            st.markdown(
                """
                - Ask specific questions about people, places, or evidence
                - Follow leads from one piece of evidence to another
                - Look for connections between witnesses and suspects
                - Pay attention to alibis and timelines
            """
            )

        # Save notes in session state for persistence
        if "notes" not in st.session_state:
            st.session_state.notes = ""

        st.session_state.notes = st.text_area(
            label="Detective's Notes",
            value=st.session_state.notes,
            height=300,
            placeholder="Record your clues, suspects and theories here...",
        )
