# Transcript Analysis API

A production-quality FastAPI service that analyzes plain-text transcripts using OpenAI and returns summaries with next actions. Built with hexagonal architecture (clean architecture) principles.

## Features

- **GET /api/v1/analyze** - Analyze single transcript
- **GET /api/v1/analyses/{id}** - Retrieve stored analysis by ID
- **POST /api/v1/analyses/batch** - Analyze multiple transcripts concurrently
- **Hexagonal Architecture** - Clean separation of concerns
- **Thread-safe Repository** - In-memory storage with async locks
- **Comprehensive Error Handling** - Proper HTTP status codes
- **OpenAPI Documentation** - Auto-generated Swagger UI
- **Async Support** - Non-blocking operations with concurrency limits

## Architecture

```
app/
├── api/                    # API Layer
│   ├── routes.py          # FastAPI endpoints
│   └── schemas.py         # Request/Response models
├── domain/                # Domain Layer
│   ├── models.py          # Domain entities
│   ├── errors.py          # Domain exceptions
│   └── ports.py           # Port interfaces
├── use_cases/             # Use Cases Layer
│   ├── analyze_transcript.py
│   ├── get_analysis.py
│   └── analyze_batch.py
├── infra/                 # Infrastructure Layer
│   ├── memory_repository.py
│   └── di.py              # Dependency injection
├── adapters/              # External Adapters
│   └── openai.py          # OpenAI integration
└── main.py               # FastAPI application
```

### Key Design Decisions

- **Port & Adapter Pattern**: OpenAI integration through ports interface
- **Anti-Corruption Layer**: Maps LLM DTOs to domain models
- **Thread Safety**: Async locks for concurrent repository access
- **Error Boundaries**: Domain errors mapped to appropriate HTTP status codes
- **Dependency Injection**: Centralized wiring with FastAPI dependencies

## Requirements

- Python 3.12+
- OpenAI API key
- Poetry (recommended) or pip

## Installation

### Using Poetry (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd ml-tech-assessment

# Install dependencies
poetry install

# Activate virtual environment
poetry shell
```

### Using pip

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Configuration

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-2024-08-06
```

## Running the Application

### Development Server

```bash
# Using Poetry
poetry run uvicorn app.main:app --reload

# Using Python directly
python -m uvicorn app.main:app --reload

# Using the main.py script
python app/main.py
```

The API will be available at:
- **Application**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

### Production

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## API Usage

### Analyze Single Transcript

```bash
curl -X GET "http://localhost:8000/api/v1/analyze?transcript=Your transcript text here"
```

**Response:**
```json
{
  "id": "8e5b7dfe-9c2c-4f76-8c35-4b8b97f9c0a3",
  "summary": "The meeting discussed onboarding tasks and deadlines.",
  "next_actions": ["Share kickoff deck", "Book follow-up meeting", "Create Jira tickets"],
  "created_at": "2025-09-04T16:21:33.501Z"
}
```

### Retrieve Analysis by ID

```bash
curl -X GET "http://localhost:8000/api/v1/analyses/8e5b7dfe-9c2c-4f76-8c35-4b8b97f9c0a3"
```

### Batch Analysis

```bash
curl -X POST "http://localhost:8000/api/v1/analyses/batch" \
  -H "Content-Type: application/json" \
  -d '{
    "transcripts": [
      "First transcript text...",
      "Second transcript text..."
    ]
  }'
```

**Response:**
```json
{
  "results": [
    {
      "transcript": "First transcript text...",
      "success": true,
      "analysis": {
        "id": "uuid1",
        "summary": "Summary 1",
        "next_actions": ["Action 1"],
        "created_at": "2025-09-04T16:21:33.501Z"
      },
      "error": null
    }
  ],
  "total_count": 2,
  "successful_count": 2
}
```

## Error Handling

The API returns appropriate HTTP status codes:

- **200**: Success
- **404**: Analysis not found
- **413**: Transcript too large (>100KB)
- **422**: Invalid input (empty transcript)
- **429**: Rate limit exceeded
- **502**: OpenAI service error
- **504**: Request timeout

## Testing

### Run All Tests

```bash
# Using Poetry
poetry run pytest

# Using pytest directly
pytest

# With coverage
pytest --cov=app tests/

# Verbose output
pytest -v
```

### Run Specific Tests

```bash
# Unit tests only
pytest tests/test_use_cases.py

# Integration tests only
pytest tests/test_routes.py

# Specific test
pytest tests/test_use_cases.py::TestAnalyzeTranscriptUseCase::test_successful_analysis
```

### Test Coverage

```bash
pytest --cov=app --cov-report=html tests/
# Open htmlcov/index.html in browser
```

## Development

### Project Structure

- **Domain Layer**: Business logic and entities
- **Use Cases**: Application-specific business rules
- **Infrastructure**: External concerns (database, APIs)
- **API**: Web interface and serialization

### Adding New Features

1. Define domain models in `app/domain/models.py`
2. Create use cases in `app/use_cases/`
3. Add API endpoints in `app/api/routes.py`
4. Update schemas in `app/api/schemas.py`
5. Wire dependencies in `app/infra/di.py`
6. Add tests in `tests/`

### Code Quality

```bash
# Format code
black app/ tests/

# Sort imports
isort app/ tests/

# Type checking
mypy app/

# Linting
flake8 app/ tests/
```

## Limitations

- **In-Memory Storage**: Data is lost when the application restarts
- **Single Process**: Memory is not shared across multiple workers
- **No Persistence**: Consider adding database integration for production
- **Rate Limiting**: Depends on OpenAI API limits
- **Concurrency**: Limited to 5 concurrent requests in batch processing

## Production Considerations

### Scaling

- Use a proper database (PostgreSQL, MongoDB)
- Implement Redis for caching
- Add rate limiting middleware
- Use multiple workers with shared storage
- Implement circuit breakers for external APIs

### Monitoring

- Add structured logging with correlation IDs
- Implement health checks for dependencies
- Add metrics collection (Prometheus)
- Set up alerting for error rates

### Security

- Add authentication and authorization
- Implement input validation and sanitization
- Use HTTPS in production
- Add request/response logging
- Implement API key management

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | Required |
| `OPENAI_MODEL` | OpenAI model to use | `gpt-4o-2024-08-06` |

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run the test suite
6. Submit a pull request

## License

This project is licensed under the MIT License.
