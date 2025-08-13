# UW Procurement RAG Agent - Backend

This directory contains the backend for the UW Procurement RAG Agent, a FastAPI application that provides a conversational interface for querying procurement policies.

## Architecture

The backend is built with FastAPI and leverages LangChain and Azure AI services to power a Retrieval-Augmented Generation (RAG) agent.

- **API Server**: FastAPI with Uvicorn
- **RAG Core**: LangChain and LangGraph for conversational flow and state management.
- **LLM & Embeddings**: Azure OpenAI
- **Vector Store**: Azure AI Search
- **Streaming**: Server-Sent Events (SSE) for real-time responses.

## Getting Started

### Prerequisites

- Python 3.10+
- An Azure account with access to Azure OpenAI and Azure AI Search.

### Setup

1.  **Clone the repository**

2.  **Navigate to the backend directory:**
    ```bash
    cd backend
    ```

3.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate
    ```

4.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

5.  **Configure environment variables:**

    Create a `.env` file by copying the `env.example` file:
    ```bash
    cp env.example .env
    ```

    Update the `.env` file with your Azure credentials:

    ```
    # Azure AI Search Configuration
    AZURE_SEARCH_SERVICE_ENDPOINT="your-search-service-endpoint"
    AZURE_SEARCH_INDEX_NAME="your-search-index-name"
    AZURE_SEARCH_API_KEY="your-search-api-key"

    # Azure OpenAI Configuration
    AZURE_OPENAI_ENDPOINT="your-openai-endpoint"
    AZURE_OPENAI_API_KEY="your-openai-api-key"
    AZURE_OPENAI_API_VERSION="2024-02-01"
    AZURE_OPENAI_DEPLOYMENT_NAME="your-openai-deployment-name"
    ```

### Running the Server

To start the FastAPI server, run the following command from the `backend` directory:

```bash
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`.

This directory contains the source code for the FastAPI backend that powers the UW Procurement Assistant. It handles all the core logic, including the RAG agent, knowledge base integration, and API endpoints.

## Architecture

The backend is built using FastAPI and follows a modular, service-oriented architecture. Key components include:

- **`main.py`**: The entry point for the FastAPI application.
- **`app/`**: The main application module.
  - **`agents/`**: Contains the logic for the different AI agents (e.g., RAG agent).
  - **`routers/`**: Defines the API endpoints for the application.
  - **`services/`**: Includes services for interacting with external systems like Azure AI Search and for processing data.
  - **`config.py`**: Manages application configuration and environment variables.

## Getting Started

Follow these steps to set up and run the backend service on your local machine.

### 1. Prerequisites

- Python 3.9 or higher

### 2. Create a Virtual Environment

To avoid conflicts with other Python projects and system-wide packages, it is **highly recommended** to use a Python virtual environment (`venv`).

From the `backend` directory, run the following commands:

```bash
# Create a virtual environment
python3 -m venv venv

# Activate the virtual environment
# On macOS and Linux:
source venv/bin/activate

# On Windows:
.\venv\Scripts\activate
```

### 3. Install Dependencies

With your virtual environment activated, install the required Python packages using the `requirements.txt` file:

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

The application requires certain environment variables to be set, such as API keys and connection strings. An example configuration file is provided.

1.  Make a copy of the example file:

    ```bash
    cp env.example .env
    ```

2.  Open the `.env` file and fill in the required values for your Azure services (OpenAI, AI Search, etc.).

### 5. Run the Server

Once everything is set up, you can start the FastAPI server using `uvicorn`:

```bash
uvicorn main:app --reload
```

This command will start the server, and it will automatically reload whenever you make changes to the code. The API will be available at `http://127.0.0.1:8000`.

## API Endpoints

The application exposes several API endpoints for interacting with the agent. You can view the full, interactive API documentation (provided by Swagger UI) by navigating to `http://127.0.0.1:8000/docs` in your browser.

Key endpoints include:

- **`POST /agents/query/stream`**: The primary endpoint for sending a query to the RAG agent and receiving a real-time, streamed response.
- **`GET /health`**: A health check endpoint to verify that the service is running correctly.

## Code Style and Linting

This project uses `black` for code formatting and `ruff` for linting to ensure a consistent and high-quality codebase. It is recommended to use these tools before committing any changes.

A modular FastAPI backend with multi-agent architecture for procurement assistance, featuring RAG (Retrieval-Augmented Generation) capabilities and Microsoft Teams integration.

## 🏗️ Architecture Overview

This backend implements a **supervisor-multiagent architecture** with the following key components:

### 🤖 Agent System
- **Supervisor Agent**: Orchestrates workflows and routes tasks to appropriate agents
- **RAG Agent**: Handles document retrieval and question answering using LangChain/LangGraph
- **Base Agent**: Abstract base class providing common functionality for all agents

### 📁 Project Structure

```
backend/
├── app/
│   ├── agents/                 # Multi-agent system
│   │   ├── __init__.py
│   │   ├── base_agent.py      # Abstract base agent class
│   │   ├── rag_agent.py       # RAG agent with LangGraph workflow
│   │   └── supervisor_agent.py # Supervisor for agent orchestration
│   ├── services/              # Business logic services
│   │   ├── __init__.py
│   │   ├── azure_search_service.py  # Azure Search integration
│   │   └── memory_service.py        # Conversation memory management
│   ├── routers/               # API endpoints
│   │   ├── __init__.py
│   │   └── agents.py          # Agent interaction endpoints
│   └── config.py              # Configuration management
├── main.py                    # FastAPI application entry point
├── requirements.txt           # Python dependencies
├── env.example               # Environment variables template
└── README.md                 # This file
```

## 🚀 Features

### Core Capabilities
- **Multi-Agent RAG System**: Advanced document retrieval and question answering
- **Supervisor Orchestration**: Intelligent task routing and workflow management
- **Azure Integration**: Azure OpenAI, Azure Search, and Azure Cognitive Services
- **Microsoft Teams Ready**: Built-in endpoints for Teams bot integration
- **Conversation Memory**: Persistent conversation history across sessions
- **Adaptive Search**: Hybrid vector + keyword search with semantic capabilities

### API Endpoints

#### Agent Interaction
- `POST /agents/query` - Process queries through the multi-agent system
- `POST /agents/workflow` - Execute multi-step workflows
- `GET /agents/status` - Get system and agent status
- `GET /agents/capabilities` - List all system capabilities

#### Microsoft Teams Integration
- `POST /agents/teams/message` - Handle Teams messages
- `POST /agents/teams/adaptive-card` - Generate Adaptive Cards for Teams
- `GET /agents/health` - Health check for monitoring

#### Conversation Management
- `DELETE /agents/conversations/{id}` - Clear conversation history
- `GET /agents/conversations` - List active conversations

## 🛠️ Setup Instructions

### 1. Environment Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

```bash
# Copy environment template
cp env.example .env

# Edit .env with your Azure credentials
nano .env
```

Required environment variables:
- `AZURE_OPENAI_CHAT_KEY` - Azure OpenAI API key for chat
- `AZURE_OPENAI_CHAT_ENDPOINT` - Azure OpenAI endpoint URL
- `AZURE_OPENAI_CHAT_DEPLOYMENT` - Deployment name (e.g., "gpt-4")
- `AZURE_OPENAI_EMBEDDING_KEY` - Azure OpenAI API key for embeddings
- `AZURE_OPENAI_EMBEDDING_ENDPOINT` - Azure OpenAI embedding endpoint
- `AZURE_OPENAI_EMBEDDING_DEPLOYMENT` - Embedding deployment name
- `AZURE_SEARCH_KEY` - Azure Cognitive Search API key
- `AZURE_SEARCH_SERVICE` - Azure Search service name
- `AZURE_SEARCH_INDEX` - Azure Search index name

### 3. Run the Application

```bash
# Development mode (with auto-reload)
python main.py

# Or using uvicorn directly
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at:
- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔧 Usage Examples

### Basic Query
```bash
curl -X POST "http://localhost:8000/agents/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the procurement policies for software purchases?",
    "conversation_id": "user123",
    "task_type": "document_query"
  }'
```

### Teams Integration
```bash
curl -X POST "http://localhost:8000/agents/teams/adaptive-card" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How do I request a new vendor?",
    "conversation_id": "teams_user456"
  }'
```

### Multi-Step Workflow
```bash
curl -X POST "http://localhost:8000/agents/workflow" \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_definition": {
      "workflow_id": "procurement_analysis",
      "name": "Comprehensive Procurement Analysis",
      "description": "Multi-step procurement guidance workflow",
      "steps": [
        {
          "step_id": "policy_lookup",
          "agent_id": "rag_agent",
          "task_type": "policy_lookup",
          "input_data": {"question": "procurement policies"},
          "depends_on": []
        }
      ]
    }
  }'
```

## 🧠 Agent System Details

### RAG Agent Workflow
The RAG agent uses LangGraph to orchestrate a sophisticated retrieval pipeline:

1. **Query Rewriting**: Optimizes user questions for better retrieval
2. **Document Retrieval**: Adaptive hybrid search (vector + keyword + semantic)
3. **Document Grading**: Filters relevant documents
4. **Document Reranking**: Orders documents by relevance
5. **Answer Generation**: Creates grounded responses with citations
6. **Memory Update**: Stores conversation history

### Supervisor Agent
The supervisor manages task routing and workflow orchestration:
- Routes single tasks to appropriate agents
- Executes multi-step workflows with dependency management
- Handles parallel task execution
- Provides system-wide monitoring and status

## 🔗 Microsoft Teams Integration

### Adaptive Cards
The system generates rich Adaptive Cards for Teams with:
- Formatted answers with citations
- Source document references
- Processing metadata
- Error handling with user-friendly messages

### Bot Framework Integration
Ready for integration with Microsoft Bot Framework:
- Teams-specific endpoints
- Conversation state management
- Rich card responses
- Error handling and fallbacks

## 📊 Monitoring and Debugging

### Health Checks
- `GET /health` - Basic API health
- `GET /agents/health` - Agent system health
- `GET /agents/status` - Detailed agent status

### Logging
The system provides comprehensive logging for:
- Agent workflow execution
- Search operations
- Error tracking
- Performance monitoring

## 🔒 Security Considerations

- Environment variables for sensitive configuration
- API key validation
- CORS configuration for Teams integration
- Input validation and sanitization
- Error handling without information leakage

## 🚀 Deployment

### Production Deployment
```bash
# Set production environment
export DEBUG=False

# Run with production WSGI server
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
```

### Docker Deployment
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 📈 Extending the System

### Adding New Agents
1. Create agent class inheriting from `BaseAgent`
2. Implement `process()` and `get_capabilities()` methods
3. Register agent in `SupervisorAgent._register_agents()`
4. Add routing logic in supervisor

### Custom Workflows
Define multi-step workflows with:
- Step dependencies
- Parallel execution
- Error handling
- Result aggregation

## 🤝 Contributing

1. Follow the modular architecture patterns
2. Add comprehensive type hints
3. Include error handling and logging
4. Update tests and documentation
5. Ensure Teams integration compatibility

## 📝 Migration Notes

This backend was migrated from Jupyter notebook code with the following improvements:
- Modular architecture with separation of concerns
- Async/await support for better performance
- Comprehensive error handling
- Teams integration capabilities
- Multi-agent orchestration
- Persistent conversation memory
- Production-ready configuration management
