import json
import os
import re
from pathlib import Path

from gpt_oss_redteam.utils import (
    ensure_dir,
    new_run_dir,
    write_jsonl,
    write_text,
    read_prompts_file,
)


def test_ensure_dir_creates_directory(tmp_path):
    d = tmp_path / "mydir" / "nested"
    created = ensure_dir(str(d))
    assert created == str(d)
    assert d.is_dir()


def test_new_run_dir_under_custom_base(tmp_path):
    run_dir = new_run_dir(str(tmp_path))
    p = Path(run_dir)
    assert p.is_dir()
    assert p.parent == tmp_path
    assert re.match(r"\d{8}_\d{6}", p.name)


def test_write_jsonl_appends(tmp_path):
    f = tmp_path / "data.jsonl"
    write_jsonl(str(f), [{"a": 1}, {"b": 2}])
    write_jsonl(str(f), [{"c": 3}])

    lines = f.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 3
    objs = [json.loads(x) for x in lines]
    assert objs == [{"a": 1}, {"b": 2}, {"c": 3}]


def test_write_text_and_read_prompts_file(tmp_path):
    f = tmp_path / "prompts.txt"
    content = " first \n\nsecond\n third  \n  \n"
    write_text(str(f), content)

    prompts = read_prompts_file(str(f))
    assert prompts == ["first", "second", "third"]
