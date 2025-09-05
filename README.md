# Transcript Analysis API

A FastAPI service that analyzes plain-text transcripts using OpenAI and returns summaries with next actions.

## Features

- **GET /api/v1/analyze** - Analyze single transcript
- **GET /api/v1/analyses/{id}** - Retrieve stored analysis by ID
- **POST /api/v1/analyses/batch** - Analyze multiple transcripts concurrently

## Quick Start

### Requirements

- Python 3.12+
- OpenAI API key

### Installation

```bash
# Clone and install
cd ml-tech-assessment
pip install -r requirements.txt

# Or using Poetry
poetry install
poetry shell
```

### Configuration

Create a `.env` file:

```env
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-2024-08-06
```

### Run

```bash
# Development
uvicorn app.main:app --reload

# Or
python app/main.py
```

The API will be available at:
- **Application**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

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

## Testing

### Unit Tests

```bash
# Run all tests
pytest

# With coverage
pytest --cov=app tests/

# Specific tests
pytest tests/test_routes.py
pytest tests/test_use_cases.py
```

### API Testing with Postman

Import the provided Postman collection:

1. Open Postman
2. Click "Import" → "Upload Files"
3. Select `postman_collection.json`
4. The collection includes:
   - Health check
   - Single transcript analysis
   - Batch analysis
   - Get analysis by ID
   - Error handling tests

**Variables:**
- `base_url`: http://localhost:8000 (default)
- `sample_transcript`: Pre-filled sample transcript
- `analysis_id`: Set this after getting an analysis response

**Usage:**
1. Start the API: `uvicorn app.main:app --reload`
2. Run "Health Check" to verify API is running
3. Run "Analyze Single Transcript" and copy the returned ID
4. Set the `analysis_id` variable with the copied ID
5. Run "Get Analysis by ID" to retrieve the stored analysis
6. Test batch analysis and error scenarios

## Architecture

The project follows hexagonal (clean) architecture:

```
app/
├── api/           # FastAPI endpoints and schemas
├── domain/        # Business models and errors
├── use_cases/     # Application business logic
├── infra/         # Infrastructure (repository, DI)
├── adapters/      # External service adapters
└── ports/         # Interface definitions
```

## Error Handling

- **200**: Success
- **404**: Analysis not found
- **413**: Transcript too large (>100KB)
- **422**: Invalid input (empty transcript)
- **429**: Rate limit exceeded
- **502**: OpenAI service error
- **504**: Request timeout

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | Required |
| `OPENAI_MODEL` | OpenAI model to use | `gpt-4o-2024-08-06` |

## License

MIT License
