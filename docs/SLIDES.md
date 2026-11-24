# Slide content for the organiser template (Innodata | IDEA SUBMISSION)

Copy each block into the matching slide of the mandatory template. Items marked [[...]] get filled in from
`outputs/results/summary.json` once all model runs finish.

---

## Slide 1: Title
- **Team Name:** NavProbe (solo)
- **Problem Statement:** Track 2, Visual Task Factory
- **Team Leader Name:** Akanksha Parija

---

## Slide 2: Brief about the idea
NavProbe is an automated factory that generates verifiable visual-reasoning tasks on robot navigation maps
(hospital floors) and uses them to test multimodal models.

- It draws a map (rooms, doors, furniture, a robot with a heading arrow, goals) from a random seed.
- It asks one of six kinds of question: count doors, left/right, reachable?, does the robot fit?,
  which goal is nearest by driving, is the goal visible?
- It computes the answer exactly with algorithms (BFS, configuration space, ray casting), with no model or
  human labelling involved.
- It proves the answer is visible in the image by rebuilding the map from the pixels alone.
- It scores open-weight VLMs against controls and reports where they fail.

Why it matters: VLMs are being used as high-level planners for service robots. If a model misreads a
map, the robot gets stuck, collides, or makes a late delivery.

---

## Slide 3: Opportunity / how different / USP
**How it differs from existing benchmarks (CLEVR, VQA, ChartQA)**
- Every task is **re-verified from its own pixels**: an independent decoder rebuilds the map from the PNG
  and the answer is recomputed. 1,405/1,405 tasks pass, with 0 failures.
- **Ambiguity is removed automatically**: near-ties, grazing sight lines and exact-fit doorways are rejected
  (2,385+ candidates rejected, each logged with a reason).
- **Shortcut-proof design**: answers are balanced, so a model that always says "no" scores exactly chance;
  blind (no-image) controls; minimal pairs where one change flips the answer; trap questions where the
  goal that looks nearest is not the nearest by path.

**USP:** a task factory whose validity is *proven*, not assumed. It shows not only *whether* models fail but
*how*: answer collapse, eyeballing instead of planning, ignoring the evidence.

---

## Slide 4: List of features
1. Procedural hospital-map generator: rooms, loops, open and closed doors, furniture, robot heading, goals
2. Six reasoning families: counting · egocentric direction · connectivity · metric clearance · path planning · occlusion
3. Two visual styles (architectural plan / ROS occupancy grid) plus an easy tier (14×14) and three standard sizes (20/28/36)
4. Pixel round-trip validator + ambiguity margins + answer balancing
5. Minimal pairs (283), style twins (222), trap questions (50% of F5)
6. Control agents: oracle (100%), random (chance), blind (no image)
7. Mutation tests: 5 kinds of deliberate corruption, 100% caught
8. Model runner (vLLM / transformers / Gemini API), resumable and cached
9. Report: accuracy with 95% bootstrap CIs, accuracy by map size, trap vs no-trap, pair consistency, style agreement, answer collapse, failure gallery
10. One-command, deterministic, Dockerised pipeline (`make all`)

---

## Slide 5: Process flow diagram
```
seed → map generator → exact answer (BFS / config space / ray casting)
     → render PNG → decode PNG → recompute answer → keep only if identical
     → balance + minimal pair + style twin → task set (1,405 tasks)
     → models (with image / blind) + oracle + random → strict JSON scoring → report + failure gallery
```
(Draw this as boxes and arrows; use `outputs/results/figures` and one sample map image.)

---

## Slide 6: Wireframes / mock diagrams
Use real outputs instead of mock-ups:
- One sample map in each style (plan and ROS), with its question and answer
- A minimal pair side by side (door open → "yes", door closed → "no")
- One failure-gallery strip (`outputs/results/gallery/F5_nearest_by_path.png`)

---

## Slide 7: Architecture diagram
```
navprobe/
  mapgen.py   → layouts (BSP), doors, furniture, markers
  geometry.py → BFS, configuration space, line of sight, room/door analysis
  render.py   → two styles          decode.py → pixels → map (independent)
  families.py → F1–F6 questions, answers, margins, minimal pairs
  generate.py → balancing, validation, tiers → tasks.jsonl + images
  verify.py   → re-checks every task from its PNG
  evaluate.py → oracle / random / vLLM / HF / Gemini, cached + resumable
  report.py   → scoring, CIs, collapse, pairs, twins, figures
  gallery.py  → failure gallery
Compute: MacBook (generation, report) · Plaksha HPC, RTX PRO 6000 Blackwell slices (model inference)
```

---

## Slide 8: Technologies used
Python 3.12 · NumPy · SciPy · Pillow · matplotlib · pytest · vLLM · Hugging Face transformers ·
Slurm (Plaksha HPC) · Docker · Claude Code (development assistant, declared).
Models: Qwen2.5-VL 3B/7B, Qwen3-VL 4B/8B/32B, InternVL3.5 8B [[final list]].

---

## Slide 9: Estimated implementation cost
- Generation, verification and reporting: **₹0**. Runs on a laptop in about 6 minutes; no external data or API.
- Model evaluation: about [[N]] GPU-hours on an institutional HPC (24/48 GB GPU slices); no paid API.
- Scales linearly: 10× more tasks costs 10× generation time (minutes) and 10× inference.

---

## Slide 10: Results and deliverables
**Results** [[fill from summary.json]]
- Headline: [[best model]] reaches [[x%]] overall vs [[chance]] chance; the 3B model scores at chance (44% vs 43% random)
  with **83% answer collapse** (it picks one favourite answer per question type).
- [[Size ladder: 4B → 8B → 32B]]
- [[Trap questions: accuracy when the looks-nearest goal is wrong vs right]]
- [[Easy tier vs large maps]]
- Minimal pairs: 3B gets both right only 7% of the time (random: 28%), so it does not use the visual evidence.

**Deliverables:** public GitHub repo · 1,405 tasks with images and evidence · validation logs (tests,
verification report, rejection log, controls) · TECHNICAL.md + LIMITATIONS.md · demo video
