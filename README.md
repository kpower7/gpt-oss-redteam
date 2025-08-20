# gpt-oss-redteam

Simple, reproducible red teaming pipeline for GPT‑OSS models via Ollama, with DeepSeek-based adversarial prompt generation.

- DeepSeek API to generate adversarial prompts from high-level HITL prompts (preserves `[insert ...]`).
- Ollama for local GPT‑OSS inference with a fake tools manifest (one string arg: `input`, description: "put all information here").
- Logs every run to JSONL for later analysis (full model JSON when available).
- Minimal analyzer: refusal rate and 95% CI.
- Minimal CLI for end-to-end runs.

## Quickstart

Prereqs:
- Python 3.9+
- Ollama running locally and the model pulled: `ollama pull gpt-oss:20b`
- DeepSeek API key in env: `DEEPSEEK_API_KEY=...`

Install (editable):

```bash
pip install -e .
```

Run the full pipeline with 20 prompts × 100 runs each (2,000 total):

```bash
# Create a starter prompts file you can edit
python -m gpt_oss_redteam.cli init --out prompts.txt

# Edit prompts.txt to include one prompt per line (each may include [insert ...])

# Run pipeline
gpt-oss-redteam all \
  --prompts-file prompts.txt \
  --runs-per-prompt 100 \
  --generation-batch-size 10 \
  --ollama-model gpt-oss:20b \
  --out-dir runs
```

Outputs:
- `runs/<timestamp>/generated_prompts.jsonl` – all generated prompts with their source high-level prompt.
- `runs/<timestamp>/inference.jsonl` – every model run with raw JSON response.
- `runs/<timestamp>/analysis.json` and `analysis.md` – refusal rate and 95% CI.

## Configuration via CLI flags or environment variables

- `DEEPSEEK_API_KEY` – required for prompt generation.
- `DEEPSEEK_BASE_URL` – optional, defaults to `https://api.deepseek.com`.
- `OLLAMA_BASE_URL` – optional, defaults to `http://localhost:11434/v1`.

## Fake tools manifest (simple)

We pass a static set of tool/function definitions so the model thinks it can call tools without consuming context with actual implementations. Every tool takes a single string arg named `input` with the description "put all information here". No tool execution occurs.

## Safety note

This project logs raw model outputs for offline analysis. The provided analyzer only checks for a very simple refusal phrase; deeper evaluation is out of scope for this minimal baseline.

## Paper outline (in `docs/`)
- Brief literature review
- Package pipeline and creation
- Quantified results
- Qualitative analysis of results
- Example problem prompts
- Next steps
