# FinGuard AI

An AI copilot for fraud & AML (anti-money-laundering) analysts. It flags suspicious
transactions, investigates them with an LLM agent, answers questions from real
regulations with citations, and writes case reports — the way analysts at banks,
fintechs and payment companies work.

Built step by step as a learning project: every phase teaches one core skill an
AI / LLM Engineer is expected to know in interviews.

## Roadmap

| Phase | What we build | Skill you learn |
|---|---|---|
| ✅ 0 | Project setup + synthetic transaction data | Python project structure, venv, git, SQL, test basics |
| ⬜ 1 | "Explain this transaction" with Claude | LLM APIs, prompts, tokens, cost, streaming, error handling |
| ⬜ 2 | Extract data from bank statements / invoices | Structured outputs, JSON schemas, Pydantic, PDF input |
| ⬜ 3 | Ask questions over AML regulations (FATF, etc.) | RAG: chunking, embeddings, vector DB, hybrid search, reranking, citations |
| ⬜ 4 | Measure quality of phases 1–3 | Evals: test sets, LLM-as-judge, retrieval metrics, regression tests |
| ⬜ 5 | Fraud investigation agent | Tool use, agent loops, MCP, SQL tools, sanctions screening |
| ⬜ 6 | ML fraud model + LLM explanations | Classic ML (XGBoost), imbalanced data, SHAP, hybrid ML+LLM systems |
| ⬜ 7 | Production API | FastAPI, Postgres + pgvector, Docker, async, caching |
| ⬜ 8 | Make it safe and observable | Guardrails, PII redaction, prompt injection, tracing, cost tracking |
| ⬜ 9 | Fine-tune a small open model | LoRA / QLoRA, Hugging Face, when fine-tuning beats prompting |
| ⬜ 10 | Analyst dashboard UI | Next.js, TypeScript, streaming chat UI |
| ⬜ 11 | Deploy it | Cloud deploy, CI/CD with GitHub Actions, secrets, monitoring |
| ⬜ 12 | Interview prep | System design for LLM apps, project walkthrough, common questions |

Each phase has notes in [`docs/`](docs/) with the concepts and interview questions.

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

python scripts/generate_data.py      # creates data/finguard.db
pytest
```

## Project layout

```
src/finguard/      the application code (grows each phase)
scripts/           one-off scripts (data generation, etc.)
tests/             pytest tests
docs/              learning notes per phase
data/              local data (git-ignored)
```
