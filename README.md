# Math Journey

Math Journey is a docs-first curriculum and content repo for a story-driven mathematics and physics learning platform.

The project starts from basic arithmetic and is designed to grow toward high school and early college topics through history, culture, formal lesson structure, worked examples, practice, and mastery checks.

## Repo Structure
- `docs/` canonical product, curriculum, pedagogy, style, sourcing, and QA documents
- `content/` chapter source files
- `data/` future structured reference data
- `components/`, `src/`, `public/` future implementation scaffolding

## Start Here
- [Project Brief](/Users/remonalberts/Documents/AI/math-journey/docs/PROJECT_BRIEF.md)
- [Product Vision](/Users/remonalberts/Documents/AI/math-journey/docs/00_product_vision.md)
- [Chapter Schema](/Users/remonalberts/Documents/AI/math-journey/docs/04_chapter_schema.md)
- [Agent Guide](/Users/remonalberts/Documents/AI/math-journey/docs/AGENTS.md)
- [First Sample Chapter](/Users/remonalberts/Documents/AI/math-journey/content/world-00-language-of-number/ch-001-why-numbers-exist.mdx)

## Current Status
- canonical docs are in place
- the first sample chapter exists as a reference implementation
- the repo is ready for either more chapter writing or the first front-end/content pipeline pass

## Build The First Site
Run:

```bash
python3 scripts/build_site.py
```

This generates a static site in `dist/`.

To preview it locally:

```bash
python3 -m http.server 8000 --directory dist
```
