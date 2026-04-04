#!/usr/bin/env python3

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import build_site


ROOT = Path(__file__).resolve().parents[1]
CONTENT_DIR = ROOT / "content"
DIST_DIR = ROOT / "dist"

QUESTION_RE = re.compile(r"^(\d+)\.\s+(.+)$")
OPTION_RE = re.compile(r"^-\s+(.+)$")
BOLD_QUESTION_RE = re.compile(r"^\*\*(\d+)\.\s+(.+?)\*\*$")
NAMED_QUESTION_RE = re.compile(r"^\*\*Question\s+(\d+):\*\*\s*(.+)$", flags=re.I)


@dataclass
class QuizQuestion:
    number: int
    prompt: str
    options: list[str] = field(default_factory=list)


@dataclass
class QuizIssue:
    code: str
    message: str


@dataclass
class QuizReport:
    path: Path
    route_path: Path
    chapter_id: str
    title: str
    question_count: int = 0
    issues: list[QuizIssue] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.issues


def normalize_answer(text: str) -> str:
    return re.sub(r"[.,;:!?]+$", "", text.strip().lower())


def find_section_lines(body: str, heading: str) -> tuple[list[str] | None, int]:
    lines = body.splitlines()
    target = heading.strip().lower()
    heading_indexes = [
        index
        for index, line in enumerate(lines)
        if re.match(rf"^##\s+{re.escape(heading)}\s*$", line.strip(), flags=re.I)
    ]

    if not heading_indexes:
        return None, 0

    start = heading_indexes[0] + 1
    end = len(lines)
    for index in range(start, len(lines)):
        if re.match(r"^##\s+.+$", lines[index].strip()):
            end = index
            break

    return lines[start:end], len(heading_indexes)


def parse_answer_block(lines: list[str]) -> tuple[bool, list[str]]:
    answers: list[str] = []
    saw_numbered_answers = False

    for raw_line in lines:
        stripped = raw_line.strip()
        if not stripped:
            continue
        if stripped.startswith("<summary>") and stripped.endswith("</summary>"):
            continue

        match = QUESTION_RE.match(stripped)
        if match:
            saw_numbered_answers = True
            answers.append(match.group(2).strip())

    return saw_numbered_answers, answers


def parse_quiz_section(lines: list[str], issues: list[QuizIssue]) -> tuple[list[QuizQuestion], list[str]]:
    questions: list[QuizQuestion] = []
    detail_blocks: list[list[str]] = []
    current_detail_lines: list[str] = []
    in_details = False
    uses_legacy_question_format = False
    saw_orphan_options = False

    for raw_line in lines:
        stripped = raw_line.strip()
        if not stripped:
            continue

        if stripped == "<details>":
            if in_details:
                issues.append(
                    QuizIssue("nested-details", "Quiz answer key contains nested <details> blocks.")
                )
            in_details = True
            current_detail_lines = []
            continue

        if stripped == "</details>":
            if not in_details:
                issues.append(
                    QuizIssue("orphan-details-close", "Quiz section closes </details> before it opens.")
                )
            else:
                detail_blocks.append(current_detail_lines)
            in_details = False
            continue

        if in_details:
            current_detail_lines.append(raw_line)
            continue

        named_question_match = NAMED_QUESTION_RE.match(stripped)
        if named_question_match:
            uses_legacy_question_format = True
            questions.append(
                QuizQuestion(
                    number=int(named_question_match.group(1)),
                    prompt=named_question_match.group(2).strip(),
                )
            )
            continue

        bold_question_match = BOLD_QUESTION_RE.match(stripped)
        if bold_question_match:
            uses_legacy_question_format = True
            questions.append(
                QuizQuestion(
                    number=int(bold_question_match.group(1)),
                    prompt=bold_question_match.group(2).strip(),
                )
            )
            continue

        question_match = QUESTION_RE.match(stripped)
        if question_match:
            questions.append(
                QuizQuestion(
                    number=int(question_match.group(1)),
                    prompt=question_match.group(2).strip(),
                )
            )
            continue

        option_match = OPTION_RE.match(stripped)
        if option_match:
            if not questions:
                saw_orphan_options = True
                continue
            questions[-1].options.append(option_match.group(1).strip())

    if in_details:
        issues.append(
            QuizIssue("unclosed-details", "Quiz answer key <details> block is not closed.")
        )

    if uses_legacy_question_format or (saw_orphan_options and not questions):
        issues.append(
            QuizIssue(
                "legacy-question-format",
                "Quiz questions are not written as ordered-list items, so the interactive quiz script cannot parse them.",
            )
        )

    if len(detail_blocks) > 1:
        issues.append(
            QuizIssue(
                "legacy-answer-key-format",
                "Quiz uses multiple per-question <details> blocks, but the interactive quiz script expects one shared answer-key block.",
            )
        )
        return questions, []

    if not detail_blocks:
        return questions, []

    saw_numbered_answers, answers = parse_answer_block(detail_blocks[0])
    if not saw_numbered_answers:
        issues.append(
            QuizIssue(
                "answer-key-format",
                "Quiz answer key is missing a numbered answer list, so the interactive quiz script cannot match answers to questions.",
            )
        )
        return questions, []

    return questions, answers


def validate_question_numbering(
    label: str, values: list[int], issues: list[QuizIssue], code: str
) -> None:
    if not values:
        return

    expected = list(range(1, len(values) + 1))
    if values != expected:
        issues.append(
            QuizIssue(
                code,
                f"{label} numbering should be sequential starting at 1, found {values}.",
            )
        )


def inspect_rendered_quiz(body: str, issues: list[QuizIssue]) -> None:
    rendered = build_site.wrap_sections(build_site.render_markdown(body))
    quiz_section_count = rendered.count('lesson-section lesson-section--quiz')
    if quiz_section_count == 0:
        issues.append(
            QuizIssue(
                "rendered-quiz-section-missing",
                "Rendered chapter HTML does not contain a quiz section.",
            )
        )
        return

    if quiz_section_count > 1:
        issues.append(
            QuizIssue(
                "rendered-quiz-section-duplicate",
                f"Rendered chapter HTML contains {quiz_section_count} quiz sections.",
            )
        )


def inspect_dist_output(route_path: Path, issues: list[QuizIssue]) -> None:
    html_path = DIST_DIR / route_path / "index.html"
    if not html_path.exists():
        issues.append(
            QuizIssue("dist-page-missing", f"Built chapter page is missing: {html_path}")
        )
        return

    html = html_path.read_text(encoding="utf-8")
    if 'lesson-section lesson-section--quiz' not in html:
        issues.append(
            QuizIssue(
                "dist-quiz-section-missing",
                "Built chapter page does not include the quiz section wrapper.",
            )
        )
    if "Interactive Quiz" not in html or "Check my answers" not in html:
        issues.append(
            QuizIssue(
                "dist-quiz-script-missing",
                "Built chapter page does not include the interactive quiz script/button markup.",
            )
        )


def check_chapter(path: Path, check_dist: bool) -> QuizReport:
    metadata, body = build_site.parse_document(path.read_text(encoding="utf-8"))
    chapter_id = str(metadata.get("id", path.stem))
    title = str(metadata.get("title", path.stem))
    route_path = path.relative_to(CONTENT_DIR).with_suffix("")
    issues: list[QuizIssue] = []

    sanitized_body = build_site.drop_duplicate_title(body, metadata.get("title"))
    publishable_body = build_site.strip_hidden_sections(sanitized_body)
    quiz_lines, quiz_heading_count = find_section_lines(publishable_body, "Unlock Quiz")

    if quiz_heading_count == 0 or quiz_lines is None:
        issues.append(
            QuizIssue("missing-quiz-section", 'Chapter is missing a "## Unlock Quiz" section.')
        )
        return QuizReport(path=path, route_path=route_path, chapter_id=chapter_id, title=title, issues=issues)

    if quiz_heading_count > 1:
        issues.append(
            QuizIssue(
                "duplicate-quiz-sections",
                f'Chapter contains {quiz_heading_count} "## Unlock Quiz" sections.',
            )
        )

    questions, answers = parse_quiz_section(quiz_lines, issues)

    if not questions:
        issues.append(
            QuizIssue("missing-quiz-questions", "Quiz section does not contain any numbered questions.")
        )

    if not answers and not any(
        issue.code in {"legacy-answer-key-format", "answer-key-format"}
        for issue in issues
    ):
        issues.append(
            QuizIssue("missing-answer-key", "Quiz section does not contain an answer key inside <details>.")
        )

    validate_question_numbering(
        "Question",
        [question.number for question in questions],
        issues,
        "question-numbering",
    )

    for question in questions:
        if not question.prompt:
            issues.append(
                QuizIssue(
                    "empty-question",
                    f"Question {question.number} is missing its prompt text.",
                )
            )
        if len(question.options) < 2:
            issues.append(
                QuizIssue(
                    "too-few-options",
                    f"Question {question.number} should have at least 2 answer options, found {len(question.options)}.",
                )
            )

    if questions and answers and len(questions) != len(answers):
        issues.append(
            QuizIssue(
                "question-answer-count-mismatch",
                f"Quiz has {len(questions)} question(s) but {len(answers)} answer(s) in the answer key.",
            )
        )

    for index, answer in enumerate(answers, start=1):
        if index > len(questions):
            break
        question = questions[index - 1]
        normalized_options = [normalize_answer(option) for option in question.options]
        normalized_answer = normalize_answer(answer)
        if normalized_answer not in normalized_options:
            issues.append(
                QuizIssue(
                    "answer-not-in-options",
                    f'Answer {index} does not match any option for question {question.number}: "{answer}".',
                )
            )

    inspect_rendered_quiz(publishable_body, issues)

    if check_dist:
        inspect_dist_output(route_path, issues)

    return QuizReport(
        path=path,
        route_path=route_path,
        chapter_id=chapter_id,
        title=title,
        question_count=len(questions),
        issues=issues,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate that every chapter quiz is present and matches the site quiz runtime expectations."
    )
    parser.add_argument(
        "--check-dist",
        action="store_true",
        help="Also verify that built dist chapter pages contain quiz markup.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    chapter_paths = sorted(CONTENT_DIR.rglob("ch-*.mdx"))

    if not chapter_paths:
        print(f"No chapter files found under {CONTENT_DIR}", file=sys.stderr)
        return 1

    reports = [check_chapter(path, check_dist=args.check_dist) for path in chapter_paths]
    failed_reports = [report for report in reports if not report.ok]
    total_questions = sum(report.question_count for report in reports)
    total_issues = sum(len(report.issues) for report in failed_reports)

    if failed_reports:
        print(
            f"FAIL: {len(failed_reports)} chapter(s) have quiz issues "
            f"({total_issues} issue(s) across {len(reports)} chapter(s), {total_questions} question(s) checked)."
        )
        for report in failed_reports:
            relative_path = report.path.relative_to(ROOT)
            print(f"\n{relative_path} [{report.chapter_id}] {report.title}")
            for issue in report.issues:
                print(f"  - [{issue.code}] {issue.message}")
        return 1

    dist_suffix = " with dist validation" if args.check_dist else ""
    print(
        f"PASS: validated {len(reports)} chapter quiz(es){dist_suffix} "
        f"covering {total_questions} question(s)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
