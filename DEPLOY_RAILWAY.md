# Deploying to Railway

This guide walks through deploying the full RAG Assistant Studio stack on [Railway](https://railway.com).

## Architecture on Railway

| Service        | Source                          | Port  | Notes                       |
|----------------|--------------------------------|-------|-----------------------------|
| **api**        | `Dockerfile` (repo root)       | 8000  | FastAPI backend             |
| **worker**     | `deploy/Dockerfile.worker`     | —     | Temporal worker (no port)   |
| **streamlit**  | `deploy/Dockerfile.streamlit`  | 8501  | Streamlit UI                |
| **temporal**   | Docker image                   | 7233  | Temporal server             |
| **postgres**   | Railway plugin                 | 5432  | Temporal persistence        |

## Step-by-step

### 1. Create a Railway project

```bash
# Install the Railway CLI
npm install -g @railway/cli

# Login
railway login

# Create a new project
railway init
```

### 2. Add PostgreSQL

In the Railway dashboard:
1. Click **+ New** → **Database** → **PostgreSQL**
2. Note the `DATABASE_URL` from the **Variables** tab — you'll need the individual parts for Temporal.

### 3. Deploy Temporal Server

Add a new service from Docker image:
1. Click **+ New** → **Docker Image**
2. Image: `temporalio/auto-setup:1.24.2`
3. Set these environment variables:

```
DB=postgres12
DB_PORT=5432
POSTGRES_USER=<from Railway Postgres>
POSTGRES_PWD=<from Railway Postgres>
POSTGRES_SEEDS=<Railway Postgres internal hostname>
```

4. Add an internal networking alias: `temporal` on port `7233`

### 4. Deploy the API service

1. Click **+ New** → **GitHub Repo** → select this repo
2. Railway will auto-detect the root `Dockerfile`
3. Set environment variables:

```
PORT=8000
TEMPORAL_ADDRESS=temporal.railway.internal:7233
DATABASE_URL=sqlite:///./data/assistants.db
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
PINECONE_API_KEY=<your key>
PINECONE_INDEX_NAME=rag-assistant
PINECONE_HOST=<your pinecone host>
AZURE_DOCINTEL_ENDPOINT=<if using Azure Doc Intelligence>
AZURE_DOCINTEL_KEY=<if using Azure Doc Intelligence>
```

4. Set the start command (or rely on railway.json):
```
uvicorn src.app.main:app --host 0.0.0.0 --port ${PORT:-8000}
```

5. Under **Settings** → **Networking**, generate a public domain.

### 5. Deploy the Worker service

1. Click **+ New** → **GitHub Repo** → select this repo again
2. Under **Settings** → **Build**, set Dockerfile path to `deploy/Dockerfile.worker`
3. Set environment variables:

```
TEMPORAL_ADDRESS=temporal.railway.internal:7233
DATABASE_URL=sqlite:///./data/assistants.db
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
PINECONE_API_KEY=<your key>
PINECONE_INDEX_NAME=rag-assistant
PINECONE_HOST=<your pinecone host>
```

> The worker has no public port — it connects outbound to Temporal.

### 6. Deploy the Streamlit UI

1. Click **+ New** → **GitHub Repo** → select this repo again
2. Under **Settings** → **Build**, set Dockerfile path to `deploy/Dockerfile.streamlit`
3. Set environment variables:

```
PORT=8501
API_BASE_URL=https://<your-api-service>.up.railway.app
```

4. Under **Settings** → **Networking**, generate a public domain.

### 7. Verify

- **API health**: `curl https://<api-domain>.up.railway.app/health`
- **Streamlit UI**: Open `https://<streamlit-domain>.up.railway.app` in browser
- **Temporal UI**: If you exposed it, check workflows at port 8080

## Shared Variables (recommended)

Use Railway's **Shared Variables** feature to avoid duplicating secrets:
1. Go to project **Settings** → **Shared Variables**
2. Add all API keys there once
3. Reference them from each service using `${{shared.OPENAI_API_KEY}}`

## Notes

- The API and Worker both use SQLite by default (`sqlite:///./data/assistants.db`). For production, consider switching to the Railway PostgreSQL instance.
- Railway assigns a `PORT` env var automatically — the configs respect this via `${PORT:-default}`.
- The worker service needs no public domain; it only makes outbound connections to Temporal.
