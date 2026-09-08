# Chunky

Ask a question in a Next.js chat UI. Attach a PDF only when you want retrieval-augmented generation.

- **No PDF:** question → LLM → answer
- **With PDF:** extract → chunk → embed → vector search → LLM → answer

## Backend layout

```
backend/app
  api/                 HTTP layer
    deps.py            request dependencies
    v1/                versioned routes
  core/                config, logging, errors, enums
  db/                  SQLAlchemy engine, sessions, bootstrap
  models/              database models
  schemas/             request/response contracts
  repositories/        data access
  services/            use cases (upload, chat, RAG)
  ingest/              PDF validation, hashing, chunking
  clients/             OpenAI and Chroma adapters
  storage/             PDF file storage
  main.py              application factory
```

Routes live under `/api/v1`. `/health` stays at the root for process probes.

## Setup

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Put your OpenAI key in `backend/.env`:

```
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small
```

Start the API:

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

Run tests:

```bash
cd backend
source .venv/bin/activate
pytest
```

### Frontend

```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). The Next.js app proxies `/backend/*` to FastAPI.

## API

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Process health |
| `POST` | `/api/v1/documents/upload` | Validate, hash, dedupe, process PDF |
| `GET` | `/api/v1/documents/{document_id}` | Document status |
| `POST` | `/api/v1/chat` | Answer with or without RAG |

`POST /api/v1/chat` body:

```json
{
  "question": "What is this document about?",
  "document_id": null
}
```

Omit `document_id` (or send `null`) for a direct LLM answer. Send a ready document id to retrieve chunks first.
