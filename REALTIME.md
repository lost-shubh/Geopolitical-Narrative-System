# Real-Time Mode

This project now supports strict live-news mode with continuous refresh and live display.

## 1) Set API key

Create `.env` in project root:

```env
NEWS_API_KEY=your_newsapi_key
```

For GitHub Codespaces, do not put only the raw key in the file. It must be exactly:

```bash
echo 'NEWS_API_KEY=your_newsapi_key' > .env
```

## 2) Run live monitor (terminal dashboard)

```powershell
.\venv\Scripts\python.exe run_realtime.py --interval 60
```

Useful flags:

```powershell
.\venv\Scripts\python.exe run_realtime.py --topic "iran OR israel OR diplomacy" --days 1 --max-articles 25 --interval 30
.\venv\Scripts\python.exe run_realtime.py --max-cycles 3
```

Live snapshots are written to:

- `data/processed/realtime/live_snapshot.json`
- `data/processed/realtime/live_history.jsonl`

## 3) Open web dashboard (optional)

Run in another terminal:

```powershell
.\venv\Scripts\streamlit.exe run src/realtime/dashboard.py
```

The dashboard auto-refreshes and reads the latest snapshot from the live monitor.

## Notes

- `config/pipeline_config.yaml` defaults to real-time mode (`realtime_only: true`).
- Stage 1 strict live mode requires `NEWS_API_KEY`.
- Stage 2 derives reaction rows from live article text when no social export is provided.
- To analyze real public reactions, pass a JSON export with `--comments-file`:

```powershell
.\venv\Scripts\python.exe run_pipeline.py --comments-file data\raw\social\comments.json --live
```

The social JSON can be a list of comment objects or `{ "comments": [...] }`. Supported text fields include `text`, `body`, `comment`, `content`, and `message`; optional fields include `platform`, `topic`, `timestamp`, `author`, `url`, and engagement counts.
- Stage 4 can add Google Fact Check evidence when `GOOGLE_FACTCHECK_API_KEY` is configured.

## GitHub Codespaces

Codespaces is Linux, so Windows commands like `.\venv\Scripts\python.exe` will not work there.

Use:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements-codespaces.txt
echo 'NEWS_API_KEY=your_newsapi_key' > .env
python run_realtime.py --query "geopolitics" --interval 60
```

To run the dashboard in Codespaces:

```bash
source .venv/bin/activate
streamlit run src/realtime/dashboard.py --server.address 0.0.0.0 --server.port 8501
```

Open forwarded port `8501` in the Codespaces UI.

If you rebuild the Codespace after this commit, `.devcontainer/devcontainer.json` will provision Python 3.11 and install `requirements-codespaces.txt` automatically.
