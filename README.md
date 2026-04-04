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

## Quiz QA
Run:

```bash
npm run check:quizzes
```

This validates every chapter under `content/` for the unlock quiz structure the site expects:
- a `## Unlock Quiz` section
- numbered questions with answer options
- a `<details>` answer key with matching answers

If you also want to verify the generated `dist/` pages contain quiz markup after a build, run:

```bash
python3 scripts/check_quizzes.py --check-dist
```

## Generate Chapter Illustrations
This repo includes a minimal OpenAI Responses API script for generating Chapter 1 illustration assets with the hosted `image_generation` tool.

1. Install dependencies:

```bash
npm install
```

2. Create an env file:

```bash
cp .env.example .env
```

3. Set `OPENAI_API_KEY` in `.env`.

4. Generate all Chapter 1 raster illustrations:

```bash
npm run generate:illustrations
```

5. Generate only the hero image:

```bash
npm run generate:illustrations:hero
```

The generator reads [ch-001.json](/Users/remonalberts/Documents/AI/math-journey/data/illustrations/ch-001.json), writes images into [public/illustrations/world-00-language-of-number](/Users/remonalberts/Documents/AI/math-journey/public/illustrations/world-00-language-of-number), and saves a sibling metadata JSON file next to each generated image with the original prompt and any revised prompt returned by the API.
