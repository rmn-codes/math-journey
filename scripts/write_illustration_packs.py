#!/usr/bin/env python3

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import re
import sys
import textwrap

from build_site import parse_document, slugify


ROOT = Path(__file__).resolve().parents[1]
CONTENT_DIR = ROOT / "content"
PACK_DIR = ROOT / "docs" / "reference-packs"
MANIFEST_DIR = ROOT / "data" / "illustrations"


WORLD_META = {
    0: {
        "name": "World 00 — Language of Number",
        "setting": "clay tablets, cave marks, counting stones, storehouses, early marketplaces, record-keepers",
        "atmosphere": "earthy, warm, tactile, lightly dusty, early human intelligence becoming visible",
        "hero_context": "Anchor the scene in tangible counting, grouping, sharing, or recording acts.",
    },
    1: {
        "name": "World 01 — Shape & Measure",
        "setting": "surveyed fields, columns, ropes, surveying tools, measured land, open stone landscapes",
        "atmosphere": "sunlit, precise, spacious, geometric",
        "hero_context": "Anchor the scene in measuring land, comparing shapes, constructing forms, or proving spatial relationships.",
    },
    2: {
        "name": "World 02 — Algebra",
        "setting": "scholar's room, papyrus, balances, written transformations, tables, oil lamps",
        "atmosphere": "amber-lit, thoughtful, balanced, mysterious but clear",
        "hero_context": "Anchor the scene in reasoning about an unknown, a balance, a written transformation, or a patterned rule.",
    },
    3: {
        "name": "World 03 — Coordination & Functions",
        "setting": "aerial cities, grids, axes embedded in terrain, roads, plotted structures",
        "atmosphere": "cool, ordered, elevated, spatially intelligible",
        "hero_context": "Anchor the scene in plotted points, axes, slopes, graphs, paths, or visible input-output structure.",
    },
    4: {
        "name": "World 04 — Trigonometry & Astronomy",
        "setting": "observatories, stars, instruments, angular sightlines, domes, night terraces",
        "atmosphere": "deep teal night, terracotta light, celestial precision",
        "hero_context": "Anchor the scene in turning, angular measurement, celestial observation, wave geometry, or directional magnitude.",
    },
    5: {
        "name": "World 05 — Calculus",
        "setting": "flowing rivers, slopes, changing hills, arrows, motion lines, accumulation landscapes",
        "atmosphere": "kinetic, windy, dynamic, continuous",
        "hero_context": "Anchor the scene in motion, slope, accumulation, changing rates, or flowing curves made visible.",
    },
    6: {
        "name": "World 06 — Probability & Statistics",
        "setting": "market stalls, games of chance, tokens, cards, counting boards, crowd patterns",
        "atmosphere": "lively but orderly, warm, patterned beneath apparent chaos",
        "hero_context": "Anchor the scene in uncertainty, repeated trials, data, risk, comparison, or patterned randomness.",
    },
    7: {
        "name": "World 07 — Modern Mathematics",
        "setting": "folded spaces, impossible geometries, abstract fields, dimensional transitions",
        "atmosphere": "most surreal world, teal-dominant, dreamlike but coherent",
        "hero_context": "Anchor the scene in abstract structure becoming spatially tangible without losing clarity.",
    },
}


GLOBAL_CONSTRAINTS = [
    "Follow `docs/illustration-guide.md` exactly.",
    "Prioritize immediate mathematical readability over atmosphere.",
    "Keep all images page-integrated, warm, light, and hand-drawn.",
    "Restrict palette to:",
    "  - warm cream `#f7f5f1`",
    "  - deep teal `#1a7a84`",
    "  - terracotta `#c06030`",
    "  - near-black ink `#1a1a1a`",
    "  - soft ink `#4a4540`",
    "  - faint ink `#8e8680`",
    "Avoid:",
    "  - photorealism",
    "  - glossy digital cartoon rendering",
    "  - muddy lighting",
    "  - fantasy-medieval drift",
    "  - crowded scenes",
    "  - ambiguous mathematical objects",
    "  - decorative rather than functional symbols",
]


@dataclass
class ChapterInfo:
    source_path: Path
    metadata: dict
    body: str

    @property
    def chapter_id(self) -> str:
        return str(self.metadata.get("id") or f"ch-{self.chapter_number:03d}")

    @property
    def chapter_number(self) -> int:
        raw = self.metadata.get("chapterNumber") or self.metadata.get("chapter")
        return int(raw)

    @property
    def world_number(self) -> int:
        return int(self.metadata.get("worldNumber"))

    @property
    def world_slug(self) -> str:
        return str(self.metadata.get("world"))

    @property
    def title(self) -> str:
        return str(self.metadata.get("title", self.source_path.stem))

    @property
    def subtitle(self) -> str:
        return str(self.metadata.get("subtitle", "")).strip()

    @property
    def historical_period(self) -> str:
        return str(self.metadata.get("historicalPeriod", "historical period not specified")).strip()

    @property
    def historical_regions(self) -> list[str]:
        raw = self.metadata.get("historicalRegions", [])
        if isinstance(raw, list):
            return [str(item).strip() for item in raw if str(item).strip()]
        if isinstance(raw, str):
            return [part.strip() for part in raw.split(",") if part.strip()]
        return []

    @property
    def main_concepts(self) -> list[str]:
        raw = self.metadata.get("mainConcepts", [])
        if isinstance(raw, list):
            return [str(item).strip() for item in raw if str(item).strip()]
        if isinstance(raw, str):
            return [part.strip() for part in raw.split(",") if part.strip()]
        return []

    @property
    def learning_objectives(self) -> list[str]:
        raw = self.metadata.get("learningObjectives", [])
        if isinstance(raw, list):
            return [str(item).strip() for item in raw if str(item).strip()]
        if isinstance(raw, str):
            return [raw.strip()]
        return []

    @property
    def slug(self) -> str:
        raw = str(self.metadata.get("slug", "")).strip()
        return raw or slugify(self.title)


def main() -> None:
    chapters = load_chapters()
    force = "--force" in sys.argv[1:]
    generated = 0

    for chapter in chapters:
        pack_path = PACK_DIR / f"{chapter.chapter_id}-illustration-generation-pack.md"
        manifest_path = MANIFEST_DIR / f"{chapter.chapter_id}.json"
        if not force and pack_path.exists() and manifest_path.exists():
            continue

        sections = build_sections(chapter)
        pack_path.write_text(render_pack(chapter, sections), encoding="utf-8")
        manifest_path.write_text(render_manifest(chapter, sections), encoding="utf-8")
        generated += 1

    print(f"Wrote {generated} illustration pack(s) and manifest(s).")


def load_chapters() -> list[ChapterInfo]:
    chapters: list[ChapterInfo] = []
    for path in sorted(CONTENT_DIR.rglob("ch-*.mdx")):
        metadata, body = parse_document(path.read_text(encoding="utf-8"))
        if not metadata:
            continue
        world_number = metadata.get("worldNumber")
        chapter_number = metadata.get("chapterNumber") or metadata.get("chapter")
        if world_number is None or chapter_number is None:
            continue
        chapters.append(ChapterInfo(path, metadata, body))
    chapters.sort(key=lambda chapter: (chapter.world_number, chapter.chapter_number))
    return chapters


def build_sections(chapter: ChapterInfo) -> list[dict[str, str]]:
    concept_names = chapter.main_concepts or ["core concept"]
    concept_primary = concept_names[0]
    concept_secondary = concept_names[1] if len(concept_names) > 1 else "mathematical relationship"
    map_label = map_filename_label(chapter.historical_regions) or chapter.slug

    return [
        {
            "heading": "Hero",
            "id": "hero",
            "file": output_file(chapter, "hero", chapter.slug),
            "prompt": hero_prompt(chapter),
        },
        {
            "heading": "Story Spot",
            "id": "story",
            "file": output_file(chapter, "story", chapter.slug),
            "prompt": story_prompt(chapter),
        },
        {
            "heading": title_case_label(concept_primary),
            "id": f"concept_{slugify(concept_primary)}",
            "file": output_file(chapter, "concept", slugify(concept_primary)),
            "prompt": concept_prompt(chapter, 0),
        },
        {
            "heading": title_case_label(concept_secondary),
            "id": f"concept_{slugify(concept_secondary)}",
            "file": output_file(chapter, "concept", slugify(concept_secondary)),
            "prompt": concept_prompt(chapter, 1),
        },
        {
            "heading": "Historical Map",
            "id": "map",
            "file": output_file(chapter, "map", map_label),
            "prompt": map_prompt(chapter),
        },
        {
            "heading": "Closing Vignette",
            "id": "closing",
            "file": output_file(chapter, "closing", chapter.slug),
            "prompt": closing_prompt(chapter),
        },
    ]


def render_pack(chapter: ChapterInfo, sections: list[dict[str, str]]) -> str:
    lines = [
        f"# Chapter {chapter.chapter_number} Illustration Generation Pack",
        "",
        f"This file collects the generation-ready prompts for every Chapter {chapter.chapter_number} image.",
        "",
        "Use it together with `docs/illustration-guide.md` when generating or reviewing chapter images.",
        "",
        "## Global Constraints",
        "",
    ]
    lines.extend(f"- {line}" if not line.startswith("  - ") else line for line in GLOBAL_CONSTRAINTS)
    for section in sections:
        lines.extend(
            [
                "",
                f"## {section['heading']}",
                "",
                f"**File:** `{Path(section['file']).name}`",
                "",
                "```text",
                section["prompt"],
                "```",
            ]
        )
    lines.append("")
    return "\n".join(lines)


def render_manifest(chapter: ChapterInfo, sections: list[dict[str, str]]) -> str:
    payload = {
        "chapter": chapter.chapter_id,
        "model": "gpt-5",
        "images": [
            {
                "id": section["id"],
                "output": section["file"],
                "prompt": section["prompt"],
            }
            for section in sections
        ],
    }
    return json.dumps(payload, indent=2) + "\n"


def output_file(chapter: ChapterInfo, role: str, label: str) -> str:
    world_code = f"w{chapter.world_number:02d}"
    chapter_code = f"ch{chapter.chapter_number:03d}"
    file_name = f"{world_code}-{chapter_code}-{role}-{slugify(label)}.png"
    return f"public/illustrations/{chapter.world_slug}/{file_name}"


def hero_prompt(chapter: ChapterInfo) -> str:
    world = WORLD_META[chapter.world_number]
    story_seed = first_paragraph(extract_section(chapter.body, "Story Hook"))
    concept_phrase = summarize_concepts(chapter.main_concepts, 3)
    example = example_seed(chapter, 0)
    return normalize_prompt(
        f"""
        Create a chapter-opening hero illustration for "{chapter.title}." The image should communicate the chapter idea at first glance: {chapter.subtitle or chapter.title}. Use the first-story-hook situation as narrative anchor: {story_seed} Keep the chapter's core mathematical act visible through concrete objects and spatial relationships, especially {concept_phrase}.

        World setting: {world['name']}. Use {world['setting']}. Atmosphere: {world['atmosphere']}. {world['hero_context']}

        If the chapter benefits from a specific readable example, weave in one explicit case such as {example}. The example should feel naturally embedded in the scene rather than pasted on as a poster.

        Mode: Hero Scene.
        The composition should leave breathing room for a chapter header while still keeping the mathematical action dominant. Background architecture and environment should remain soft and secondary.

        Mood: curious, intelligent, humane, lightly whimsical, never grim or over-dramatic.

        Style: page-integrated ink-and-wash illustration on warm cream paper, hand-drawn near-black linework with natural variation, delicate cross-hatching, loose watercolor fills, tactile materials, and restrained contrast.

        Palette restricted to warm cream (#f7f5f1), deep teal (#1a7a84), terracotta (#c06030), near-black ink (#1a1a1a), soft ink (#4a4540), and faint ink neutrals (#8e8680).

        Avoid: photorealism, glossy digital painting, fantasy drift, cluttered scenes, vague symbolism, or mathematical objects that are too small or ambiguous to read.
        """
    )


def story_prompt(chapter: ChapterInfo) -> str:
    world = WORLD_META[chapter.world_number]
    story_seed = first_paragraph(extract_section(chapter.body, "Story Hook"))
    return normalize_prompt(
        f"""
        Create an intimate story vignette for "{chapter.title}" based closely on this narrative moment: {story_seed} Focus on a single human-scale action, gesture, or close scene that makes the chapter's mathematical situation emotionally and visually clear without requiring text to explain it.

        World setting: {world['name']}. Use {world['setting']} in a restrained way. Atmosphere: {world['atmosphere']}.

        Mode: Floating Vignette.
        Keep generous warm cream paper visible around the image. Let edges fade softly into paper. The background should be recessive, with only the minimum environmental detail needed to place the scene.

        Mood: intimate, thoughtful, clear, lightly whimsical.

        Style: hand-drawn ink-and-wash, fine near-black linework, watercolor softness, light cross-hatching, tactile paper and material surfaces.

        Palette restricted to warm cream (#f7f5f1), deep teal (#1a7a84), terracotta (#c06030), near-black ink (#1a1a1a), soft ink (#4a4540), and faint ink neutrals (#8e8680).

        Avoid: poster-like staging, crowded backgrounds, generic portraiture, or a scene so symbolic that the actual mathematical situation disappears.
        """
    )


def concept_prompt(chapter: ChapterInfo, index: int) -> str:
    concept_names = chapter.main_concepts or ["core concept"]
    primary = concept_names[index] if index < len(concept_names) else concept_names[-1]
    supporting = concept_names[index + 1] if index + 1 < len(concept_names) else concept_names[0]
    example = example_seed(chapter, index)
    objective = chapter.learning_objectives[index] if index < len(chapter.learning_objectives) else ""
    objective_line = f"Target learning outcome: {objective}." if objective else ""
    return normalize_prompt(
        f"""
        Create a hand-drawn concept diagram for "{chapter.title}" centered on {primary} and {supporting}. The diagram should make the mathematical relationship immediately legible using explicit labels, arrows, braces, groupings, axes, or correspondences as needed.

        Use one concrete, visually verifiable example: {example}. If quantity matters, the count must be exact. If position, rate, proportion, or transformation matters, that structure must be visible and easy to follow.

        {objective_line}

        Mode: Concept Diagram.
        The math idea is the hero. Keep the layout warm and page-integrated rather than textbook-flat, but do not sacrifice clarity.

        Style: hand-drawn ink sketch with watercolor washes on warm cream paper, natural line variation, small handwritten labels where useful, light cross-hatching, and restrained palette.

        Palette restricted to warm cream (#f7f5f1), deep teal (#1a7a84), terracotta (#c06030), near-black ink (#1a1a1a), soft ink (#4a4540), and faint ink neutrals (#8e8680).

        Avoid: sterile infographic boxes, decorative icons unrelated to the math act, ambiguous counts, tiny unreadable labels, or unnecessary extra examples.
        """
    )


def map_prompt(chapter: ChapterInfo) -> str:
    regions = chapter.historical_regions
    if regions:
        labels = ", ".join(regions[:-1] + [regions[-1]]) if len(regions) == 1 else ", ".join(regions)
        region_instruction = f"Mark and label these historically relevant regions or centers with terracotta dots: {labels}."
    else:
        region_instruction = "Mark and label the key region or transmission centers most relevant to the chapter's history with terracotta dots."
    period = chapter.historical_period
    return normalize_prompt(
        f"""
        Create a historical map for "{chapter.title}" showing where this mathematics developed, circulated, or mattered during {period}. {region_instruction}

        Mode: Historical Map.
        Use recognisably accurate geography with Antarctica omitted and tiny islands reduced. If a route of transmission or comparison helps, add one restrained dashed flow line or soft teal focus wash, but keep geography and labels legible first.

        The map should feel like it was drawn by a careful scholar with a fine quill: accurate enough to teach, warm enough to sit naturally beside the rest of the chapter illustrations.

        Style: deep-teal or near-black coastlines with slight natural line variation, warm cream paper field, restrained teal water wash, subtle hatching texture, minimal hand-drawn cartographic details, and readable handwritten labels with enough contrast.

        Palette restricted to warm cream (#f7f5f1), deep teal (#1a7a84), terracotta (#c06030), near-black ink (#1a1a1a), soft ink (#4a4540), and faint ink neutrals (#8e8680).

        Avoid: political borders unless historically necessary, modern atlas polish, dense legends, decorative sea monsters, or labels too small to read.
        """
    )


def closing_prompt(chapter: ChapterInfo) -> str:
    world = WORLD_META[chapter.world_number]
    concept_phrase = summarize_concepts(chapter.main_concepts, 2)
    example = example_seed(chapter, 1)
    return normalize_prompt(
        f"""
        Create a quiet closing vignette for "{chapter.title}" that leaves the reader with a spacious visual summary of {concept_phrase}. Use a simpler, calmer arrangement than the hero image, with one clear mathematical motif that suggests the idea extending beyond the page. A suitable anchor could be {example}.

        World setting: {world['name']}. Let the setting language appear lightly through materials, geometry, or atmosphere rather than a full scene.

        Mode: Floating Vignette.
        Preserve generous empty paper, softly fading edges, and a contemplative rhythm. The chapter's core idea should still be legible, but quieter and more distilled than in the hero image.

        Mood: calm, thoughtful, inviting, lightly whimsical.

        Style: refined hand-drawn ink-and-wash, delicate cross-hatching, tactile paper, restrained color, and a clean page-integrated composition.

        Palette restricted to warm cream (#f7f5f1), deep teal (#1a7a84), terracotta (#c06030), near-black ink (#1a1a1a), soft ink (#4a4540), and faint ink neutrals (#8e8680).

        Avoid: melodrama, visual noise, mystical abstraction that disconnects from the chapter, or a composition so vague that the mathematical topic becomes unreadable.
        """
    )


def extract_section(body: str, heading: str) -> str:
    pattern = re.compile(
        rf"^##\s+{re.escape(heading)}\s*$\n(.*?)(?=^##\s+|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(body)
    return match.group(1).strip() if match else ""


def first_paragraph(text: str) -> str:
    for block in re.split(r"\n\s*\n", text):
        candidate = clean_markdown(block)
        if candidate:
            return finish_sentence(candidate)
    return "a clear human-scale mathematical moment from the chapter"


def clean_markdown(text: str) -> str:
    text = re.sub(r"^#+\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"\$\$(.*?)\$\$", r"\1", text, flags=re.DOTALL)
    text = re.sub(r"\$(.*?)\$", r"\1", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\*{1,2}([^*]+)\*{1,2}", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1", text)
    text = re.sub(r"^\s*[-*]\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def finish_sentence(text: str) -> str:
    text = text.strip()
    text = re.sub(r"[:;,\-–—]+\s*$", "", text)
    text = re.sub(r'([.!?]["\']?)\.+$', r"\1", text)
    text = re.sub(r"\.{2,}$", ".", text)
    if text and not re.search(r'[.!?]["\']?$', text):
        text += "."
    return text


def summarize_concepts(concepts: list[str], max_items: int) -> str:
    chosen = concepts[:max_items]
    if not chosen:
        return "the chapter's central mathematical relationship"
    if len(chosen) == 1:
        return chosen[0]
    if len(chosen) == 2:
        return f"{chosen[0]} and {chosen[1]}"
    return ", ".join(chosen[:-1]) + f", and {chosen[-1]}"


def title_case_label(text: str) -> str:
    words = re.split(r"\s+", text.strip())
    return " ".join(word[:1].upper() + word[1:] for word in words if word)


def map_filename_label(regions: list[str]) -> str:
    if not regions:
        return ""
    normalized = [slugify(region) for region in regions[:3]]
    return "-".join(part for part in normalized if part)


def normalize_prompt(text: str) -> str:
    return textwrap.dedent(text).strip()


def example_seed(chapter: ChapterInfo, variant: int) -> str:
    title_blob = f"{chapter.title} {' '.join(chapter.main_concepts)} {chapter.slug}".lower()
    keyword_examples = [
        (["complex"], ["the point 3 + 2i plotted on the complex plane with modulus and angle"]),
        (["coordinate plane", "ordered pair", "quadrant"], ["the point (3, 2) or (-2, 4) placed clearly on labeled axes"]),
        (["slope"], ["a line rising 3 units for every 2 units run, with rise and run marked"]),
        (["function", "input", "output"], ["a mapping of 1, 2, 3 to outputs, or a graph where each x has exactly one y"]),
        (["addition", "subtraction"], ["247 + 183 = 430 with regrouping, or 430 - 156 = 274"]),
        (["multiplication"], ["a 6 by 4 array making 24, or four groups of 6"]),
        (["division"], ["17 objects shared among 5 people with a visible remainder, or 156 divided by 12"]),
        (["fraction"], ["one whole divided into 4 equal parts with 3 shaded, or a number line showing 0, 1/2, and 3/4"]),
        (["decimal", "metric"], ["2.75 meters shown as 2 ones, 7 tenths, and 5 hundredths, or metric units stepping by powers of ten"]),
        (["prime", "divisibility", "factor", "multiple"], ["the numbers 1 to 30 sorted by factor structure, or factor pairs arranged around 24"]),
        (["place value"], ["4,637 decomposed into 4 thousands, 6 hundreds, 3 tens, and 7 ones"]),
        (["measurement", "perimeter", "area"], ["a 5 by 3 field with perimeter traced and area tiled by unit squares"]),
        (["point", "line", "angle"], ["a small geometric construction with labeled point, ray, and angle measure"]),
        (["triangle"], ["a 3-4-5 triangle with sides, angles, or area made explicit"]),
        (["pythagorean"], ["a 3-4-5 right triangle with squares on each side showing 3^2 + 4^2 = 5^2"]),
        (["circle", "arc", "pi"], ["a circle with radius, diameter, central angle, and a highlighted arc"]),
        (["polygon", "tessellation"], ["regular polygons tiling a surface, with one shape fitting perfectly and another failing"]),
        (["construction", "compass", "straightedge"], ["a compass-and-straightedge construction with visible arcs and a finished geometric target"]),
        (["proof", "axiom"], ["a small chain of statements or a construction whose conclusion follows visibly from prior steps"]),
        (["unknown", "equation", "variable"], ["a balance or written statement such as x + 5 = 12 with the unknown isolated step by step"]),
        (["zero", "negative"], ["a number line showing movement through zero into negative values"]),
        (["ratio", "proportion", "percent"], ["two similar mixtures or bar lengths showing 3:4 = 6:8, or 25% of a whole"]),
        (["quadratic", "factoring"], ["x^2 + 5x + 6 split into two factors, or a rectangle whose side lengths explain factoring"]),
        (["sequence", "pattern"], ["a sequence of figures or numbers with the next term made visible by rule"]),
        (["linear"], ["a line rising 3 units for every 2 units run, with rise and run marked"]),
        (["parabola", "quadratic function"], ["a parabola with vertex and axis of symmetry clearly marked"]),
        (["exponential"], ["a doubling table or curve showing growth from 1 to 2 to 4 to 8"]),
        (["logarithm"], ["powers of 10 linked to exponents, such as 10^3 = 1000 and log10(1000) = 3"]),
        (["transformation"], ["one graph shifted, reflected, or stretched into another with arrows"]),
        (["system"], ["two lines intersecting at one point, or showing no solution and infinitely many solutions"]),
        (["angle", "radian", "degree"], ["a circle with one angle labeled in degrees and radians"]),
        (["unit circle", "sine", "cosine"], ["a point on the unit circle with cosine as horizontal and sine as vertical distance"]),
        (["trig", "triangle", "law of sines", "law of cosines"], ["a labeled triangle with side-angle correspondences visibly matched"]),
        (["polar", "vector"], ["a point described by radius and angle, or a vector decomposed into components"]),
        (["wave", "oscillation"], ["one clean sinusoidal wave with amplitude, period, and midline marked"]),
        (["limit"], ["a sequence or graph approaching a value without touching it"]),
        (["derivative", "tangent"], ["a secant line approaching a tangent line on a curve"]),
        (["integral", "accumulation", "area"], ["thin slices accumulating into area under a curve"]),
        (["differential equation"], ["a field of short direction arrows with one solution curve flowing through"]),
        (["series"], ["partial sums of a geometric series approaching a finite limit"]),
        (["probability", "chance", "sample space"], ["a fair die sample space with an event highlighted"]),
        (["counting", "combinatorics"], ["a tree diagram or slot arrangement showing how possibilities multiply"]),
        (["expected value", "random variable"], ["a game board or payoff table with outcomes and probabilities"]),
        (["binomial"], ["ten coin flips with exact success counts grouped visually"]),
        (["normal distribution", "bell curve"], ["a bell curve with mean and standard deviation marks"]),
        (["data", "statistics", "median", "mean"], ["a dot plot or box plot with center and spread labeled"]),
        (["correlation", "regression"], ["a scatter plot with a fitted line and visible positive or negative trend"]),
        (["sampling", "inference", "confidence interval"], ["a small sample feeding into an estimate with visible margin of error"]),
        (["bayes"], ["a probability tree or diagnostic test table updating a prior belief"]),
        (["matrix", "vector"], ["a grid transformed by a 2x2 matrix, with basis vectors moved"]),
        (["non-euclidean", "curvature", "spherical", "hyperbolic"], ["parallel lines on a sphere or saddle surface behaving differently than Euclid predicts"]),
        (["symmetry", "group"], ["rotations of a polygon or object arranged as a closed symmetry system"]),
        (["graph theory", "network"], ["a small network of nodes and edges with paths or bridges highlighted"]),
        (["information theory", "bit", "entropy"], ["a branching message tree or binary stream with uncertainty visually reduced"]),
        (["fourier"], ["one complex wave decomposed into simpler sine waves"]),
        (["relativity", "space-time"], ["a light clock or tilted space-time diagram showing time dilation"]),
        (["quantum"], ["a probability wave or measurement setup with multiple possible outcomes"]),
        (["godel", "incompleteness", "self-reference"], ["a self-referential statement or encoded number chain pointing back to itself"]),
        (["chaos", "logistic", "bifurcation"], ["a bifurcation-style branching pattern or two nearby paths diverging dramatically"]),
    ]
    for keywords, options in keyword_examples:
        if any(keyword in title_blob for keyword in keywords):
            return options[min(variant, len(options) - 1)]
    fallback_objective = chapter.learning_objectives[min(variant, len(chapter.learning_objectives) - 1)] if chapter.learning_objectives else ""
    if fallback_objective:
        return clean_markdown(fallback_objective)
    return f"one explicit, chapter-appropriate example for {chapter.title.lower()}"


if __name__ == "__main__":
    main()
