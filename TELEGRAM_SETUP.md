# Telegram ↔️ Claude Integration via Galaxy Map

## Architecture

```
Telegram (your chat)
    ↓
Telegram Bot (galaxy-map/backend/tg_bot.py, runs on server)
    ↓ POST /api/messages
Galaxy Map API (existing FastAPI)
    ↓ polls GET /api/messages?status=pending
Claude Code (this Mac, message_poller.py)
    ↓ (you respond to me through Telegram)
    ↓ PATCH /api/messages/{id}
Telegram Bot reads response
    ↓
Telegram (your chat)
```

## Setup on Server

### 1. Install dependencies
```bash
cd ~/git/galaxy-map/backend
pip install -r requirements.txt
```

### 2. Get Telegram Bot Token
- Talk to [@BotFather](https://t.me/botfather) on Telegram
- Create a new bot, get the token (format: `123456789:ABCdef...`)

### 3. Configure systemd service
```bash
# Copy service file to systemd directory
sudo cp ~/git/galaxy-map/galaxy-map-telegram.service /etc/systemd/system/

# Edit to add your bot token
sudo nano /etc/systemd/system/galaxy-map-telegram.service
# Replace: Environment="TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN_HERE"

# Reload and start
sudo systemctl daemon-reload
sudo systemctl enable galaxy-map-telegram
sudo systemctl start galaxy-map-telegram

# Check status
sudo systemctl status galaxy-map-telegram
sudo journalctl -u galaxy-map-telegram -f  # follow logs
```

## Setup on This Mac

### 1. Install dependencies
```bash
pip install httpx
```

### 2. Start the message poller
```bash
export GALAXY_MAP_URL=http://192.168.50.34:8000
python3 /Users/dbocchiantequera/git/claude-worker/message_poller.py
```

Or with a loop (to auto-restart):
```bash
/claude /loop 10m "python3 /Users/dbocchiantequera/git/claude-worker/message_poller.py"
```

## API Endpoints

All endpoints on Galaxy Map API (`http://192.168.50.34:8000/api/messages`):

### POST /api/messages
Create a message from Telegram bot or any source.
```bash
curl -X POST http://192.168.50.34:8000/api/messages \
  -H "Content-Type: application/json" \
  -d '{"user_id": "123456", "text": "Hello Claude"}'
```

**Response:**
```json
{
  "id": "abc123def456",
  "user_id": "123456",
  "text": "Hello Claude",
  "response": null,
  "status": "pending",
  "created_at": "2026-03-13T10:00:00+00:00",
  "updated_at": "2026-03-13T10:00:00+00:00"
}
```

### GET /api/messages?status=pending
Fetch pending messages (only answered=false).
```bash
curl http://192.168.50.34:8000/api/messages?status=pending
```

### GET /api/messages/{message_id}
Get a single message by ID.
```bash
curl http://192.168.50.34:8000/api/messages/abc123def456
```

### PATCH /api/messages/{message_id}
Update message with response and mark as answered.
```bash
curl -X PATCH http://192.168.50.34:8000/api/messages/abc123def456 \
  -H "Content-Type: application/json" \
  -d '{"response": "Here is my answer...", "status": "answered"}'
```

### GET /api/messages
List all messages (newest first).
```bash
curl http://192.168.50.34:8000/api/messages
```

## Workflow

1. **You send message on Telegram** → Bot receives it
2. **Bot POSTs to Galaxy Map** → Message created with status=`pending`
3. **Message poller detects pending message** → Displays to you in Claude
4. **You respond** → Poller calls PATCH to mark as `answered` with response
5. **Bot polls Galaxy Map** → Sees response, sends to Telegram
6. **You see reply on Telegram** ✓

## Debugging

### Check if Galaxy Map is running
```bash
curl http://192.168.50.34:8000/api/health
# Should return: {"status":"ok","version":"0.2.0"}
```

### Check Telegram bot logs
```bash
sudo journalctl -u galaxy-map-telegram -f
```

### Test bot manually
```bash
# Start bot in foreground
cd ~/git/galaxy-map/backend
TELEGRAM_BOT_TOKEN=YOUR_TOKEN GALAXY_MAP_URL=http://localhost:8000 python3 tg_bot.py
```

### Test poller manually
```bash
export GALAXY_MAP_URL=http://192.168.50.34:8000
python3 /Users/dbocchiantequera/git/claude-worker/message_poller.py
```

## Notes

- Messages timeout after 2 minutes if Claude doesn't respond
- All messages are stored in Galaxy Map SQLite (board.db)
- Telegram bot auto-reconnects on disconnect
- Poller polls every 2 seconds; easily configurable in code
