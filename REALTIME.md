# Real-Time Mode

This project now supports strict live-news mode with continuous refresh and live display.

## 1) Set API key

Create `.env` in project root:

```env
NEWS_API_KEY=your_newsapi_key
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
- Stage 2 now derives reaction rows from live article text (news-only pipeline, no mock social dataset).
