# Chapter Schema

## Purpose of This Document
This document defines the standard structure for every chapter in Math Journey. It is the canonical template for chapter design, writing, assembly, review, and implementation.

The goal is consistency. Every chapter should feel like part of the same product, even when the topic, historical era, or difficulty level changes.

## Core Principle
A chapter is not just a page of content. It is a structured learning unit with:
- a clear educational purpose
- a recognizable internal sequence
- a consistent set of content blocks
- formal mathematical material
- practice and assessment
- a clear relationship to the larger curriculum

## What This Schema Controls
This schema defines:
- chapter metadata
- required sections
- optional sections
- standard ordering
- content block types
- implementation expectations
- review expectations

This document should be used by:
- curriculum planning
- chapter writing
- design
- front-end implementation
- editorial QA

## Chapter Identity
Every chapter must have a stable identity.

### Required Metadata Fields
Each chapter should define the following metadata fields at the top of the file.

```yaml
id: ch-001
slug: why-numbers-exist
title: Why Numbers Exist
world: world-00-language-of-number
worldNumber: 0
chapterNumber: 1
level: foundational
estimatedTimeMinutes: 35
core: true
prerequisites: []
historicalPeriod: "prehistory to early civilizations"
historicalRegions:
  - Mesopotamia
  - Egypt
  - India
mainFigures: []
mainConcepts:
  - number
  - counting
  - quantity
learningObjectives:
  - Understand why number systems emerged
  - Distinguish counting from measurement
  - Explain how numerical systems support trade and record-keeping
unlockCriteria:
  quizMinScore: 0.8
  practiceRequired: true
  reasoningRequired: false
```

### Optional Metadata Fields
Use these when the chapter benefits from them:

```yaml
subtitle: "How humans turned quantity into language"
status: draft
tags:
  - history
  - arithmetic
  - foundations
keyTerms:
  - quantity
  - counting
  - numeral
relatedChapters:
  - ch-002
storySetting:
  place: "Mesopotamia"
  era: "early cities and trade networks"
assets:
  heroImage: "illustrations/counting-tokens.png"
  diagrams:
    - "images/place-value-grid.svg"
review:
  mathChecked: false
  historicalChecked: false
  editorialChecked: false
```

## File Naming Rule
Chapter files should live at:

`/content/world-xx-descriptive-slug/ch-xxx-descriptive-slug.mdx`

This makes the curriculum order and chapter identity readable from the path.

## Required Chapter Sections
Every chapter should contain these sections in this order unless there is a strong reason not to.

### 1. Story Hook
Open with a scene, tension, or human problem that makes the chapter concept necessary.

### 2. Why It Matters
State why the concept matters in practical, scientific, historical, or future-curriculum terms.

### 3. Historical Context
Give the learner a grounded sense of the cultures, needs, or transmission history involved.

### 4. Core Concept
Explain the main idea in plain but precise language before introducing too much notation.

### 5. Definitions and Formal Lesson
Present definitions, notation, formulas, theorems, and relationships in a structured way.

### 6. Worked Examples
Include at least two solved examples that model actual reasoning.

### 7. Practice Set
Provide independent problems that align directly with the chapter objectives.

### 8. Reasoning Task
Ask the learner to explain, compare, justify, derive, or critique something.

### 9. Application or Lab
Connect the idea to a real-world or scientific use case.

### 10. Recap
Summarize key ideas, terms, and forward links.

### 11. Unlock Quiz
Provide a short end-of-chapter mastery check.

## Strongly Recommended Optional Sections
- misconceptions
- quick review of prerequisites
- glossary terms
- challenge extension
- teacher or parent note for early chapters
- source notes for historical chapters

## Content Block Types
Chapters should be assembled from a repeatable set of block types.

### Narrative Blocks
- story intro
- historical scene
- voiceover transition

### Teaching Blocks
- concept explanation
- definition
- formula card
- theorem block
- diagram explanation

### Practice Blocks
- worked example
- guided question
- independent practice
- hint reveal

### Mastery Blocks
- reasoning task
- recap
- unlock quiz

## Minimum Expectations Per Chapter
A chapter is not complete unless it includes:
- one meaningful story opening
- one clear historical anchor
- one precise concept explanation
- one formal section with mathematical content
- at least two worked examples
- at least five practice problems
- at least one reasoning prompt
- one application or transfer connection
- one recap
- one unlock check

## Recommended Internal Pacing
As a rough guide for a standard chapter:
- story and framing: 10 to 15 percent
- core concept and formal lesson: 30 to 35 percent
- worked examples: 20 to 25 percent
- practice and reasoning: 20 to 25 percent
- recap and unlock check: 10 percent

This is not rigid, but it helps prevent chapters from becoming either all exposition or all exercises.

## Canonical MDX Skeleton

```mdx
---
id: ch-000
slug: sample-slug
title: Sample Title
world: world-00-sample
worldNumber: 0
chapterNumber: 0
level: foundational
estimatedTimeMinutes: 35
core: true
prerequisites: []
historicalPeriod: "..."
historicalRegions:
  - ...
mainFigures: []
mainConcepts:
  - ...
learningObjectives:
  - ...
unlockCriteria:
  quizMinScore: 0.8
  practiceRequired: true
  reasoningRequired: true
---

# Sample Title

## Story Hook
...

## Why It Matters
...

## Historical Context
...

## Core Concept
...

## Definitions and Formal Lesson
...

## Worked Examples
...

## Practice Set
...

## Reasoning Task
...

## Application
...

## Recap
...

## Unlock Quiz
...
```

## Writing and Review Expectations
Each chapter should be checked for:
- mathematical correctness
- historical care
- voice consistency
- notation consistency
- alignment to learning objectives
- alignment to interaction and assessment rules

## Implementation Expectations
The chapter source should be readable as plain text and portable into a front-end implementation.

That means:
- text should stand on its own without custom UI
- section headings should remain meaningful
- diagrams and interactions should be additive, not structurally required
- metadata should be parseable

## Definition of Done
A chapter is ready to serve as a reference implementation when:
- the metadata is complete
- the required sections exist
- the content teaches all four learning layers
- practice and unlock expectations are explicit
- the chapter can be understood without hidden context from chat
