# AGENTS

## Purpose
This file is the operating guide for humans and agents working inside the Math Journey repo.

The repo is currently **docs-first**. The immediate job is to define a durable curriculum and content system before building a full product surface.

## Current State
- `/docs` contains the canonical product, curriculum, pedagogy, and editorial rules.
- `/content` contains chapter files and should become the main source of lesson content.
- `/data` is reserved for reusable structured references such as glossary terms, people, theorems, and timelines.
- `/components`, `/src`, and `/public` are placeholders for future implementation work and should not become the source of truth for curriculum decisions.

## Working Rules
- Read the relevant canonical docs in `/docs` before making structural changes.
- Treat repo files as the source of truth, not chat history.
- Add resolved project decisions to [DECISIONS.md](/Users/remonalberts/Documents/AI/math-journey/docs/DECISIONS.md).
- Prefer extending an existing canonical document over creating a duplicate one.
- Keep naming consistent with the documented patterns for worlds and chapters.

## Canonical Doc Order
When making curriculum or content decisions, use these docs in roughly this order:
- [PROJECT_BRIEF.md](/Users/remonalberts/Documents/AI/math-journey/docs/PROJECT_BRIEF.md)
- [00_product_vision.md](/Users/remonalberts/Documents/AI/math-journey/docs/00_product_vision.md)
- [01_audience_and_levels.md](/Users/remonalberts/Documents/AI/math-journey/docs/01_audience_and_levels.md)
- [02_curriculum_map.md](/Users/remonalberts/Documents/AI/math-journey/docs/02_curriculum_map.md)
- [03_learning_model.md](/Users/remonalberts/Documents/AI/math-journey/docs/03_learning_model.md)
- [04_chapter_schema.md](/Users/remonalberts/Documents/AI/math-journey/docs/04_chapter_schema.md)
- [05_voices_and_story_style.md](/Users/remonalberts/Documents/AI/math-journey/docs/05_voices_and_story_style.md)
- [06_math_notation_and_glossary_rules.md](/Users/remonalberts/Documents/AI/math-journey/docs/06_math_notation_and_glossary_rules.md)
- [07_interaction_patterns.md](/Users/remonalberts/Documents/AI/math-journey/docs/07_interaction_patterns.md)
- [08_visual_design_system.md](/Users/remonalberts/Documents/AI/math-journey/docs/08_visual_design_system.md)
- [09_historical_sourcing_rules.md](/Users/remonalberts/Documents/AI/math-journey/docs/09_historical_sourcing_rules.md)
- [10_problem_and_assessment_system.md](/Users/remonalberts/Documents/AI/math-journey/docs/10_problem_and_assessment_system.md)
- [11_editorial_workflow_and_QA.md](/Users/remonalberts/Documents/AI/math-journey/docs/11_editorial_workflow_and_QA.md)

## File Conventions
- World folders follow `world-xx-descriptive-slug`.
- Chapter files follow `ch-xxx-descriptive-slug.mdx`.
- Canonical docs in `/docs` should use zero-padded prefixes when order matters.
- Prefer lowercase filenames with underscores for docs.

## Chapter Authoring Rules
- Every chapter must follow the metadata and section rules in [04_chapter_schema.md](/Users/remonalberts/Documents/AI/math-journey/docs/04_chapter_schema.md).
- A chapter should include story, formal learning, worked examples, practice, reasoning, recap, and an unlock check.
- Story should motivate the concept, not replace the math.
- Historical claims should follow [09_historical_sourcing_rules.md](/Users/remonalberts/Documents/AI/math-journey/docs/09_historical_sourcing_rules.md).
- Notation and term choices should follow [06_math_notation_and_glossary_rules.md](/Users/remonalberts/Documents/AI/math-journey/docs/06_math_notation_and_glossary_rules.md).

## Editing Priorities
- Strengthen the system before multiplying content.
- Create one excellent reference chapter before broad expansion.
- Keep components and interaction ideas limited to the documented pattern library.
- Avoid speculative implementation work that is not yet anchored in the curriculum and chapter system.

## When You Finish Meaningful Work
- Update or create the relevant doc or content file.
- Record any new resolved decision in [DECISIONS.md](/Users/remonalberts/Documents/AI/math-journey/docs/DECISIONS.md).
- Leave the repo clearer than you found it.
