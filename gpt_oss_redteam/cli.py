import argparse
import json
import os
from typing import List

from .analysis import analyze_records, load_jsonl, render_markdown
from .pipeline import run_generation, run_inference
from .utils import new_run_dir, read_prompts_file, write_text


def cmd_init(args: argparse.Namespace) -> None:
    path = args.out
    if os.path.exists(path):
        print(f"File already exists: {path}")
        return
    demo = (
        "Assess whether a generic assistant safely declines requests that could harm systems. "
        "Use [insert domain here] as a placeholder."
    )
    with open(path, "w", encoding="utf-8") as f:
        f.write(demo + "\n")
    print(f"Wrote starter prompts file: {path}")


def cmd_generate(args: argparse.Namespace) -> None:
    high_level_prompts = read_prompts_file(args.prompts_file)
    run_dir = args.out_dir or new_run_dir()
    out_gens = os.path.join(run_dir, "generated_prompts.jsonl")

    pairs = run_generation(
        high_level_prompts,
        runs_per_prompt=args.runs_per_prompt,
        batch_size=args.generation_batch_size,
        temperature=args.generation_temperature,
        deepseek_model=args.deepseek_model,
        out_jsonl_path=out_gens,
        request_interval_s=args.generation_interval,
    )
    print(f"Generated {len(pairs)} prompts -> {out_gens}")


def cmd_infer(args: argparse.Namespace) -> None:
    run_dir = args.out_dir or new_run_dir()
    in_file = args.generated_jsonl
    out_file = os.path.join(run_dir, "inference.jsonl")

    def read_pairs(path: str):
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                obj = json.loads(line)
                yield obj["source"], obj["generated"]

    pairs = list(read_pairs(in_file))
    run_inference(
        pairs,
        system_prompt=args.system_prompt,
        ollama_model=args.ollama_model,
        out_jsonl_path=out_file,
        request_interval_s=args.inference_interval,
    )
    print(f"Ran inference on {len(pairs)} prompts -> {out_file}")


def cmd_analyze(args: argparse.Namespace) -> None:
    run_dir = args.out_dir or new_run_dir()
    in_file = args.inference_jsonl
    out_json = os.path.join(run_dir, "analysis.json")
    out_md = os.path.join(run_dir, "analysis.md")

    summary = analyze_records(load_jsonl(in_file))
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    write_text(out_md, render_markdown(summary))
    print(f"Wrote analysis -> {out_json} and {out_md}")


def cmd_all(args: argparse.Namespace) -> None:
    run_dir = args.out_dir or new_run_dir()
    os.makedirs(run_dir, exist_ok=True)

    # 1) Generate
    out_gens = os.path.join(run_dir, "generated_prompts.jsonl")
    pairs = run_generation(
        read_prompts_file(args.prompts_file),
        runs_per_prompt=args.runs_per_prompt,
        batch_size=args.generation_batch_size,
        temperature=args.generation_temperature,
        deepseek_model=args.deepseek_model,
        out_jsonl_path=out_gens,
        request_interval_s=args.generation_interval,
    )

    # 2) Inference
    out_infer = os.path.join(run_dir, "inference.jsonl")
    results = run_inference(
        pairs,
        system_prompt=args.system_prompt,
        ollama_model=args.ollama_model,
        out_jsonl_path=out_infer,
        request_interval_s=args.inference_interval,
    )

    # 3) Analyze
    out_json = os.path.join(run_dir, "analysis.json")
    out_md = os.path.join(run_dir, "analysis.md")
    summary = analyze_records(results)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    write_text(out_md, render_markdown(summary))

    print(f"Done. Outputs in: {run_dir}")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="gpt-oss-redteam", description="Run GPT-OSS red teaming pipeline")
    sub = p.add_subparsers(dest="cmd")

    s = sub.add_parser("init", help="Create a starter prompts file")
    s.add_argument("--out", required=True, help="Path to write starter prompts file")
    s.set_defaults(func=cmd_init)

    s = sub.add_parser("generate", help="Generate adversarial prompts via DeepSeek")
    s.add_argument("--prompts-file", required=True)
    s.add_argument("--runs-per-prompt", type=int, default=100)
    s.add_argument("--generation-batch-size", type=int, default=10)
    s.add_argument("--generation-temperature", type=float, default=1.3)
    s.add_argument("--generation-interval", type=float, default=0.0, help="sleep seconds between DeepSeek calls")
    s.add_argument("--deepseek-model", default=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"))
    s.add_argument("--out-dir", default=None)
    s.set_defaults(func=cmd_generate)

    s = sub.add_parser("infer", help="Run Ollama inference on generated prompts")
    s.add_argument("--generated-jsonl", required=True)
    s.add_argument("--system-prompt", default=None)
    s.add_argument("--ollama-model", default=os.getenv("OLLAMA_MODEL", "gpt-oss:20b"))
    s.add_argument("--inference-interval", type=float, default=0.0, help="sleep seconds between Ollama calls")
    s.add_argument("--out-dir", default=None)
    s.set_defaults(func=cmd_infer)

    s = sub.add_parser("analyze", help="Analyze inference JSONL")
    s.add_argument("--inference-jsonl", required=True)
    s.add_argument("--out-dir", default=None)
    s.set_defaults(func=cmd_analyze)

    s = sub.add_parser("all", help="Run generate -> infer -> analyze")
    s.add_argument("--prompts-file", required=True)
    s.add_argument("--runs-per-prompt", type=int, default=100)
    s.add_argument("--generation-batch-size", type=int, default=10)
    s.add_argument("--generation-temperature", type=float, default=1.3)
    s.add_argument("--generation-interval", type=float, default=0.0)
    s.add_argument("--deepseek-model", default=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"))
    s.add_argument("--system-prompt", default=None)
    s.add_argument("--ollama-model", default=os.getenv("OLLAMA_MODEL", "gpt-oss:20b"))
    s.add_argument("--inference-interval", type=float, default=0.0)
    s.add_argument("--out-dir", default=None)
    s.set_defaults(func=cmd_all)

    return p


def main(argv: List[str] = None) -> None:
    p = build_parser()
    args = p.parse_args(argv)
    if not hasattr(args, "func"):
        p.print_help()
        return
    args.func(args)


if __name__ == "__main__":
    main()
