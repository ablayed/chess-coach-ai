# ChessCoach AI Backend

FastAPI backend for ChessCoach AI, providing:
- Stockfish analysis (`/api/v1/analyze`, SSE stream)
- Coaching explanations (`/api/v1/coach/explain`) via Groq -> Gemini -> OpenRouter fallback
- Full game review (`/api/v1/review/game`)
- JWT auth and saved game APIs
- RAG retrieval from classic chess book embeddings in Postgres/pgvector

## Local Run

1. Copy `.env.example` to `.env` and fill values.
2. Create and activate a Python 3.14 virtual environment:
   ```powershell
   cd C:\Users\diaab\chess-coach-ai\backend
   py -3.14 -m venv venv
   venv\Scripts\activate
   ```
3. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
4. Run server:
   ```powershell
   uvicorn app.main:app --reload --port 7860
   ```

For every new backend terminal session:

```powershell
cd C:\Users\diaab\chess-coach-ai\backend
venv\Scripts\activate
```

If activation worked, your prompt starts with `(venv)`.

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
