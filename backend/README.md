# ChessCoach AI Backend

FastAPI backend for ChessCoach AI, providing:
- Stockfish analysis (`/api/v1/analyze`, SSE stream)
- Coaching explanations (`/api/v1/coach/explain`) via Groq -> Gemini -> OpenRouter fallback
- Full game review (`/api/v1/review/game`)
- JWT auth and saved game APIs
- RAG retrieval from classic chess book embeddings in Postgres/pgvector

## Local Run

1. Copy `.env.example` to `.env` and fill values.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run server:
   ```bash
   uvicorn app.main:app --reload --port 7860
   ```

## Ingest Book Embeddings

```bash
python -m app.rag.ingest
```

or

```bash
python scripts/run_ingestion.py
```

## API Docs

- Swagger: `http://localhost:7860/docs`
- ReDoc: `http://localhost:7860/redoc`
