# War Bot - Discord Timer Tracking System

A Discord bot integrated with a FastAPI backend for tracking war timers. The system allows users to record timer events through Discord commands, which are stored in a SQLite database via a REST API.

## Features

- **Discord Bot Integration**: Easy-to-use commands for recording timers
- **Desktop GUI App**: Native Python window for quick timer entry
- **Live Dashboard**: Auto-updating Discord embed showing all active timers
- **Pro Drop Alerts**: Automatic alerts 5-10 minutes before Pro Drop windows
- **REST API Backend**: FastAPI-powered backend with full CRUD operations
- **Automatic Calculations**: Pro Drop windows calculated based on timer type
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

**Quick Commands (Auto-capture current time):**
- `!whacked Mucci` - Record a pro whack for Mucci with current time
  - Bot responds: "💀 Mucci was whacked at 14:30:25 - Pro Drop: 14:45:25"
  - Can also use: `!whacked` (uses your Discord name)
- `!hit Mucci` - Record a friendly hit for Mucci with current time
  - Bot responds: "🛡️ Mucci was hit at 14:30:25 - Pro Drop (safe window): 18:10:25 - 18:50:25"
  - Can also use: `!hit` (uses your Discord name)
- `!enemy Mucci` - Record an enemy hit for Mucci with current time
  - Bot responds: "⚔️ Mucci got hit by enemy at 14:30:25 - Enemy Pro Drop starts: 18:10:25"
  - Can also use: `!enemy` (uses your Discord name)

**Manual Time Commands:**
- `!im_hit HH:MM:SS` - Record a friendly hit timer with specific time
  - Example: `!im_hit 14:30:25`
- `!pro_whack HH:MM:SS` - Record a pro whack timer with specific time
  - Example: `!pro_whack 09:15:30`
- `!enemy_hit HH:MM:SS` - Record an enemy hit timer with specific time
  - Example: `!enemy_hit 12:45:00`

**Dashboard Commands:**
- `!setup_dashboard` - Create a live-updating dashboard in the current channel
- `!clear_timers` - Clear all active timers

**Features:**
- **Live Dashboard**: Auto-updates every 5 seconds with all active timers
- **Instant Responses**: Bot tells you the Pro Drop time immediately
- **Pro Drop Alerts**: Automatically alerts users 5-10 minutes before their Pro Drop window
- **Timezone Aware**: All timestamps are UTC-based

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

### Timer Types & Pro Drop Calculations

- **`friendly_hit`** - Friendly fire event
  - Pro Drop Start: Time Shot + 3h 40m
  - Pro Drop End: Time Shot + 4h 20m

- **`pro_whack`** - Pro whack event
  - Pro Drop: Time Shot + 15m

- **`enemy_hit`** - Enemy attack event
  - Pro Drop Start: Time Shot + 3h 40m
  - No end time (enemy window)

## Desktop App

A native Python desktop application is available for quick timer entry with instant Discord updates.

**Features:**
- Native desktop window (no browser needed)
- Quick timer entry with one-click buttons
- "Use Now" button for current time
- Real-time display of all active timers
- Auto-refreshes every 5 seconds
- Instant sync with Discord bot

**Usage:**
```bash
python timer_app.py
```

The app window will open showing:
- Input fields for player name and time
- Three big buttons: 🛡️ Friendly Hit, 💀 Pro Whack, ⚔️ Enemy Hit
- Live display of all active timers with Pro Drop calculations
- Auto-refresh status

When you click a button, the timer is:
1. Sent to the API
2. Saved to the database
3. Instantly appears on Discord dashboard
4. Shows in the desktop app

## Configuration

Configuration can be customized via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| DISCORD_TOKEN | - | Discord bot token (required) |
| API_KEY | - | API authentication key (required) |
| API_URL | http://127.0.0.1:8000 | API base URL |
| DASHBOARD_CHANNEL_ID | - | Discord channel ID for dashboard (optional) |
| ALERT_CHANNEL_ID | - | Discord channel ID for alerts (optional, defaults to dashboard channel) |
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
├── timer_app.py        # Desktop GUI app
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
