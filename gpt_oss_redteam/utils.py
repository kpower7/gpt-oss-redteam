import json
import os
from datetime import datetime
from typing import Iterable, List


def ensure_dir(path: str) -> str:
    os.makedirs(path, exist_ok=True)
    return path


def new_run_dir(base_dir: str = "runs") -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = os.path.join(base_dir, ts)
    ensure_dir(run_dir)
    return run_dir


def write_jsonl(file_path: str, records: Iterable[dict]) -> None:
    with open(file_path, "a", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def write_text(file_path: str, text: str) -> None:
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(text)


def read_prompts_file(path: str) -> List[str]:
    prompts: List[str] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if s:
                prompts.append(s)
    return prompts
