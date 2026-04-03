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


# Maps H2 heading text (lowercase) to a CSS modifier class
SECTION_CLASS_MAP: dict[str, str] = {
    "story hook": "story",
    "why it matters": "motivation",
    "historical context": "historical",
    "core concept": "concept",
    "definitions and formal lesson": "definitions",
    "worked examples": "examples",
    "practice set": "practice",
    "reasoning task": "reasoning",
    "application": "application",
    "recap": "recap",
    "unlock quiz": "quiz",
    "source notes": "sources",
}


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


def wrap_sections(html: str) -> str:
    """Post-process rendered HTML: wrap content between H2 headings in
    typed <section> elements so CSS can apply per-section visual treatments."""
    parts = re.split(r"(<h2\b[^>]*>.*?</h2>)", html)
    if len(parts) <= 1:
        return html

    result: list[str] = []

    # Content before the first H2 (introductory preamble, rare)
    if parts[0].strip():
        result.append(parts[0])

    i = 1
    while i < len(parts):
        h2_html = parts[i]
        content_html = parts[i + 1] if i + 1 < len(parts) else ""

        # Strip any inline HTML tags to get plain heading text for lookup
        heading_text = re.sub(r"<[^>]+>", "", h2_html).strip().lower()
        section_type = SECTION_CLASS_MAP.get(heading_text, "generic")

        result.append(
            f'<section class="lesson-section lesson-section--{section_type}">'
        )
        result.append(h2_html)
        result.append(content_html)
        result.append("</section>")

        i += 2

    return "".join(result)


def render_inline(text: str) -> str:
    # Extract markdown links before escaping, replace with placeholders
    links: list[tuple[str, str]] = []
    def _stash_link(m: re.Match) -> str:
        links.append((m.group(1), m.group(2)))
        return f"\x00LINK{len(links) - 1}\x00"
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", _stash_link, text)

    rendered = escape(text)
    rendered = re.sub(r"`([^`]+)`", r"<code>\1</code>", rendered)
    rendered = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", rendered)
    rendered = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", rendered)

    # Restore links
    for i, (label, href) in enumerate(links):
        rendered = rendered.replace(
            f"\x00LINK{i}\x00",
            f'<a href="{escape(href)}" target="_blank" rel="noopener">{escape(label)}</a>',
        )
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


def render_site_header(current_path: str = "/") -> str:
    home_active = ' aria-current="page"' if current_path == "/" else ""
    return f"""
    <header class="site-header">
      <div class="site-header-inner">
        <a class="site-logo" href="/" aria-label="Math Journey home">
          <span class="site-logo-mark">∑</span>
          <span class="site-logo-text">Math Journey</span>
        </a>
        <nav class="site-nav" aria-label="Site navigation">
          <a href="/"{ home_active}>Chapters</a>
        </nav>
      </div>
    </header>
    """


WORLD_TITLES: dict[int, str] = {
    0: "The Language of Number",
    1: "Shape, Measure, and the Greek Project",
    2: "Algebra Is Born",
    3: "Coordinate Space and Functions",
    4: "Trigonometry, Astronomy, and the Heavens",
    5: "Change, Motion, and Calculus",
    6: "Probability, Statistics, and Uncertainty",
    7: "Fields, Waves, Space-Time, and the Modern View",
}


def render_index(chapters: list[Chapter]) -> str:
    # Group chapters by world number
    worlds: dict[int, list[Chapter]] = {}
    for chapter in chapters:
        wn = int(chapter.metadata.get("worldNumber", 999))
        worlds.setdefault(wn, []).append(chapter)

    world_sections: list[str] = []
    for world_num in sorted(worlds):
        world_chapters = worlds[world_num]
        world_title = WORLD_TITLES.get(world_num, f"World {world_num:02d}")
        chapter_count = len(world_chapters)

        cards_html = []
        for chapter in world_chapters:
            objectives = chapter.metadata.get("learningObjectives", [])
            objective_html = (
                "".join(f"<li>{escape(str(item))}</li>" for item in objectives[:2])
                if objectives
                else "<li>Foundational lesson</li>"
            )
            cards_html.append(
                f"""
                <article class="chapter-card">
                  <p class="eyebrow">Ch. {chapter.metadata.get('chapterNumber', '?')}</p>
                  <h2><a href="/{chapter.route_path.as_posix()}/">{escape(chapter.title)}</a></h2>
                  <p class="lede">{escape(chapter.description)}</p>
                  <ul class="mini-list">{objective_html}</ul>
                  <div class="card-meta">
                    <span>{escape(str(chapter.metadata.get('estimatedTimeMinutes', '?')))} min</span>
                    <span>{escape(str(chapter.metadata.get('level', 'core')))}</span>
                  </div>
                </article>
                """
            )

        world_sections.append(f"""
        <section class="world-block">
          <div class="world-heading">
            <p class="eyebrow">World {world_num:02d}</p>
            <h2>{escape(world_title)}</h2>
            <p class="world-count">{chapter_count} chapter{"s" if chapter_count != 1 else ""}</p>
          </div>
          <div class="card-grid">
            {''.join(cards_html)}
          </div>
        </section>
        """)

    body = f"""
    {render_site_header("/")}
    <main class="page-shell home-shell">
      <section class="hero-panel">
        <p class="eyebrow">Math Journey</p>
        <h1>Mathematics as a human adventure</h1>
        <p class="hero-copy">
          From the first counting marks pressed into clay to the geometry of curved space-time —
          every idea in mathematics grew from a real human need. This is where that story unfolds.
        </p>
      </section>

      {''.join(world_sections)}
    </main>
    """
    return render_document("Math Journey", "Mathematics as a human adventure", body)


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

    navigation: list[str] = []
    if previous_chapter:
        navigation.append(
            f'<a class="pager-link pager-link--prev" href="/{previous_chapter.route_path.as_posix()}/">'
            f'<span class="pager-dir">← Previous</span>'
            f'<span class="pager-title">{escape(previous_chapter.title)}</span>'
            f"</a>"
        )
    if next_chapter:
        navigation.append(
            f'<a class="pager-link pager-link--next" href="/{next_chapter.route_path.as_posix()}/">'
            f'<span class="pager-dir">Next →</span>'
            f'<span class="pager-title">{escape(next_chapter.title)}</span>'
            f"</a>"
        )

    regions = ", ".join(str(item) for item in chapter.metadata.get("historicalRegions", []))
    period = escape(str(chapter.metadata.get("historicalPeriod", "")))

    # Wrap rendered body in typed sections
    sectioned_body = wrap_sections(chapter.rendered_body)

    body = f"""
    {render_site_header(f"/{chapter.route_path.as_posix()}/")}
    <div class="reading-progress" role="progressbar" aria-label="Reading progress">
      <div class="reading-progress-bar" id="js-progress"></div>
    </div>

    <main class="page-shell chapter-shell">
      <a class="back-link" href="/">← All chapters</a>

      <section class="hero-panel chapter-hero">
        <p class="eyebrow">World {escape(str(chapter.metadata.get('worldNumber', '?')))} · Chapter {escape(str(chapter.metadata.get('chapterNumber', '?')))}</p>
        <h1>{escape(chapter.title)}</h1>
        <p class="hero-copy">{escape(chapter.description)}</p>
        <div class="hero-meta">
          <span>{escape(str(chapter.metadata.get('estimatedTimeMinutes', '?')))} min</span>
          <span>{escape(str(chapter.metadata.get('level', 'core')))}</span>
          {f'<span>{escape(regions)}</span>' if regions else ''}
          {f'<span>{period}</span>' if period else ''}
        </div>
      </section>

      <div class="content-grid">
        <aside class="chapter-sidebar">
          <section class="sidebar-card">
            <p class="eyebrow">Objectives</p>
            <ul class="sidebar-list">{objectives}</ul>
          </section>
          <section class="sidebar-card">
            <p class="eyebrow">On This Page</p>
            <ul class="toc-list">{toc_items}</ul>
          </section>
        </aside>

        <article class="chapter-article">
          {sectioned_body}
        </article>
      </div>

      <nav class="pager">{''.join(navigation) or '<span></span>'}</nav>
    </main>
    """
    return render_document(chapter.title, chapter.description, body, is_chapter=True)


def chapter_neighbors(
    chapter: Chapter, chapters: list[Chapter]
) -> tuple[Chapter | None, Chapter | None]:
    index = chapters.index(chapter)
    previous_chapter = chapters[index - 1] if index > 0 else None
    next_chapter = chapters[index + 1] if index + 1 < len(chapters) else None
    return previous_chapter, next_chapter


def render_document(
    title: str, description: str, body: str, is_chapter: bool = False
) -> str:
    katex_cdn = """
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css" crossorigin="anonymous">
    <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js" crossorigin="anonymous"></script>
    <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js" crossorigin="anonymous"
      onload="renderMathInElement(document.body, {delimiters: [{left:'$$',right:'$$',display:true},{left:'$',right:'$',display:false}]})"></script>
    """ if is_chapter else ""

    chapter_js = """
    <script>
      /* --- Reading progress bar --- */
      (function () {
        var bar = document.getElementById('js-progress');
        if (!bar) return;
        function update() {
          var scrollTop = window.scrollY || document.documentElement.scrollTop;
          var docHeight = document.documentElement.scrollHeight - window.innerHeight;
          var pct = docHeight > 0 ? (scrollTop / docHeight) * 100 : 0;
          bar.style.width = Math.min(100, pct) + '%';
        }
        window.addEventListener('scroll', update, { passive: true });
        update();
      })();

      /* --- Interactive Quiz --- */
      (function () {
        var quiz = document.querySelector('.lesson-section--quiz');
        if (!quiz) return;

        /* 1. Extract correct answers from the <details> block */
        var details = quiz.querySelector('details');
        if (!details) return;
        var answerItems = details.querySelectorAll('ol li');
        var correctAnswers = [];
        function normalize(s) {
          return s.trim().toLowerCase().replace(/[.,;:!?]+$/g, '');
        }
        answerItems.forEach(function (li) {
          correctAnswers.push(normalize(li.textContent));
        });
        details.remove(); /* hide the static answer key */

        /* 2. Parse the alternating OL (question) + UL (options) pairs */
        var ols = quiz.querySelectorAll(':scope > ol');
        var uls = quiz.querySelectorAll(':scope > ul');
        var questions = [];
        for (var i = 0; i < ols.length && i < uls.length; i++) {
          questions.push({ questionEl: ols[i], optionsEl: uls[i] });
        }

        /* 3. Build interactive quiz cards */
        var selections = new Array(questions.length).fill(-1);
        var quizContainer = document.createElement('div');
        quizContainer.className = 'quiz-interactive';

        questions.forEach(function (q, qi) {
          var card = document.createElement('div');
          card.className = 'quiz-card';

          /* Question number + text */
          var qLabel = document.createElement('div');
          qLabel.className = 'quiz-q-label';
          qLabel.textContent = 'Q' + (qi + 1);
          card.appendChild(qLabel);

          var qText = document.createElement('p');
          qText.className = 'quiz-q-text';
          qText.textContent = q.questionEl.querySelector('li').textContent;
          card.appendChild(qText);

          /* Options */
          var optionsDiv = document.createElement('div');
          optionsDiv.className = 'quiz-options';
          var optionLis = q.optionsEl.querySelectorAll('li');
          optionLis.forEach(function (li, oi) {
            var btn = document.createElement('button');
            btn.className = 'quiz-option';
            btn.type = 'button';
            btn.textContent = li.textContent;
            btn.setAttribute('data-qi', qi);
            btn.setAttribute('data-oi', oi);
            btn.addEventListener('click', function () {
              selections[qi] = oi;
              var siblings = optionsDiv.querySelectorAll('.quiz-option');
              siblings.forEach(function (s) { s.classList.remove('selected'); });
              btn.classList.add('selected');
              card.classList.add('answered');
              /* Enable check button if all answered */
              if (selections.every(function (s) { return s >= 0; })) {
                checkBtn.disabled = false;
                checkBtn.classList.add('ready');
              }
            });
            optionsDiv.appendChild(btn);
          });
          card.appendChild(optionsDiv);

          quizContainer.appendChild(card);

          /* Remove the original OL and UL from the DOM */
          q.questionEl.remove();
          q.optionsEl.remove();
        });

        /* 4. Check Answers button */
        var checkBtn = document.createElement('button');
        checkBtn.className = 'quiz-check-btn';
        checkBtn.type = 'button';
        checkBtn.textContent = 'Check my answers';
        checkBtn.disabled = true;

        /* Results area */
        var resultsDiv = document.createElement('div');
        resultsDiv.className = 'quiz-results';

        checkBtn.addEventListener('click', function () {
          var score = 0;
          var cards = quizContainer.querySelectorAll('.quiz-card');
          cards.forEach(function (card, qi) {
            var options = card.querySelectorAll('.quiz-option');
            options.forEach(function (opt, oi) {
              var optText = normalize(opt.textContent);
              var isCorrect = optText === correctAnswers[qi];
              var isSelected = selections[qi] === oi;
              opt.disabled = true;
              if (isCorrect) {
                opt.classList.add('correct');
              }
              if (isSelected && !isCorrect) {
                opt.classList.add('incorrect');
              }
            });
            var selectedText = '';
            if (selections[qi] >= 0) {
              selectedText = normalize(options[selections[qi]].textContent);
            }
            if (selectedText === correctAnswers[qi]) {
              score++;
              card.classList.add('quiz-card--correct');
            } else {
              card.classList.add('quiz-card--incorrect');
            }
          });

          checkBtn.style.display = 'none';

          var pct = Math.round((score / questions.length) * 100);
          var passed = pct >= 80;
          resultsDiv.innerHTML =
            '<div class=\"quiz-score ' + (passed ? 'quiz-score--pass' : 'quiz-score--retry') + '\">' +
            '<span class=\"quiz-score-number\">' + score + '/' + questions.length + '</span>' +
            '<span class=\"quiz-score-label\">' + (passed ? 'Chapter unlocked!' : 'Keep going — you need 80% to unlock.') + '</span>' +
            '</div>';
          resultsDiv.style.display = 'block';

          /* Show "Try again" button */
          retryBtn.style.display = '';
        });

        /* 5. Retry button */
        var retryBtn = document.createElement('button');
        retryBtn.className = 'quiz-check-btn ready';
        retryBtn.type = 'button';
        retryBtn.textContent = 'Try again';
        retryBtn.style.display = 'none';

        retryBtn.addEventListener('click', function () {
          /* Reset all state */
          selections = new Array(questions.length).fill(-1);
          var cards = quizContainer.querySelectorAll('.quiz-card');
          cards.forEach(function (card) {
            card.classList.remove('answered', 'quiz-card--correct', 'quiz-card--incorrect');
            var options = card.querySelectorAll('.quiz-option');
            options.forEach(function (opt) {
              opt.disabled = false;
              opt.classList.remove('selected', 'correct', 'incorrect');
            });
          });
          checkBtn.disabled = true;
          checkBtn.classList.remove('ready');
          checkBtn.style.display = '';
          retryBtn.style.display = 'none';
          resultsDiv.style.display = 'none';
          resultsDiv.innerHTML = '';

          /* Scroll quiz into view */
          quiz.scrollIntoView({ behavior: 'smooth', block: 'start' });
        });

        /* 6. Insert everything into the quiz section */
        var heading = quiz.querySelector('h2');
        /* Clear remaining content after the heading */
        while (heading.nextSibling) {
          heading.nextSibling.remove();
        }
        quiz.appendChild(quizContainer);
        quiz.appendChild(checkBtn);
        quiz.appendChild(retryBtn);
        quiz.appendChild(resultsDiv);
      })();
    </script>
    """ if is_chapter else ""

    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{escape(title)} — Math Journey</title>
    <meta name="description" content="{escape(description)}" />
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Source+Serif+4:ital,opsz,wght@0,8..60,300..700;1,8..60,300..700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="/assets/site.css" />
    {katex_cdn}
  </head>
  <body>
    {body}
    {chapter_js}
  </body>
</html>
"""


if __name__ == "__main__":
    main()
