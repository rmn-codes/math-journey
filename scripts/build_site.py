#!/usr/bin/env python3

from __future__ import annotations

from dataclasses import dataclass
from html import escape
from pathlib import Path
import re
import shutil


ROOT = Path(__file__).resolve().parents[1]
CONTENT_DIR = ROOT / "content"
DIST_DIR = ROOT / "dist"
STYLE_SOURCE = ROOT / "src" / "styles" / "site.css"
STYLE_OUT = DIST_DIR / "assets" / "site.css"


@dataclass
class Chapter:
    source_path: Path
    route_path: Path
    metadata: dict
    toc: list[tuple[int, str, str]]
    rendered_body: str

    @property
    def title(self) -> str:
        return str(self.metadata.get("title", self.source_path.stem))

    @property
    def subtitle(self) -> str:
        return str(self.metadata.get("subtitle", "")).strip()

    @property
    def description(self) -> str:
        subtitle = self.subtitle
        if subtitle:
            return subtitle
        objectives = self.metadata.get("learningObjectives", [])
        if objectives:
            return str(objectives[0])
        return "Story-driven mathematics lesson"


def main() -> None:
    chapters = load_chapters()
    build_site(chapters)
    print(f"Built {len(chapters)} chapter page(s) into {DIST_DIR}")


def load_chapters() -> list[Chapter]:
    chapters: list[Chapter] = []
    for path in sorted(CONTENT_DIR.rglob("ch-*.mdx")):
        metadata, body = parse_document(path.read_text(encoding="utf-8"))
        sanitized_body = drop_duplicate_title(body, metadata.get("title"))
        toc = extract_toc(sanitized_body)
        route = path.relative_to(CONTENT_DIR).with_suffix("")
        chapters.append(
            Chapter(
                source_path=path,
                route_path=route,
                metadata=metadata,
                toc=toc,
                rendered_body=render_markdown(sanitized_body),
            )
        )

    chapters.sort(
        key=lambda chapter: (
            int(chapter.metadata.get("worldNumber", 999)),
            int(chapter.metadata.get("chapterNumber", 999)),
            chapter.title.lower(),
        )
    )
    return chapters


def parse_document(text: str) -> tuple[dict, str]:
    if not text.startswith("---\n"):
        return {}, text

    _, remainder = text.split("---\n", 1)
    frontmatter, body = remainder.split("\n---\n", 1)
    return parse_frontmatter(frontmatter), body.strip() + "\n"


def parse_frontmatter(frontmatter: str) -> dict:
    lines = frontmatter.splitlines()
    parsed, next_index = parse_yaml_block(lines, 0, 0, dict)
    if next_index != len(lines):
        raise ValueError("Failed to parse full frontmatter block")
    return parsed


def parse_yaml_block(
    lines: list[str], start_index: int, indent: int, container_type: type
) -> tuple[dict | list, int]:
    container = {} if container_type is dict else []
    index = start_index

    while index < len(lines):
        raw_line = lines[index]
        if not raw_line.strip():
            index += 1
            continue

        current_indent = count_indent(raw_line)
        if current_indent < indent:
            break
        if current_indent > indent:
            raise ValueError(f"Unexpected indentation on line: {raw_line}")

        stripped = raw_line.strip()

        if isinstance(container, list):
            if not stripped.startswith("- "):
                break
            container.append(parse_scalar(stripped[2:].strip()))
            index += 1
            continue

        key, sep, rest = stripped.partition(":")
        if not sep:
            raise ValueError(f"Invalid frontmatter line: {raw_line}")

        if rest.strip():
            container[key] = parse_scalar(rest.strip())
            index += 1
            continue

        next_index = index + 1
        while next_index < len(lines) and not lines[next_index].strip():
            next_index += 1

        if next_index >= len(lines) or count_indent(lines[next_index]) <= indent:
            container[key] = {}
            index = next_index
            continue

        child_indent = count_indent(lines[next_index])
        child_type = list if lines[next_index].strip().startswith("- ") else dict
        child, index = parse_yaml_block(lines, next_index, child_indent, child_type)
        container[key] = child

    return container, index


def parse_scalar(value: str):
    if value == "true":
        return True
    if value == "false":
        return False
    if re.fullmatch(r"-?\d+", value):
        return int(value)
    if re.fullmatch(r"-?\d+\.\d+", value):
        return float(value)
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [parse_scalar(part.strip()) for part in inner.split(",")]
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    return value


def count_indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def drop_duplicate_title(body: str, title: object) -> str:
    if not title:
        return body

    lines = body.splitlines()
    while lines and not lines[0].strip():
        lines.pop(0)
    if lines and lines[0].strip() == f"# {title}":
        lines.pop(0)
        while lines and not lines[0].strip():
            lines.pop(0)
    return "\n".join(lines)


def extract_toc(body: str) -> list[tuple[int, str, str]]:
    toc: list[tuple[int, str, str]] = []
    for line in body.splitlines():
        match = re.match(r"^(#{2,3})\s+(.+)$", line.strip())
        if not match:
            continue
        label = match.group(2).strip()
        toc.append((len(match.group(1)), label, slugify(label)))
    return toc


def render_markdown(markdown: str) -> str:
    lines = markdown.splitlines()
    html_parts: list[str] = []
    paragraph_lines: list[str] = []
    list_type: str | None = None
    list_items: list[str] = []

    def flush_paragraph() -> None:
        nonlocal paragraph_lines
        if not paragraph_lines:
            return
        text = " ".join(part.strip() for part in paragraph_lines if part.strip())
        html_parts.append(f"<p>{render_inline(text)}</p>")
        paragraph_lines = []

    def flush_list() -> None:
        nonlocal list_type, list_items
        if not list_type or not list_items:
            list_type = None
            list_items = []
            return
        inner = "".join(f"<li>{render_inline(item)}</li>" for item in list_items)
        html_parts.append(f"<{list_type}>{inner}</{list_type}>")
        list_type = None
        list_items = []

    in_code_block = False
    code_lines: list[str] = []

    for raw_line in lines:
        line = raw_line.rstrip()
        stripped = line.strip()

        if in_code_block:
            if stripped.startswith("```"):
                html_parts.append(
                    "<pre><code>"
                    + escape("\n".join(code_lines))
                    + "</code></pre>"
                )
                code_lines = []
                in_code_block = False
            else:
                code_lines.append(raw_line)
            continue

        if stripped.startswith("```"):
            flush_paragraph()
            flush_list()
            in_code_block = True
            code_lines = []
            continue

        if not stripped:
            flush_paragraph()
            flush_list()
            continue

        if re.match(r"^</?(details|summary)\b", stripped):
            flush_paragraph()
            flush_list()
            html_parts.append(stripped)
            continue

        heading_match = re.match(r"^(#{1,6})\s+(.+)$", stripped)
        if heading_match:
            flush_paragraph()
            flush_list()
            level = len(heading_match.group(1))
            label = heading_match.group(2).strip()
            html_parts.append(
                f'<h{level} id="{slugify(label)}">{render_inline(label)}</h{level}>'
            )
            continue

        ordered_match = re.match(r"^\d+\.\s+(.+)$", stripped)
        if ordered_match:
            flush_paragraph()
            item_text = ordered_match.group(1).strip()
            if list_type != "ol":
                flush_list()
                list_type = "ol"
            list_items.append(item_text)
            continue

        unordered_match = re.match(r"^-\s+(.+)$", stripped)
        if unordered_match:
            flush_paragraph()
            item_text = unordered_match.group(1).strip()
            if list_type != "ul":
                flush_list()
                list_type = "ul"
            list_items.append(item_text)
            continue

        paragraph_lines.append(stripped)

    flush_paragraph()
    flush_list()
    return "\n".join(html_parts)


def render_inline(text: str) -> str:
    rendered = escape(text)
    rendered = re.sub(r"`([^`]+)`", r"<code>\1</code>", rendered)
    rendered = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", rendered)
    rendered = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", rendered)
    return rendered


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or "section"


def build_site(chapters: list[Chapter]) -> None:
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)

    (DIST_DIR / "assets").mkdir(parents=True, exist_ok=True)
    shutil.copy2(STYLE_SOURCE, STYLE_OUT)

    index_html = render_index(chapters)
    (DIST_DIR / "index.html").write_text(index_html, encoding="utf-8")

    for chapter in chapters:
        output_dir = DIST_DIR / chapter.route_path
        output_dir.mkdir(parents=True, exist_ok=True)
        output_dir.joinpath("index.html").write_text(
            render_chapter(chapter, chapters), encoding="utf-8"
        )


def render_index(chapters: list[Chapter]) -> str:
    cards = []
    for chapter in chapters:
        objectives = chapter.metadata.get("learningObjectives", [])
        objective_html = (
            "".join(f"<li>{escape(str(item))}</li>" for item in objectives[:2])
            if objectives
            else "<li>Foundational lesson</li>"
        )
        cards.append(
            f"""
            <article class="chapter-card">
              <p class="eyebrow">World {chapter.metadata.get('worldNumber', '?')} · Chapter {chapter.metadata.get('chapterNumber', '?')}</p>
              <h2><a href="{chapter.route_path.as_posix()}/">{escape(chapter.title)}</a></h2>
              <p class="lede">{escape(chapter.description)}</p>
              <ul class="mini-list">{objective_html}</ul>
              <div class="card-meta">
                <span>{escape(str(chapter.metadata.get('estimatedTimeMinutes', '?')))} min</span>
                <span>{escape(str(chapter.metadata.get('level', 'core')))}</span>
              </div>
            </article>
            """
        )

    body = f"""
    <main class="page-shell home-shell">
      <section class="hero-panel">
        <p class="eyebrow">Math Journey</p>
        <h1>A first content-rendering pipeline</h1>
        <p class="hero-copy">
          This static build reads chapter source files from <code>content/</code>,
          parses frontmatter, renders lesson content, and outputs a browsable site
          into <code>dist/</code>.
        </p>
      </section>

      <section class="section-block">
        <div class="section-heading">
          <p class="eyebrow">Available Lessons</p>
          <h2>Current chapters</h2>
        </div>
        <div class="card-grid">
          {''.join(cards)}
        </div>
      </section>
    </main>
    """
    return render_document("Math Journey", "First content pipeline", body)


def render_chapter(chapter: Chapter, chapters: list[Chapter]) -> str:
    previous_chapter, next_chapter = chapter_neighbors(chapter, chapters)
    objectives = "".join(
        f"<li>{escape(str(item))}</li>"
        for item in chapter.metadata.get("learningObjectives", [])
    )
    toc_items = "".join(
        f'<li class="toc-level-{level}"><a href="#{anchor}">{escape(label)}</a></li>'
        for level, label, anchor in chapter.toc
    )

    navigation = []
    if previous_chapter:
        navigation.append(
            f'<a class="pager-link" href="/{previous_chapter.route_path.as_posix()}/">Previous: {escape(previous_chapter.title)}</a>'
        )
    if next_chapter:
        navigation.append(
            f'<a class="pager-link" href="/{next_chapter.route_path.as_posix()}/">Next: {escape(next_chapter.title)}</a>'
        )

    regions = ", ".join(str(item) for item in chapter.metadata.get("historicalRegions", []))
    body = f"""
    <main class="page-shell chapter-shell">
      <a class="back-link" href="/">Back to index</a>

      <section class="hero-panel chapter-hero">
        <p class="eyebrow">World {escape(str(chapter.metadata.get('worldNumber', '?')))} · Chapter {escape(str(chapter.metadata.get('chapterNumber', '?')))}</p>
        <h1>{escape(chapter.title)}</h1>
        <p class="hero-copy">{escape(chapter.description)}</p>
        <div class="hero-meta">
          <span>{escape(str(chapter.metadata.get('estimatedTimeMinutes', '?')))} min</span>
          <span>{escape(str(chapter.metadata.get('level', 'core')))}</span>
          <span>{escape(regions)}</span>
        </div>
      </section>

      <div class="content-grid">
        <aside class="chapter-sidebar">
          <section class="sidebar-card">
            <p class="eyebrow">Objectives</p>
            <ul>{objectives}</ul>
          </section>
          <section class="sidebar-card">
            <p class="eyebrow">On This Page</p>
            <ul class="toc-list">{toc_items}</ul>
          </section>
        </aside>

        <article class="chapter-article">
          {chapter.rendered_body}
        </article>
      </div>

      <nav class="pager">{''.join(navigation)}</nav>
    </main>
    """
    return render_document(chapter.title, chapter.description, body)


def chapter_neighbors(chapter: Chapter, chapters: list[Chapter]) -> tuple[Chapter | None, Chapter | None]:
    index = chapters.index(chapter)
    previous_chapter = chapters[index - 1] if index > 0 else None
    next_chapter = chapters[index + 1] if index + 1 < len(chapters) else None
    return previous_chapter, next_chapter


def render_document(title: str, description: str, body: str) -> str:
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{escape(title)}</title>
    <meta name="description" content="{escape(description)}" />
    <link rel="stylesheet" href="/assets/site.css" />
  </head>
  <body>
    {body}
  </body>
</html>
"""


if __name__ == "__main__":
    main()
