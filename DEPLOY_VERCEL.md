# Vercel Deployment

This branch deploys the public dashboard as a Next.js app in `web/`, uses Vercel Blob for the latest JSON snapshot, and refreshes the snapshot from GitHub Actions.

## Architecture

- `web/`: public Next.js dashboard hosted on Vercel
- `src/realtime/publish_live_snapshot.py`: one-shot Python publisher
- `Vercel Blob`: stores `dashboard/live/latest.json`
- `GitHub Actions`: refreshes the Blob snapshot every 30 minutes

## 1. Create the Blob store

In Vercel:

1. Open your project.
2. Add **Blob** storage.
3. Keep the store public.
4. Note the pathname you want to use. Default in this branch: `dashboard/live/latest.json`

## 2. Import the repo into Vercel

When creating the Vercel project:

1. Select this repository.
2. Set the **Root Directory** to `web`
3. Framework preset: **Next.js**

## 3. Add Vercel environment variables

Add these in the Vercel project settings:

- `BLOB_READ_WRITE_TOKEN`
- `GNS_BLOB_SNAPSHOT_PATH`

Recommended value:

- `GNS_BLOB_SNAPSHOT_PATH=dashboard/live/latest.json`

## 4. Add GitHub secrets and variables

In GitHub repository settings:

Secrets:

- `NEWS_API_KEY`
- `BLOB_READ_WRITE_TOKEN`

Variables:

- `GNS_BLOB_SNAPSHOT_PATH=dashboard/live/latest.json`
- `GNS_LIVE_QUERY=geopolitics`
- `GNS_MAX_ARTICLES=36`
- `GNS_MAX_HEADLINES=12`

## 5. Trigger the first publish

Run the GitHub Actions workflow:

- **Actions** -> **Publish Live Snapshot** -> **Run workflow**

This uploads the first JSON snapshot to Blob.

## 6. Deploy the website

After the first snapshot exists, deploy the Vercel project from this branch or open a PR from this branch.

## 7. Attach a custom domain

Optional in Vercel:

1. Open project settings.
2. Add your domain.
3. Follow the DNS instructions Vercel provides.

## Local commands

Local snapshot only:

```bash
python -m src.realtime.publish_live_snapshot --skip-upload
```

Local publish to Blob:

```bash
python -m pip install -r requirements-live-web.txt
python -m src.realtime.publish_live_snapshot --blob-path dashboard/live/latest.json
```
