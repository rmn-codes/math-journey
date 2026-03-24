# Decisions Log

This file records decisions that have been made for the project. It is a short operational memory for the repo. New entries should be added with the date and written as clearly as possible.

---

## 2026-03-23

- Project working title is **Math Journey**.
- The product direction is a **story-driven math and physics website**.
- The audience includes **kids, teenagers, and curious adults**.
- The learning path starts from **basic arithmetic** and aims to reach **AP / early college level**.
- The platform should combine **history, culture, formulas, theorems, worked examples, and practice problems**.
- The experience should feel **intelligent, cinematic, and respectful**, not childish.
- The curriculum should be structured as a **chapter-based journey** with progression and unlocks.
- The long-term structure is expected to include multiple “worlds” or major learning domains.
- The first implementation priority is to build a **content and product system**, not to write the full curriculum immediately.
- The source of truth should live in **repo files**, not in chat history.
- Canonical project documentation will live in `/docs`.
- Lesson content is expected to live in `/content`.
- The initial top-level local folders are:
  - `/docs`
  - `/content`
  - `/components`
  - `/data`
- The first chapter file is:
  - `/content/world-00-language-of-number/ch-001-why-numbers-exist.mdx`
- The first core docs to complete are:
  - `PROJECT_BRIEF.md`
  - `DECISIONS.md`
  - `00_product_vision.md`
  - `02_curriculum_map.md`
  - `03_learning_model.md`
  - `04_chapter_schema.md`
  - `07_interaction_patterns.md`
- Canonical docs in `/docs` should use lowercase filenames with ordered numeric prefixes where relevant.
- Chapter source files should use the `.mdx` extension.
- The repo should complete its canonical documentation and first sample chapter before major UI implementation begins.

## Rules for using this file

- Add a new dated entry whenever a meaningful decision is made.
- Keep entries short and specific.
- Record only resolved decisions, not open questions.
- If a decision changes later, add a new entry rather than rewriting history silently.
