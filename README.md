# dloader

A minimal web app that runs `yt-dlp -N 10 <url>` inside a container and stores the output in a mounted volume at `/download`.

## Run locally (Docker)

```bash
docker build -t dloader:latest .
docker run --rm -p 8000:8000 -v /path/on/host:/download dloader:latest
```

Open `http://localhost:8000` and submit a URL. Optionally set a subdirectory (relative to `/download`) to place the file(s).

## Run from Docker Hub

```bash
docker pull assaffeuerstein/dloader:latest
docker run --rm -p 8000:8000 -v /path/on/host:/download assaffeuerstein/dloader:latest
```

## Notes
- The container expects a volume mounted at `/download`.
- Subdirectories are validated; only letters, numbers, dots, dashes, underscores, and `/` are allowed.
- Downloads run synchronously; the page will show logs after completion.

## GitHub Actions
Workflow: `.github/workflows/docker-publish.yml`

Set these secrets in your repo:
- `DOCKERHUB_USERNAME`
- `DOCKERHUB_TOKEN`

Adjust `IMAGE_NAME` or tagging strategy as needed.
