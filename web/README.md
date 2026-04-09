# GNS Live Dashboard

This is the public Next.js dashboard for the geopolitical narrative live monitor.

## Local development

```bash
npm install
npm run dev
```

Set these environment variables in `web/.env.local` for local Blob access:

```bash
GNS_BLOB_SNAPSHOT_PATH=dashboard/live/latest.json
BLOB_READ_WRITE_TOKEN=your_vercel_blob_token
```
