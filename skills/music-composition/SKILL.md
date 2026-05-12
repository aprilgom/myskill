---
name: music-composition
description: Use when the user asks to compose, analyze, revise, critique, teach, arrange, orchestrate, harmonize, reharmonize, write lyrics/toplines, explain theory, or diagnose musical problems. Trigger on concrete theory/craft questions ("what scale fits over Cm7", "write a melancholy bridge progression", "voice this chord on piano") and vague creative problems ("the chorus feels weak", "this transition is awkward", "my song sounds generic"). Do not use for DAW operation, MIDI generation, audio engineering, mixing/mastering, sound design, notation software UI, or performance pedagogy.
---

# Music Composition

A comprehensive composition skill covering music theory and compositional craft for both DAW-based and acoustic/score-based workflows. This skill does NOT handle DAW automation, MIDI generation, audio engineering, or notation software — those belong to other skills.

## Core philosophy

Composition is a series of decisions, not a list of rules to follow. When advising:

- **Frame techniques as options, not commandments.** A "rule" in voice-leading is a probability distribution that creates a certain sound. Breaking it makes a different sound, which may be exactly what's wanted. Always know which sound the user is after.
- **Explain *why* a technique produces its effect.** Cite the perceptual or contextual reason — "the leading tone resolves up because the half-step gravity is strong and the ear expects closure". This lets the user reason about novel situations rather than memorize rules.
- **When the user describes a feeling or goal, give multiple options.** "I want this to feel uneasy" has many valid solutions (tritone substitution, modal mixture, polychords, rhythmic displacement). Offer 2–4 with their trade-offs rather than picking one.
- **Be concrete.** "Try a iv chord" beats "try modal mixture." "Voice this with the 3rd on top in close position, low E in the bass" beats "make it tighter." Always give the user something they can play.
- **Respect genre conventions but don't be enslaved by them.** A "wrong" choice in jazz might be perfect in indie rock. Always know which genre frame the user is operating in.
- **When the user describes a vague creative problem, translate it before answering.** "The chorus feels weak" decomposes into: melodic range, harmonic surprise, dynamic contrast, arrangement density, rhythmic activity, lyric/syllable density. Diagnose, then prescribe.
- **Don't moralize about technique.** Parallel fifths aren't immoral. They're a sound. Bach avoided them; Debussy used them; the user's track might want them.

## What this skill does NOT cover

- **DAW operation** — keyboard shortcuts, plugin parameters, automation lanes (separate skill).
- **MIDI file generation or direct manipulation** — handled elsewhere.
- **Audio engineering / mixing / mastering / sound design** — frequency-aware *composition* is in `production-aware/`, but EQ, compression, and synthesis decisions are out of scope.
- **Music history trivia** unconnected to composition technique. (Stylistic conventions of a period ARE in scope.)
- **Music notation software operation** (Sibelius, Finale, Dorico, MuseScore UI).
- **Performance pedagogy or instrumental exercise routines** for becoming a player. Composition-facing playability and idiomatic writing are in `references/instrument-idiom/`, but this skill does not replace a private teacher, method book, or technique practice plan.

## Workflow

1. **Classify the ask and boundary.** Confirm this is composition, theory, songwriting, arrangement, orchestration, analysis, critique, teaching, or reference-driven composition. If it is DAW operation, MIDI file generation, mixing/mastering, sound design, notation software UI, or performance pedagogy, say this skill is out of scope and answer only any composition-facing part.
2. **Identify the musical frame.** Surface the user's stated goal and the likely underlying musical problem. Name the genre frame when known. If genre, level, or project constraints would materially change the answer and cannot be safely inferred, ask one concise question.
3. **Read `references/00-navigation.md`.** Use it to choose the smallest useful context set. For most requests, load 1-3 files. If the route points to 5+ files, narrow the dominant issue first.
4. **Load references progressively.** Use `references/` for concepts and judgment. Use `assets/` for short lookups, templates, chord catalogs, voicing tables, diagnostic checklists, and response shapes.
5. **Produce concrete musical options.** Translate theory into playable or writable output: chord names, Roman numerals, notes, voicings, rhythm, form map, lyric/prosody edits, or arrangement moves. Prefer 2-4 options with trade-offs over one rule.
6. **State assumptions and adjacent risks.** Mention genre assumptions, range/playability limits, copyright/style-cloning boundaries, cultural specificity caveats, or currentness requirements when they affect the answer.
7. **Stop at the useful depth.** Give enough rationale for the user to act, then stop before turning the answer into a survey.

## Navigation

The bulk of this skill lives in `references/`. **Always start by reading `references/00-navigation.md`** — it maps user requests to the specific reference files you need.

Don't load every reference. Load only what's directly relevant to the current question. For most requests, 1–3 reference files is enough. If you would need 5+, the question is too broad — narrow it first, or pick the dominant aspect and answer that.

For quick lookups (chord progression catalogs, mode formulas, voicing libraries), check `assets/`. Asset files are short and can be quoted directly. Reference files should be synthesized, not quoted.

## Top-level structure

```
references/
├── 00-navigation.md              ← Read this first, every time
├── fundamentals/                 ← Pitch, intervals, scales, rhythm, notation, prosody
├── harmony/                      ← Chords, voice leading, modulation, jazz, modal, reharm
├── melody/                       ← Construction, motivic development, phrase structure
├── counterpoint.md               ← Species → tonal → fugue
├── rhythm-groove/                ← Rhythmic devices, groove/feel, odd meters
├── form/                         ← Classical & popular forms, narrative
├── orchestration/                ← Instruments, voicing, texture, density, choral writing
├── instrument-idiom/             ← Composition-facing playability for piano, guitar, bass, drums, strings, winds, brass, vocals
├── genres/                       ← Per-genre conventions (incl. Korean traditional, C-pop / SE Asian, Latin, Afrobeats, MENA, South Asian, country, metal, gospel, Brazilian, game, media/commercial)
├── songwriting/                  ← Lyrics, hooks, topline
├── analysis.md                   ← Roman numeral, form, Schenker, set theory
├── techniques/                   ← Theme & variation, 20th C., constraint-based, microtonal, algorithmic / AI-assisted
├── production-aware/             ← Pre-production, composition-mix interface, energy
├── research/                     ← Web trends, user listening context, regional trend evolution, reference digging, style/copyright guardrails
├── creative-workflows/           ← Musical brainstorming, answer calibration, revision loops, and user-agent collaboration patterns
├── validation/                   ← Release readiness, Phase B/C records, RC packaging, and prompt smoke tests
├── source-bibliography.md        ← Maintainer-facing source map and verification guide
├── workflow.md                   ← Starting, revising, hybrid-genre advising
├── critique-and-feedback.md      ← Evaluating user's existing work (critique mode)
└── teaching-composition.md       ← Pedagogy mode, learning paths, exercises

scripts/
└── music_theory_sanity_check.py   ← Validation and regression helper for maintainers

assets/
├── progressions-catalog.md
├── response-templates.md
├── diagnostic-checklists.md
├── trend-and-reference-matrices.md
├── musical-brainstorming-cards.md
├── session-brief-and-decision-log.md
├── web-search-cheatsheet.md
├── chord-symbol-ambiguity-and-parsing.md
├── scale-degree-spelling-cheatsheet.md
├── music-theory-audit-rubric.md
├── cadence-reference.md
├── modes-cheatsheet.md
├── intervals-and-scale-formulas.md
├── jazz-voicings.md
├── form-templates.md
└── chord-symbol-conventions.md
```

## Validation

For normal composition answers, validate by checking that the response:

1. answers in the user's genre frame or names the assumption,
2. includes concrete musical material rather than only abstract advice,
3. avoids protected-expression copying and living-artist cloning,
4. does not invent current trend claims without web research,
5. stays out of DAW, mixing, MIDI-generation, notation-UI, and performance-pedagogy scope.

For maintainer validation or release work, run:

```bash
python3 scripts/music_theory_sanity_check.py
```

Then use `references/validation/prompt-smoke-tests.md` for behavioral QA and record partial/full results in `references/validation/phase-c-smoke-test-results.md`.

## Output Format

Match the user's requested shape first. When no shape is specified, prefer:

1. **Direct answer or diagnosis.** Name the musical problem or technique in one short paragraph.
2. **Concrete actions.** Give 2-4 playable/writable options with chords, notes, rhythm, form, lyric edits, voicings, or arrangement moves.
3. **Trade-offs and assumptions.** Briefly explain why each option works, what genre assumption it uses, and what to avoid.
4. **Next step.** If useful, suggest the single highest-value next musical test rather than a broad menu.

For critiques, lead with findings ordered by musical impact, then give revision actions. For teaching requests, give a plain explanation, one playable example, and one exercise.

## Notation conventions

Use these consistently throughout the skill:

- **Chord symbols** (lead-sheet / jazz style): `Cmaj7`, `Dm7`, `G7♭9`, `F♯dim7`, `B♭/D` (slash chord), `Cmaj7♯11`.
- **Roman numerals**: capital = major triad, lowercase = minor; `°` = diminished, `+` = augmented; arabic for inversions and 7ths (`I`, `vi`, `V7`, `ii⁶`, `V⁶/⁵`, `vii°⁷`, `iiø7`); `♭` and `♯` prefix for chromatic alterations of scale degree (`♭VI`, `♯iv°`); `/` for tonicization (`V/V`, `V7/vi`).
- **Pitches**: scientific pitch notation when register matters (C4 = middle C); plain letter names when unambiguous. Sharp = `♯`, flat = `♭`, double-sharp = `𝄪`, double-flat = `𝄫`.
- **Intervals**: `m2 M2 m3 M3 P4 A4 d5 P5 m6 M6 m7 M7 P8`; "tritone" acceptable when style is informal.
- **Scale degrees**: `^1 ^2 ^3 ...` when concise; "tonic / supertonic / mediant / subdominant / dominant / submediant / leading tone" in prose.
- **Tempo**: BPM (`120 BPM`); `♩=120` when discussing notation.

## Genre framing — always required

The same musical question has different answers in different genres. Before applying any technique, identify the genre frame and route through the genre table in `references/00-navigation.md` when genre affects the answer.

If the user hasn't named a genre and context doesn't make it obvious, ask when the missing frame would materially change the advice. Don't default silently — you'll give wrong-feeling advice.

## Extensibility

This skill is designed to grow. To add new content:

1. **New genre or sub-genre**: add a descriptive file under `references/genres/`, then update `00-navigation.md`'s genre table.
2. **New technique**: add to the most relevant existing folder, or create a new sub-folder if the topic is large enough to warrant 3+ files.
3. **New cheatsheet / matrix asset**: add to `assets/`, update `00-navigation.md`'s asset map.
4. **New instrument idiom**: add a descriptive file under `references/instrument-idiom/`, then update `instrument-idiom/overview.md` and `00-navigation.md`.
5. **New current-research workflow**: add to `references/research/`, include a snapshot note, update `00-navigation.md`, and link from related genre files.
6. **New user-agent creative workflow**: add to `references/creative-workflows/`, update `00-navigation.md`, and add quick templates in `assets/` if the workflow benefits from reusable cards. Use `creative-workflows/answer-calibration.md` for bounded variation, answer length, and loading discipline.
7. **New validation / release-readiness file**: add to `references/validation/`, update `00-navigation.md`, `RELEASE-ROADMAP.md` if relevant, and add expected-file checks when it becomes release-critical. Ship `KNOWN-LIMITATIONS.md` or include its caveats in release validation reports.

When adding files, keep them under ~600 lines (split if longer), one topic per file, descriptive names. Always update `00-navigation.md` so the agent can find new content.

Keep expansion notes, release decisions, and long project history in `RELEASE-ROADMAP.md`, `MAINTENANCE.md`, release notes, or validation files instead of this always-loaded skill body. Future additions should prioritize prompt smoke tests, deeper regional genre idioms, instrument-family expansions where needed, style-specific reference libraries, and stronger automated validation.

## Honesty about gaps

If a user asks about a topic this skill doesn't yet cover, say so explicitly: "This skill doesn't have a dedicated reference for [X] yet — I'll work from general principles and flag what I'm uncertain about." Then do that. Don't fabricate confident answers from gaps.
