# War Bot - Discord Timer Tracking System

A Discord bot integrated with a FastAPI backend for tracking war timers. The system allows users to record timer events through Discord commands, which are stored in a SQLite database via a REST API.

## Features

- **Discord Bot Integration**: Easy-to-use commands for recording timers
- **REST API Backend**: FastAPI-powered backend with full CRUD operations
- **Secure Authentication**: API key-based authentication
- **Input Validation**: Comprehensive validation for timer types and user data
- **Error Handling**: Robust error handling with retry logic and logging
- **Timezone Aware**: UTC-based timestamp handling
- **Database Management**: SQLite database with SQLAlchemy ORM

## Architecture

- **bot.py**: Discord bot that handles user commands
- **main.py**: FastAPI backend providing REST API endpoints
- **models.py**: Data models (SQLAlchemy and Pydantic)
- **database.py**: Database configuration
- **auth.py**: API authentication middleware
- **config.py**: Centralized configuration management

## Installation

### Prerequisites

- Python 3.8+
- Discord Bot Token
- API Key (for securing the backend)

### Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd Warbot
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**:
   ```bash
   cp .env.example .env
   ```

   Edit `.env` and add your credentials:
   ```
   DISCORD_TOKEN=your_discord_bot_token_here
   API_KEY=your_secure_api_key_here
   API_URL=http://127.0.0.1:8000
   ```

## Usage

### Starting the API Server

Run the FastAPI backend:

```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

The API will be available at `http://127.0.0.1:8000`

API documentation is auto-generated at:
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

### Starting the Discord Bot

In a separate terminal, run:

```bash
python bot.py
```

### Discord Commands

- `!im_hit HH:MM:SS` - Record a friendly hit timer
  - Example: `!im_hit 14:30:25`

## API Endpoints

All endpoints require an `X-API-Key` header with a valid API key.

### Timers

- **POST /timers/** - Create a new timer
  - Body: `{"user_name": "string", "timer_type": "friendly_hit", "time_shot": "2025-01-01T12:00:00Z"}`

- **GET /timers/** - List all timers
  - Query params: `skip` (default: 0), `limit` (default: 100, max: 500)

- **GET /timers/{timer_id}** - Get a specific timer

- **PUT /timers/{timer_id}** - Update a timer
  - Body: `{"user_name": "string", "timer_type": "enemy_hit", "time_shot": "2025-01-01T12:00:00Z"}`

- **DELETE /timers/{timer_id}** - Delete a timer

### Timer Types

- `friendly_hit` - Friendly fire event
- `enemy_hit` - Enemy attack event
- `defensive_hit` - Defensive action event

## Configuration

Configuration can be customized via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| DISCORD_TOKEN | - | Discord bot token (required) |
| API_KEY | - | API authentication key (required) |
| API_URL | http://127.0.0.1:8000 | API base URL |
| COMMAND_PREFIX | ! | Discord bot command prefix |
| MAX_API_RETRIES | 3 | Max API request retries |
| API_TIMEOUT | 10 | API request timeout (seconds) |
| MAX_QUERY_LIMIT | 500 | Maximum query result limit |
| LOG_LEVEL | INFO | Logging level |
| DATABASE_URL | sqlite:///./war_timer.db | Database connection URL |

## Development

### Project Structure

```
Warbot/
├── bot.py              # Discord bot
├── main.py             # FastAPI backend
├── models.py           # Data models
├── database.py         # Database configuration
├── auth.py             # Authentication
├── config.py           # Configuration management
├── requirements.txt    # Python dependencies
├── .env.example        # Environment template
├── README.md           # Documentation
└── war_timer.db        # SQLite database (auto-created)
```

### Code Quality

The codebase includes:
- Comprehensive docstrings
- Type hints
- Input validation
- Error handling with retry logic
- Structured logging
- Security best practices

## Security Considerations

- API endpoints are protected with API key authentication
- Input validation prevents injection attacks
- SQLAlchemy ORM protects against SQL injection
- Environment variables for sensitive data
- Secure error messages that don't leak implementation details

## Troubleshooting

### Bot won't start
- Check that DISCORD_TOKEN is set correctly in `.env`
- Verify the bot has proper permissions in your Discord server

### API connection errors
- Ensure the FastAPI server is running before starting the bot
- Check that API_URL matches the server address
- Verify API_KEY matches between bot and server

### Database errors
- Delete `war_timer.db` to reset the database
- Check file permissions for database file

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]
