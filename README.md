# UW Procurement RAG Agent

This project is a Retrieval-Augmented Generation (RAG) agent designed to answer questions about the University of Washington's procurement policies. It provides a conversational interface that allows users to get clear, accurate, and cited answers from a knowledge base of procurement documents.

## Components

- **Backend**: A FastAPI application that serves the RAG agent, handles conversational memory, and streams responses. See the [backend/README.md](backend/README.md) for detailed setup and usage instructions.
- **Frontend**: A Microsoft Teams application that provides the user interface for interacting with the agent (not included in this repository).

## Features

- **Conversational Q&A**: Ask questions in natural language and get helpful answers.
- **Sourced Answers**: Responses are based on and cite the source documents from the knowledge base.
- **Streaming Responses**: Get real-time feedback as the agent generates an answer.
- **Conversation History**: The agent remembers the context of the conversation to answer follow-up questions.

Welcome to the UW Procurement Assistant, an intelligent, conversational AI agent designed to streamline procurement processes at the University of Washington. This agent provides quick, accurate answers to procurement-related questions, leveraging a robust knowledge base and a sophisticated RAG (Retrieval-Augmented Generation) architecture.

Built with FastAPI for the backend and designed for integration with Microsoft Teams, this assistant offers a seamless and professional user experience.

## Key Features

- **Conversational AI:** Engage in natural, human-like conversations to get the information you need.
- **RAG Architecture:** Retrieves information directly from a secure knowledge base of UW procurement documents, ensuring answers are accurate, context-aware, and up-to-date.
- **Microsoft Teams Integration:** A user-friendly interface within Teams allows for easy access and interaction.
- **Real-time Streaming:** Responses are streamed in real-time, allowing you to see answers as they are generated.
- **Conversation Memory:** The agent remembers the context of your conversation for a more coherent and efficient experience.
- **Professional & Organized Responses:** Answers are well-structured, with clear citations and links to source documents.

## Project Structure

This repository is organized into two main components:

- **/frontend:** Contains the Microsoft Teams application source code. (Further details to be added as the frontend is developed).
- **/backend:** The core FastAPI application that powers the RAG agent, manages the knowledge base, and serves the API.

## Getting Started

To get the project up and running, you will need to set up the backend service and, optionally, the Teams frontend.

### Backend Setup

For detailed instructions on setting up the backend, please refer to the `backend/README.md` file.

### Frontend Setup

For detailed instructions on setting up the Microsoft Teams application, please refer to the `frontend/README.md` file.

## Technology Stack

- **Backend:** FastAPI, Python, LangChain, LangGraph, Azure AI Search
- **Frontend:** Microsoft Teams SDK, TypeScript, Adaptive Cards
- **Deployment:** Designed for Azure

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue for any bugs, feature requests, or improvements.


A FastAPI backend application for procurement agent functionality.

## Project Structure

```
procurement-agent/
├── backend/           # FastAPI backend application
│   ├── app/          # Application modules
│   ├── main.py       # FastAPI application entry point
│   ├── requirements.txt  # Python dependencies
│   ├── env.example   # Environment variables template
│   └── .gitignore    # Backend-specific gitignore
├── frontend/         # Frontend application (to be developed)
│   └── .gitignore    # Frontend-specific gitignore
├── .gitignore        # Root gitignore (includes notebooks and security files)
└── README.md         # This file
```

## Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Copy environment template and configure:
   ```bash
   cp env.example .env
   # Edit .env with your specific configuration
   ```

5. Run the development server:
   ```bash
   python main.py
   ```

The API will be available at `http://localhost:8000` with automatic documentation at `http://localhost:8000/docs`.

## Security Notes

- Jupyter notebooks (*.ipynb) are excluded from version control
- Environment files (.env*) are ignored
- API keys and sensitive configuration should be stored in .env files
- Never commit credentials or API keys to the repository

## Development

- The backend is set up with FastAPI and includes CORS middleware for frontend integration
- Configuration is managed through environment variables
- The project structure supports easy expansion with additional modules in the `app/` directory
