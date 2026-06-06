#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import re
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
TSV_PATH = BASE_DIR.parent / "richard_translation.tsv"
DATA_PATH = BASE_DIR / "data.json"
SPEAKER_RE = re.compile(r"^\s*([^:：]{1,80}?)\s*[:：]\s*(.+?)\s*$")


def split_speaker(text: str) -> tuple[str, str]:
    match = SPEAKER_RE.match(text or "")
    if not match or text.rstrip().endswith(":"):
        return "", text or ""
    speaker, spoken_text = match.groups()
    return speaker.strip(), spoken_text.strip()


def remove_matching_speaker(text: str, speaker: str) -> str:
    if not speaker:
        return text or ""
    _, spoken_text = split_speaker(text or "")
    return spoken_text


def row_kind(french_text: str, speaker: str) -> str:
    if speaker:
        return "dialogue"
    if re.match(r"^\d+\s*[–-]\s+", french_text):
        return "section"
    if french_text.isupper() and len(french_text) <= 40:
        return "title"
    return "stage"


def main() -> None:
    with TSV_PATH.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))

    lines = []
    for index, row in enumerate(rows, start=1):
        speaker, french_text = split_speaker(row["french"])
        lines.append(
            {
                "id": index,
                "speaker": speaker,
                "french": french_text,
                "russian": remove_matching_speaker(row["russian"], speaker),
                "note": row["notes"].strip(),
                "kind": row_kind(french_text, speaker),
            }
        )

    DATA_PATH.write_text(
        json.dumps({"title": "RICHARD", "lines": lines}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Wrote {DATA_PATH} ({len(lines)} lines)")


if __name__ == "__main__":
    main()
