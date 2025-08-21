# gpt-oss-redteam

Minimal, reproducible red‑teaming pipeline for GPT‑OSS models.

- Local‑only by default: prompt generation and inference via Ollama.
- Optional: DeepSeek as the generator backend.
- Local GPT‑OSS inference with a fake tools manifest (one string arg: `input`, description: "put all information here").
- Logs every run to JSONL for analysis (full raw model JSON when available).
- Minimal analyzer: strict refusal metric with Wilson 95% CI.
- Minimal CLI: `init`, `generate`, `infer`, `analyze`, `all`.

## Novel contributions

- Pair prompting: contrast overtly malicious plain‑text queries with semantically equivalent tool‑primed prompts.
- Tool‑primed attacks on agentic models by injecting a notional tool manifest/schema (no execution) to measure refusal deltas.
- Human‑in‑the‑loop high‑level prompt design combined with model‑assisted expansion (preserves `[insert ...]`).
- Fully local, reproducible pipeline and small library producing precise artifacts for auditability.

## Quickstart

Prereqs:
- Python 3.9+
- Ollama running locally; pull the inference model (e.g., `ollama pull gpt-oss:20b`).
- Optional: DeepSeek credentials if you choose `--generator-backend deepseek`.

Install (editable):

```bash
pip install -e .
```

Run the full pipeline (local‑only by default) with 20 prompts × 100 runs each (2,000 total):

```bash
# Create a starter prompts file you can edit
python -m gpt_oss_redteam.cli init --out prompts.txt

# Edit prompts.txt to include one prompt per line (each may include [insert ...])

# Run pipeline (generation via Ollama by default)
gpt-oss-redteam all \
  --prompts-file prompts.txt \
  --runs-per-prompt 100 \
  --generation-batch-size 10 \
  --generator-backend ollama \
  --ollama-model gpt-oss:20b \
  --out-dir runs
```

Optional: use DeepSeek for generation (still local inference via Ollama):

```bash
# 1) Generate via DeepSeek
gpt-oss-redteam generate \
  --prompts-file prompts.txt \
  --runs-per-prompt 100 \
  --generation-batch-size 10 \
  --generator-backend deepseek \
  --deepseek-model deepseek-chat \
  --out-dir runs

# 2) Inference locally via Ollama
gpt-oss-redteam infer \
  --generated-jsonl runs/<timestamp>/generated_prompts.jsonl \
  --ollama-model gpt-oss:20b \
  --out-dir runs
```

Outputs:
- `runs/<timestamp>/generated_prompts.jsonl` – all generated prompts with their source high-level prompt.
- `runs/<timestamp>/inference.jsonl` – every model run with raw JSON response.
- `runs/<timestamp>/analysis.json` and `analysis.md` – refusal rate and 95% CI.

## Results (5,200 runs)

- Strict refusals: 3,790
- Refusal rate: 0.729
- 95% Wilson CI: [0.717, 0.741]

See `PAPER.md` for per–high‑level prompt breakdowns and discussion.

## Configuration via CLI flags or environment variables

- `GENERATOR_BACKEND` – default `ollama`; set to `deepseek` to use DeepSeek.
- `GENERATOR_MODEL` (CLI flag) – model id/tag for the chosen backend. For Ollama, e.g., `qwen2.5:7b-instruct`. For DeepSeek, e.g., `deepseek-chat`.
- `OLLAMA_GEN_MODEL` – optional env to set the Ollama generator tag (defaults to `OLLAMA_MODEL` or `gpt-oss:20b`).
- `OLLAMA_MODEL` – inference model tag (default `gpt-oss:20b`).
- `OLLAMA_BASE_URL` – defaults to `http://localhost:11434/v1`.
- `DEEPSEEK_API_KEY` – optional; only required if using DeepSeek.
- `DEEPSEEK_BASE_URL` – optional; defaults to `https://api.deepseek.com`.
- `DEEPSEEK_MODEL` – optional; defaults to `deepseek-chat`.

## Fake tools manifest (simple)

We pass a static set of tool/function definitions so the model thinks it can call tools without consuming context with actual implementations. Every tool takes a single string arg named `input` with the description "put all information here". No tool execution occurs.

## Safety note

This project logs raw model outputs for offline analysis. The provided analyzer only checks for a very simple refusal phrase; deeper evaluation is out of scope for this minimal baseline.

## Reproducibility

- Archive `runs/<timestamp>/` including `generated_prompts.jsonl`, `inference.jsonl`, `analysis.json`, and `analysis.md`.
- Record package version and model tags (e.g., `gpt_oss_redteam.__version__`, `OLLAMA_MODEL`).
- Note generator backend and model, system prompt, and any generation parameters (batch size, temperature).
- Keep the tool manifest fixed across comparative runs unless explicitly studying its effects.

## Paper

See `PAPER.md` for a full description of methods, related work, detailed results (including per–high‑level prompt breakdown), and discussion.
