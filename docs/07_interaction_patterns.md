# Interaction Patterns

## Purpose of This Document
This document defines the core interaction patterns used across Math Journey. Its purpose is to create consistency, reduce design drift, simplify implementation, and ensure that chapters feel like part of the same product.

This is not a list of every possible UI element. It is a rulebook for the small set of reusable interaction types the product should rely on.

## Core Principle
Do not invent new interactions casually.

The product should feel rich because the content is strong and the interaction patterns are well designed, not because every chapter has a different gimmick.

A limited set of patterns will make the platform:
- easier to build
- easier to maintain
- easier to understand
- more coherent for learners
- more scalable across many chapters

## Interaction Design Goals
Interactions should:
- support learning, not distract from it
- clarify mathematical ideas
- reinforce chapter structure
- create rhythm and variety
- make progress visible
- work across beginner and advanced content
- remain usable even when the learner is new to the topic

## Global Interaction Rules

### Rule 1: Text First
The lesson must still work as a lesson even if an interactive element fails to load.

### Rule 2: One Purpose Per Interaction
Every interaction should do one main job clearly.

### Rule 3: Reuse Over Novelty
If an existing pattern can solve the problem, reuse it instead of inventing a new one.

### Rule 4: Low Friction
Interactions should not require the learner to "figure out the interface" before learning the concept.

### Rule 5: No Decorative Motion
Animation and motion should support comprehension, attention, or progression. They should not exist just to look advanced.

### Rule 6: Progress Should Be Visible
Learners should be able to see where they are, what they completed, and what comes next.

## Core Interaction Library
The product should be built around a small library of repeatable patterns.

---

## Pattern 01 — Story Intro

### Purpose
Create emotional and intellectual entry into the chapter through a story, scene, or historical moment.

### Typical Content
- short narrative opening
- image or illustration
- optional highlighted quote
- optional historical setting note

### Behavior
- appears near the top of the chapter
- should feel visually distinct from the formal lesson
- may include a "continue into lesson" transition

### Rules
- keep it concise
- do not bury the learner in too much exposition before teaching begins
- the story should lead naturally into the concept

### Use Cases
- why numbers emerged
- Kepler struggling with Mars
- Euclid and proof
- al-Khwarizmi solving inheritance and algebraic problems
- Einstein questioning light and simultaneity

---

## Pattern 02 — Why It Matters Block

### Purpose
Explicitly state why the idea matters before or during formal instruction.

### Typical Content
- practical significance
- scientific importance
- historical consequence
- forward-looking curricular importance

### Behavior
- short callout block
- can appear after Story Intro or before Formal Lesson

### Rules
- should be brief
- should connect directly to the chapter concept
- should avoid generic claims like “math is everywhere”

---

## Pattern 03 — Concept Block

### Purpose
Explain the main concept in plain but precise language.

### Typical Content
- key idea
- intuitive framing
- one diagram or visual if useful
- short bridge into formal content

### Behavior
- static text-first block
- may include highlighted definitions

### Rules
- should prioritize clarity over density
- should prepare the learner for the formal lesson

---

## Pattern 04 — Definition Block

### Purpose
Present a key term in a stable visual format.

### Typical Content
- term
- precise definition
- optional informal paraphrase
- optional example

### Behavior
- card-like treatment
- visually consistent everywhere in the product

### Rules
- definitions should be short and exact
- use the same style throughout the site

---

## Pattern 05 — Formula Card

### Purpose
Present a formula or relationship in a memorable, reusable format.

### Typical Content
- formula
- variable meanings
- short interpretation
- optional unit note
- optional conditions or constraints

### Behavior
- visually prominent but not oversized
- can be reused in lesson, recap, or reference mode

### Rules
- all variable meanings must be explicit
- avoid showing formulas without context
- use consistent notation treatment site-wide

---

## Pattern 06 — Theorem Block

### Purpose
Present a theorem, proposition, or named result in a formal but approachable format.

### Typical Content
- theorem name
- statement
- optional plain-language interpretation
- optional small diagram
- optional proof link or proof reveal

### Behavior
- styled more formally than a standard definition
- may link to deeper reasoning content

### Rules
- theorem statements should be exact
- avoid fake precision in early chapters
- only use theorem blocks when the result is important enough to deserve formal treatment

---

## Pattern 07 — Worked Example Stepper

### Purpose
Walk the learner through a problem in structured steps.

### Typical Content
- problem statement
- step-by-step solution
- highlighted reasoning
- optional “watch out” notes
- final answer

### Behavior
- can be fully visible or step-reveal
- may allow learner to reveal one step at a time

### Rules
- each step should reflect actual reasoning, not just answer dumping
- avoid overly long examples without segmentation
- at least some examples should be visible without interaction

### Why It Matters
This will be one of the most important teaching patterns in the whole product.

---

## Pattern 08 — Practice Set

### Purpose
Let learners solve problems independently.

### Typical Content
- problem list
- answer input or self-check mode
- difficulty tags
- optional hints
- optional solution reveal after attempt

### Behavior
- grouped into small, manageable sets
- may provide instant feedback
- may unlock hint after first attempt

### Rules
- practice should not feel endless
- problem types should align with chapter objectives
- use a consistent difficulty progression

---

## Pattern 09 — Hint Reveal

### Purpose
Support stuck learners without immediately giving away the full solution.

### Typical Content
- conceptual nudge
- setup hint
- first step hint
- common error note

### Behavior
- hidden by default
- revealed on demand

### Rules
- hints should guide, not replace thinking
- use no more than 2 to 3 hint levels in standard practice
- avoid hints that are almost the full answer

---

## Pattern 10 — Solution Reveal

### Purpose
Allow learners to inspect a complete solution after genuine effort.

### Typical Content
- full worked solution
- reasoning notes
- optional comparison with alternative methods

### Behavior
- hidden by default in practice mode
- can be revealed after attempt or by user action

### Rules
- should be clearly distinct from hints
- should not be the first thing the learner sees
- should preserve instructional quality

---

## Pattern 11 — Reasoning Task

### Purpose
Push learners beyond procedure into explanation, proof, comparison, or justification.

### Typical Content
- explain why
- identify an error
- compare methods
- fill in a proof skeleton
- justify a pattern
- interpret a visual argument

### Behavior
- presented as a focused prompt
- may support short written response or guided selection

### Rules
- keep the prompt precise
- reasoning tasks should be central, not decorative
- difficulty should match learner level

---

## Pattern 12 — Proof Reveal

### Purpose
Support formal reasoning without overwhelming beginners.

### Typical Content
- theorem statement
- proof sketch
- visual proof
- full formal proof in later chapters

### Behavior
- collapsed by default in some chapters
- expandable for curious or advanced learners

### Rules
- not every chapter needs a proof reveal
- use where formal justification adds real value
- label proof difficulty clearly if needed

---

## Pattern 13 — Application Block

### Purpose
Show how a concept operates in the real world, history, science, or physics.

### Typical Content
- short applied scenario
- diagram, map, or data visualization
- explanatory text
- optional mini-question

### Behavior
- usually appears after formal learning and practice
- may include light interactivity

### Rules
- applications must be genuinely connected to the concept
- avoid fake “real-world relevance”
- keep it focused

---

## Pattern 14 — Timeline Strip

### Purpose
Situate a concept or person inside the broader historical arc.

### Typical Content
- era marker
- region markers
- related events
- neighboring figures or developments

### Behavior
- compact horizontal or vertical timeline
- non-blocking
- optional expand for more detail

### Rules
- use sparingly but consistently
- should help orientation, not overload the page

---

## Pattern 15 — Map / Civilization Context

### Purpose
Show where an idea emerged or developed.

### Typical Content
- region highlights
- civilization labels
- trade routes or transmission paths where relevant
- associated figures or texts

### Behavior
- can be static or lightly interactive
- often paired with story or history sections

### Rules
- prioritize clarity over geographic detail
- use to reinforce the cross-cultural nature of the curriculum

---

## Pattern 16 — Diagram Explorer

### Purpose
Help learners understand a visual mathematical relationship by manipulating a simple diagram.

### Typical Content
- geometric construction
- function graph
- unit circle view
- triangle ratio diagram
- vector decomposition
- orbit or ellipse diagram

### Behavior
- draggable points, sliders, or toggles
- immediate visual response

### Rules
- only use when interactivity genuinely improves understanding
- controls must be obvious
- avoid excessive feature complexity

### Best Use Cases
- Pythagorean relationships
- slope
- graph transformations
- trig on the unit circle
- ellipse geometry
- vectors

---

## Pattern 17 — Quiz Block

### Purpose
Check chapter mastery and control progression.

### Typical Content
- 4 to 8 questions
- mixed conceptual and procedural checks
- immediate or delayed scoring
- pass threshold indicator

### Behavior
- appears at the end of chapter
- may gate next chapter unlock

### Rules
- questions should align tightly to chapter goals
- do not overuse trick questions
- provide simple feedback where possible

---

## Pattern 18 — Recap Block

### Purpose
Consolidate the chapter.

### Typical Content
- main idea
- key definitions
- formulas
- one-line memory anchor
- “what this prepares you for”

### Behavior
- short and skimmable
- appears near chapter end

### Rules
- should be compact
- should not introduce new material

---

## Pattern 19 — Next Step Block

### Purpose
Show the learner where to go next.

### Typical Content
- next chapter
- optional side quests
- related review chapter
- key dependency note

### Behavior
- clear end-of-chapter transition
- may include a small journey map

### Rules
- should preserve momentum
- should make the path legible

---

## Pattern 20 — Progress Map

### Purpose
Show the learner their place in the larger curriculum.

### Typical Content
- world structure
- current chapter
- completed chapters
- locked chapters
- optional side branches

### Behavior
- used on dashboard, world pages, and chapter header/footer zones

### Rules
- the main path should always be easy to understand
- do not let the map become visually overwhelming

## Pattern Priority Levels

### Tier A — Must Exist Early
These are required for the first usable version:
- Story Intro
- Why It Matters Block
- Concept Block
- Definition Block
- Formula Card
- Worked Example Stepper
- Practice Set
- Reasoning Task
- Quiz Block
- Recap Block
- Next Step Block

### Tier B — Strongly Recommended
These should come soon after:
- Theorem Block
- Hint Reveal
- Solution Reveal
- Application Block
- Progress Map

### Tier C — Add Later
These are valuable but not required for the first version:
- Proof Reveal
- Timeline Strip
- Map / Civilization Context
- Diagram Explorer

## Consistency Rules for Interactions

### Same Pattern, Same Behavior
If a learner sees a Formula Card in one chapter, it should work the same way in every chapter.

### Same Pattern, Same Visual Language
Each interaction type should have a stable appearance.

### Same Pattern, Same Naming
Do not rename the same kind of thing in different chapters.

### Same Pattern, Same Cognitive Role
A Quiz Block should always feel like assessment.
A Story Intro should always feel like entry.
A Recap should always feel like consolidation.

## Mobile and Simplicity Rules
Interactions must work well on smaller screens.

Therefore:
- avoid tiny drag targets
- avoid dense control panels
- avoid interactions that require high precision
- keep layout stacked and readable
- ensure that all critical content is available without hover

## Accessibility Rules
Interactions should:
- be keyboard accessible where feasible
- not rely on color alone
- have clear labels
- allow learners to understand what to do immediately
- preserve meaning in text

## Anti-Patterns to Avoid
Do not add:
- decorative animations with no learning value
- game mechanics that distract from content
- endless click-to-reveal fragmentation
- overcomplicated simulations
- multiple interaction styles that solve the same problem differently
- novelty interfaces that require explanation

## First-Version Recommendation
For the first version of the product, focus on these interaction patterns only:
- Story Intro
- Why It Matters Block
- Definition Block
- Formula Card
- Worked Example Stepper
- Practice Set
- Reasoning Task
- Recap Block
- Quiz Block
- Next Step Block

That is enough to make the product feel rich and structured without overbuilding.

## Final Principle
Interaction should make the learner feel guided, not dazzled.
