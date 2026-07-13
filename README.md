# TeleDumpMaster

Watches a folder and auto-uploads files to a Telegram channel in natural order (episode 1 → 2 → 3, not 1 → 10 → 11).

---

## Docker (runs 24/7)

```bash
git clone https://github.com/nayaksomkar/TeleDumpMaster.git
cd TeleDumpMaster
cp .env.example .env          # then edit .env with your settings
docker compose up -d           # start
docker compose logs -f         # watch logs (Ctrl+C to exit, keeps running)
docker compose down            # stop
```

> To watch your own folder, edit `docker-compose.yml` — change `./uploads` to your path.

---

## Terminal (no Docker)

**Requires:** Python 3.11+

```bash
git clone https://github.com/nayaksomkar/TeleDumpMaster.git
cd TeleDumpMaster
cp .env.example .env           # then edit .env with your settings
pip install -e .
teledumpmaster                 # watch forever (Ctrl+C to stop)
teledumpmaster --once          # upload everything once, then exit
```

---

## Commands

| Command | What it does |
|---|---|
| `teledumpmaster` | Watch & upload forever |
| `--once` | Upload everything once, then exit |
| `--dry-run` | List files that would upload, don't send |
| `--no-progress` | Hide progress bar (clean for logs) |
| `--log-level DEBUG` | Show detailed logs |
| `--caption` | Use each file's name as its caption |
| `--caption "text"` | Set a custom caption for all files |
| `--dotenv my.env` | Use a custom env file |
| `--help` | Show all options |

Examples:
```bash
teledumpmaster --caption              # file "song.mp3" → caption "song.mp3"
teledumpmaster --caption "My file"    # every file gets caption "My file"
teledumpmaster --once --caption       # upload once with filenames as captions
```

---

## What the output looks like

```
Uploading:  60%|████████    | 3/5 [00:12<00:08,  4.0s/file, file=episode3.mp4, size=15.2 MB, speed=3.8 MB/s]
  ✓ episode1.mp4  (10.5 MB @ 5.2 MB/s)
Done! Uploaded 3 file(s), 45.8 MB total, avg 3.8 MB/s, in 12.0s
```

The bar shows progress, ETA, current file name, size, and upload speed. The summary shows totals.

---

## Settings (in `.env`)

| Setting | Required | Default | What it does |
|---|---|---|---|
| `TELEDUMP_BOT_TOKEN` | ✅ | — | Bot token from @BotFather |
| `TELEDUMP_CHANNEL_ID` | ✅ | — | Channel ID (use @getidsbot to find it) |
| `TELEDUMP_UPLOAD_FOLDER` | ✅ | — | Folder to watch for files |
| `TELEDUMP_POLL_INTERVAL` | ❌ | `5` | Check every X seconds |
| `TELEDUMP_RETRIES` | ❌ | `3` | Retry failed uploads this many times |
| `TELEDUMP_TIMEOUT` | ❌ | `60` | Give up after X seconds |
| `TELEDUMP_POST_ACTION` | ❌ | `keep` | `keep`, `delete`, or `archive` after upload |
| `TELEDUMP_CAPTION` | ❌ | `""` | Caption sent with every file |
| `TELEDUMP_ARCHIVE_DIR` | ❌ | `./archive` | Where to move files if action is `archive` |
| `TELEDUMP_LOG_DIR` | ❌ | `./logs` | Where upload history is saved |
| `TELEDUMP_LOG_FORMAT` | ❌ | `json` | Log format: `json`, `csv`, or `none` |

---

## Troubleshooting

- **"chat not found"** — Add bot as admin to the channel. Check channel ID (use @getidsbot).
- **"bot token is required"** — You forgot to fill `.env`. Set `TELEDUMP_BOT_TOKEN=your_token`.
- **Progress bar garbled in Docker** — Add `--no-progress` to `docker-compose.yml`.
- **Files not picked up** — Check the folder path exists. Already-uploaded files are skipped.

---

## Dev

```bash
uv sync --extra dev
uv run ruff check .
uv run mypy teledumpmaster
uv run pytest
```

---

## License

MIT
