# Procurement Agent

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
