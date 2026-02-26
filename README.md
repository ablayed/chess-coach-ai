# ChessCoach AI

## Live Demo

**[Try it here](https://chesscoach-ai.pages.dev)**

**The chess engine that explains the *why*.**

ChessCoach AI combines Stockfish engine analysis with chess book knowledge and LLM-powered coaching to explain chess positions in natural language, not just what the best move is, but *why* it is the best move.

![Screenshot](docs/screenshot.png)

## Features

- **Engine Analysis**: Stockfish 18 at depth 20 with multi-PV (top 3 lines)
- **AI Coaching**: Natural language explanations powered by Groq LLaMA 3.3 70B
- **RAG Knowledge Base**: 2900+ embedded passages from classic chess books (Capablanca, Nimzowitsch, Lasker, Tarrasch) plus Wikipedia/Wikibooks
- **Game Review**: Import PGN or Lichess games for full move-by-move analysis with accuracy scoring
- **Move Classification**: Brilliant, great, good, inaccuracy, mistake, blunder with coaching for critical moments
- **Position Concepts**: Auto-detect opening/middlegame/endgame, tactical motifs, and strategic themes

## Architecture

```text
Frontend (Next.js 14 + react-chessboard + Tailwind)
        |
     REST + SSE
        |
Backend (FastAPI + Python)
        |
        +-- Stockfish 18 (async pool, UCI protocol)
        +-- RAG pipeline (sentence-transformers + pgvector)
        +-- LLM coaching (Groq -> Gemini -> OpenRouter fallback)
        |
Neon PostgreSQL (pgvector for embeddings)
```

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 14, TypeScript, react-chessboard, chess.js, Tailwind CSS, Zustand |
| Backend | FastAPI, python-chess, Stockfish 18, sentence-transformers |
| Database | Neon PostgreSQL + pgvector |
| AI/ML | Groq API (LLaMA 3.3 70B), all-MiniLM-L6-v2 embeddings |
| RAG Sources | Public-domain books + Wikipedia + Wikibooks |

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Stockfish binary ([download](https://stockfishchess.org/download/))
- Neon PostgreSQL account ([free](https://neon.tech))
- Groq API key ([free](https://console.groq.com))

### Setup

```bash
# Backend
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
python -m scripts.run_ingestion

# Frontend
cd frontend
npm install
cp .env.local.example .env.local
```

### Run

```bash
# Terminal 1: Backend
cd backend && venv\Scripts\activate
uvicorn app.main:app --port 7860

# Terminal 2: Frontend
cd frontend && npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## How It Works

1. You play a move on the board.
2. Stockfish analyzes the position at depth 20 with top 3 lines.
3. Concept extraction finds tactical motifs and strategic themes.
4. RAG retrieval pulls relevant passages from the chess knowledge base.
5. The LLM generates coaching in natural language.
6. You get actionable feedback on why a move is strong or weak.

## Project Structure

```text
chess-coach-ai/
  frontend/
    src/app/
    src/components/
    src/stores/
    src/lib/
  backend/
    app/api/
    app/services/
    app/core/
    app/rag/
    app/models/
  docs/
  README.md
```

## Legal

RAG content is sourced from:

- Public-domain books
- Lichess public data
- Wikipedia/Wikibooks content

## License

MIT
