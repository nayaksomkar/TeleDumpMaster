# TeleDumpMaster

A tool that watches a folder on your computer and automatically uploads any new files to a Telegram channel. Files are uploaded in the correct order (episode 1, then 2, then 3... not 1, 10, 11, 2).

---

## How to use with Docker (easiest, runs 24/7)

**Step 1 — Get the code**
```bash
git clone https://github.com/nayaksomkar/TeleDumpMaster.git
cd TeleDumpMaster
```

**Step 2 — Set up your settings**
```bash
cp .env.example .env
```
Now open the `.env` file with any text editor and fill in:
- Your bot token (from @BotFather on Telegram)
- Your channel ID (where files should be uploaded)
- The folder path you want to watch

**Step 3 — Start it**
```bash
docker compose up -d
```

**Step 4 — See what's happening**
```bash
docker compose logs -f
```
Press `Ctrl+C` to stop watching the logs. The tool keeps running.

**Step 5 — Stop it**
```bash
docker compose down
```

> **Want to watch your own folder?** Open `docker-compose.yml` and replace `./uploads` with your folder path.

---

## How to use without Docker (just terminal)

**You'll need:** Python 3.11 or higher and pip (Python's package installer).

```bash
# 1. Get the code
git clone https://github.com/nayaksomkar/TeleDumpMaster.git
cd TeleDumpMaster

# 2. Set up your settings
cp .env.example .env
# Open .env and put in your bot token, channel ID, and folder path

# 3. Install everything
pip install -e .

# 4. Run it (keeps watching until you stop it)
teledumpmaster

# Press Ctrl+C to stop

# Or run once (upload everything and exit):
teledumpmaster --once
```

---

## Settings explained

Everything goes in the `.env` file. Here's what each setting does:

| Setting | Need it? | Default | What it does |
|---|---|---|---|
| `TELEDUMP_BOT_TOKEN` | ✅ Yes | — | Your bot's secret key from @BotFather |
| `TELEDUMP_CHANNEL_ID` | ✅ Yes | — | Where to upload (like `-1001234567890`) |
| `TELEDUMP_UPLOAD_FOLDER` | ✅ Yes | — | Which folder to watch for new files |
| `TELEDUMP_POLL_INTERVAL` | ❌ No | `5` | Check for new files every X seconds |
| `TELEDUMP_RETRIES` | ❌ No | `3` | Try uploading again if it fails |
| `TELEDUMP_TIMEOUT` | ❌ No | `60` | Wait X seconds before giving up on a file |
| `TELEDUMP_POST_ACTION` | ❌ No | `keep` | What to do after upload: `keep` / `delete` / `archive` |
| `TELEDUMP_CAPTION` | ❌ No | `""` | A message to send with every file |
| `TELEDUMP_ARCHIVE_DIR` | ❌ No | `./archive` | Where to move files if action is `archive` |
| `TELEDUMP_LOG_DIR` | ❌ No | `./logs` | Where to save upload history |
| `TELEDUMP_LOG_FORMAT` | ❌ No | `json` | How to save history: `json` / `csv` / don't save |

---

## Project files

```
teledumpmaster/     → The main code
tests/              → Test files
.env.example        → Settings template (copy to .env)
Dockerfile          → For building Docker image
docker-compose.yml  → For running with Docker
```

---

## For developers

```bash
uv sync --extra dev
uv run ruff check .
uv run mypy teledumpmaster
uv run pytest
```

---

## License

MIT
