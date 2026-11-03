# SQL Detective - A Murder Mystery RAG Game

SQL Detective is an interactive investigation game where you solve a murder mystery by querying a police database using natural language. This application showcases the power of Retrieval-Augmented Generation (RAG) techniques with local small language models and database integration.

## 🔎 Overview

As a detective in SQL City, you're tasked with solving a murder that occurred on January 15, 2018. The uniqueness of this application lies in its approach:

1. **Natural Language to SQL Translation**: Ask questions in plain English
2. **Database Query Execution**: Retrieve specific information from the police database
3. **Context-Aware Analysis**: Get intelligent insights based on the query results
4. **Progressive Investigation**: Follow leads from clue to clue to solve the case

## 🚀 Features

- **Conversational Interface**: Interact with the investigation through a chat interface
- **Automatic SQL Translation**: No SQL knowledge required - just ask questions naturally
- **Intelligent Analysis**: The detective AI analyzes query results and suggests next steps
- **Investigation Notes**: Keep track of your findings in the detective's notebook
- **Local Processing**: All processing happens locally with no data sent to external APIs

## 🛠️ Technical Stack

- **Backend Framework**: `Python`
- **Frontend**: `Streamlit`
- **Database**: `SQLite`
- **LLM Platform**: `Ollama`
- **Language Model Used**: `DeepSeek-R1:1.5b`
- **Structured output**: `Instructor` with Pydantic response models

## 📂 Project Structure
```
Ollama-SQLite-RAG/ 
│ 
├── main.py              # Application entry point 
├── modules/ 
│ ├── chatbot.py             # Main conversation handler
│ ├── model.py               # Base classes for language model interactions 
│ ├── settings.py            # Configuration settings 
│ ├── tools.py               # Utility functions 
│ └── database/ 
│   ├── db.py                    # Database connection and query handling 
│   └── sql-murder-mystery.db    # SQLite database file 
│ 
├── detective_test.py    # Test script for detective model 
└── translator_test.py   # Test script for translator model
```
## 🧠 How It Works

1. **User Input**: The user submits a natural language question about the case
2. **Translation**: The Translator model converts the question to a valid SQL query
3. **Database Query**: The system executes the SQL query against the police database
4. **Analysis**: The Detective model analyzes the query results in the context of the question
5. **Response**: The system presents findings and suggests next investigative steps

## 📖 RAG Architecture

This application implements a complete RAG pipeline:

1. **Retrieval**: SQL queries retrieve relevant information from the database
2. **Augmentation**: The retrieved data augments the context for the language model
3. **Generation**: The language model generates insights based on the augmented context

## 🚦 Getting Started

### Prerequisites
- Python 3.8+
- [Ollama](https://ollama.ai/) installed locally
- `DeepSeek-R1:1.5b` model downloaded to Ollama

### Installation

```bash
# Clone the repository
git clone https://github.com/Ne0bliviscaris/Ollama-SQLite-RAG.git
cd Ollama-SQLite-RAG

# Create a virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start Ollama in the background and install the model
ollama run deepseek-r1:1.5b
# Run the application
python main.py
```

## 🙏 Acknowledgements

- [SQL Murder Mystery](https://github.com/NUKnightLab/sql-mysteries) for the original game concept
- [Instructor](https://python.useinstructor.com/) for validated structured output
- [Ollama](https://ollama.ai/) for local language model support
- [DeepSeek](https://www.deepseek.com) for their R1:1.5b model
- [Streamlit](https://streamlit.io/) for the interactive web interface
