#!/usr/bin/env python3

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTENT_DIR = ROOT / "content"

STANDARD_QUESTION_RE = re.compile(r"^(\d+)\.\s+(.+)$")
LEGACY_BOLD_NUMBER_RE = re.compile(r"^\*\*(\d+)\.\s*(.*?)\*\*(.*)$")
LEGACY_NAMED_RE = re.compile(r"^\*\*Question\s+(\d+):\*\*\s*(.+)$", flags=re.I)
LEGACY_Q_RE = re.compile(r"^\*\*Q(\d+):\s*(.*?)\*\*(.*)$", flags=re.I)
OPTION_RE = re.compile(r"^-\s+(.+)$")


@dataclass
class Question:
    number: int
    prompt: str
    options: list[str] = field(default_factory=list)
    answer_block: list[str] = field(default_factory=list)


def strip_frontmatter(text: str) -> tuple[str, str, str]:
    if not text.startswith("---\n"):
        return "", text, ""
    _, remainder = text.split("---\n", 1)
    frontmatter, body = remainder.split("\n---\n", 1)
    return "---\n" + frontmatter + "\n---\n", body, ""


def find_unlock_quiz_bounds(body: str) -> tuple[int, int] | None:
    match = re.search(r"^## Unlock Quiz\s*$", body, flags=re.M)
    if not match:
        return None
    start = match.start()
    next_heading = re.search(r"^##\s+.+$", body[match.end():], flags=re.M)
    end = match.end() + next_heading.start() if next_heading else len(body)
    return start, end


def parse_question_line(stripped: str) -> tuple[int, str] | None:
    for pattern in (STANDARD_QUESTION_RE, LEGACY_NAMED_RE):
        match = pattern.match(stripped)
        if match:
            return int(match.group(1)), match.group(2).strip()

    match = LEGACY_BOLD_NUMBER_RE.match(stripped)
    if match:
        prompt = (match.group(2) + match.group(3)).strip()
        return int(match.group(1)), prompt

    match = LEGACY_Q_RE.match(stripped)
    if match:
        prompt = (match.group(2) + match.group(3)).strip()
        return int(match.group(1)), prompt

    return None


def clean_markdown(text: str) -> str:
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"\*(.*?)\*", r"\1", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = text.replace("\\$", "$")
    text = text.replace("$", "")
    text = text.replace("\\", "")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def normalize(text: str) -> str:
    text = clean_markdown(text)
    text = text.replace("—", "-")
    text = re.sub(r"\s+", " ", text).strip().lower()
    text = re.sub(r"[.,;:!?]+$", "", text)
    return text


def first_nonempty_content(lines: list[str]) -> str:
    parts: list[str] = []
    for raw_line in lines:
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("<summary>"):
            continue
        parts.append(stripped)
    return " ".join(parts).strip()


def split_shared_answers(lines: list[str]) -> list[str]:
    answers: list[str] = []
    for raw_line in lines:
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("<summary>"):
            continue
        match = STANDARD_QUESTION_RE.match(stripped)
        if match:
            answers.append(match.group(2).strip())
    return answers


def extract_candidate_answer_text(raw_answer: str) -> list[str]:
    cleaned = clean_markdown(raw_answer)
    candidates = [raw_answer.strip(), cleaned]

    bold_label_match = re.match(r"^\*\*[A-D]\s*[-:]\s*(.*?)\.\*\*", raw_answer)
    if bold_label_match:
        candidates.append(bold_label_match.group(1).strip())

    bold_value_match = re.match(r"^\*\*(.*?)\*\*\s*[-:]", raw_answer)
    if bold_value_match:
        candidates.append(bold_value_match.group(1).strip())

    plain_label_match = re.match(r"^[A-D]\s*[-:]\s*(.+)$", clean_markdown(raw_answer))
    if plain_label_match:
        candidates.append(plain_label_match.group(1).strip())

    dash_parts = re.split(r"\s[-:]\s", clean_markdown(raw_answer), maxsplit=1)
    if dash_parts:
        candidates.append(dash_parts[0].strip())

    quoted_match = re.search(r'The answer is ["“](.+?)["”]', cleaned, flags=re.I)
    if quoted_match:
        candidates.append(quoted_match.group(1).strip())

    simple_answer_match = re.search(r"The answer is (.+)$", cleaned, flags=re.I)
    if simple_answer_match:
        candidates.append(simple_answer_match.group(1).strip().rstrip("."))

    seen: list[str] = []
    for candidate in candidates:
        candidate = candidate.strip()
        if candidate and candidate not in seen:
            seen.append(candidate)
    return seen


def map_answer_to_option(raw_answer: str, options: list[str]) -> str | None:
    option_norms = [normalize(option) for option in options]
    cleaned = clean_markdown(raw_answer).lower()

    ordinal_lookup = {
        "first": 0,
        "second": 1,
        "third": 2,
        "fourth": 3,
    }

    ordinal_match = re.search(r"\b(first|second|third|fourth)\s+option\b", cleaned)
    if ordinal_match:
        index = ordinal_lookup[ordinal_match.group(1)]
        if index < len(options):
            return options[index]

    for candidate in extract_candidate_answer_text(raw_answer):
        candidate_norm = normalize(candidate)
        for option, option_norm in zip(options, option_norms):
            if candidate_norm == option_norm:
                return option

    answer_norm = normalize(raw_answer)
    contained = [
        option for option, option_norm in zip(options, option_norms) if option_norm and option_norm in answer_norm
    ]
    if len(contained) == 1:
        return contained[0]

    prefix_matches = [
        option
        for option, option_norm in zip(options, option_norms)
        if option_norm and (answer_norm.startswith(option_norm) or option_norm.startswith(answer_norm))
    ]
    if len(prefix_matches) == 1:
        return prefix_matches[0]

    return None


def parse_legacy_quiz(section_body: str) -> tuple[list[Question], list[str], bool]:
    questions: list[Question] = []
    shared_answer_block: list[str] = []
    current_question: Question | None = None
    in_details = False
    detail_lines: list[str] = []
    saw_legacy_shape = False

    for raw_line in section_body.splitlines():
        stripped = raw_line.strip()

        if not stripped or stripped == "---":
            continue

        if stripped == "<details>":
            in_details = True
            detail_lines = []
            continue

        if stripped == "</details>":
            in_details = False
            if current_question is not None and not shared_answer_block:
                numbered_answers = split_shared_answers(detail_lines)
                if numbered_answers:
                    shared_answer_block = detail_lines[:]
                else:
                    current_question.answer_block = detail_lines[:]
            continue

        if in_details:
            detail_lines.append(raw_line)
            continue

        question = parse_question_line(stripped)
        if question:
            number, prompt = question
            if not STANDARD_QUESTION_RE.match(stripped):
                saw_legacy_shape = True
            current_question = Question(number=number, prompt=prompt)
            questions.append(current_question)
            continue

        option_match = OPTION_RE.match(stripped)
        if option_match and current_question is not None:
            current_question.options.append(option_match.group(1).strip())
            continue

    if any(question.answer_block for question in questions):
        saw_legacy_shape = True
    if shared_answer_block and "<summary>Unlock Quiz Answers</summary>" not in shared_answer_block:
        saw_legacy_shape = True

    return questions, shared_answer_block, saw_legacy_shape


def build_replacement_section(questions: list[Question], answers: list[str]) -> str:
    lines = ["## Unlock Quiz", ""]
    for index, question in enumerate(questions, start=1):
        lines.append(f"{index}. {question.prompt}")
        for option in question.options:
            lines.append(f"   - {option}")
        if index != len(questions):
            lines.append("")

    lines.extend(["", "<details>", "<summary>Unlock Quiz Answers</summary>", ""])
    for index, answer in enumerate(answers, start=1):
        lines.append(f"{index}. {answer}")
    lines.extend(["", "</details>", ""])
    return "\n".join(lines)


def migrate_file(path: Path) -> tuple[bool, str | None]:
    text = path.read_text(encoding="utf-8")
    bounds = find_unlock_quiz_bounds(text)
    if bounds is None:
        return False, None

    start, end = bounds
    section = text[start:end]
    header, _, body = section.partition("\n")
    questions, shared_answer_block, saw_legacy_shape = parse_legacy_quiz(body)

    if not saw_legacy_shape:
        return False, None

    if not questions:
        return False, "could not parse any quiz questions"

    raw_answers: list[str]
    if shared_answer_block:
        raw_answers = split_shared_answers(shared_answer_block)
    else:
        raw_answers = [first_nonempty_content(question.answer_block) for question in questions]

    if len(raw_answers) != len(questions):
        return False, f"found {len(questions)} question(s) but {len(raw_answers)} answer block(s)"

    mapped_answers: list[str] = []
    for question, raw_answer in zip(questions, raw_answers):
        mapped = map_answer_to_option(raw_answer, question.options)
        if mapped is None:
            return False, f"could not map answer for question {question.number}: {raw_answer}"
        mapped_answers.append(mapped)

    replacement = build_replacement_section(questions, mapped_answers)
    updated = text[:start] + replacement + text[end:]
    path.write_text(updated, encoding="utf-8")
    return True, None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert legacy quiz sections to the current Math Journey quiz format.")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Report which files would be migrated without writing changes.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    changed = 0
    errors: list[tuple[Path, str]] = []

    for path in sorted(CONTENT_DIR.rglob("ch-*.mdx")):
        if args.check:
            text = path.read_text(encoding="utf-8")
            bounds = find_unlock_quiz_bounds(text)
            if bounds is None:
                continue
            start, end = bounds
            _, _, body = text[start:end].partition("\n")
            _, _, saw_legacy_shape = parse_legacy_quiz(body)
            if saw_legacy_shape:
                print(path.relative_to(ROOT))
                changed += 1
            continue

        updated, error = migrate_file(path)
        if error is not None:
            errors.append((path, error))
            continue
        if updated:
            print(f"migrated {path.relative_to(ROOT)}")
            changed += 1

    if errors:
        print("\nMigration stopped with unresolved quiz mappings:", file=sys.stderr)
        for path, error in errors:
            print(f"- {path.relative_to(ROOT)}: {error}", file=sys.stderr)
        return 1

    if args.check:
        print(f"\n{changed} file(s) need migration.")
    else:
        print(f"\nMigrated {changed} file(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
