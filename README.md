# Model Context Protocol (MCP)

A Flask application that integrates with PostgreSQL and a Large Language Model (LLM) to provide database context for reasoning.

## Features

- **Dynamic Database Schema**: Uses SQLAlchemy's reflection capabilities to adapt to database changes without code modifications.
- **RESTful API**: CRUD operations for all tables in the connected PostgreSQL database.
- **Server-Sent Events (SSE)**: Stream LLM responses with database context.
- **LLM Integration**: Connects to an LLM API (e.g., OpenAI, Grok) to provide intelligent responses about the database.

## Project Structure

```
mcp-postgresql/
├── app/                  # Core application package
│   ├── __init__.py       # Initializes Flask, DB, and routes
│   ├── config.py         # Configuration (DB URI, LLM keys)
│   ├── models/           # Dynamic model handling
│   │   ├── __init__.py   
│   │   └── dynamic.py    # Reflects DB schema dynamically
│   ├── routes/           # API endpoints
│   │   ├── __init__.py   
│   │   ├── api.py        # RESTful CRUD endpoints
│   │   └── sse.py        # SSE endpoint for LLM streaming
│   ├── llm/              # LLM integration
│   │   ├── __init__.py   
│   │   └── llm_client.py # LLM API client
│   └── utils/            # Helper functions
│       ├── __init__.py   
│       └── db_utils.py   # Extracts DB context for LLM
├── migrations/           # DB migration files (auto-generated)
├── tests/                # Unit tests
│   ├── __init__.py      
│   └── test_sse.py       # Tests for SSE and LLM
├── .env                  # Environment variables (DB, LLM keys)
├── .gitignore            # Ignores pycache, env, etc.
├── docker-compose.yml    # Docker composition
├── Dockerfile            # Docker container definition
├── requirements.txt      # Lists dependencies
├── run.py                # App entry point
└── README.md             # Project docs
```

## Getting Started

### Prerequisites

- Docker and Docker Compose
- PostgreSQL database

### Environment Setup

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/mcp-postgresql.git
   cd mcp-postgresql
   ```

2. Configure environment variables in `.env` file:
   ```
   # Required environment variables
   DATABASE_URL=postgresql://username:password@host:port/dbname
   LLM_API_KEY=your-llm-api-key
   LLM_API_URL=https://api.openai.com/v1/chat/completions
   LLM_MODEL=gpt-3.5-turbo
   ```

### Running with Docker

1. Build and start the containers:
   ```
   docker-compose up --build
   ```

2. The application will be available at http://localhost:5000

### Running Locally (without Docker)

1. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run the application:
   ```
   python run.py
   ```

## API Endpoints

### RESTful API

- `GET /api/tables` - List all tables
- `GET /api/tables/<table_name>` - Get table details
- `GET /api/tables/<table_name>/rows` - Get rows from a table
- `POST /api/tables/<table_name>/rows` - Add a new row
- `PUT /api/tables/<table_name>/rows/<row_id>` - Update a row
- `DELETE /api/tables/<table_name>/rows/<row_id>` - Delete a row
- `POST /api/execute` - Execute custom SQL (requires authorization)

### SSE Endpoint

- `POST /sse/llm` - Stream LLM responses with database context

## Testing

Run tests with:
```
python -m unittest discover
```

## License

This project is licensed under the MIT License - see the LICENSE file for details. 