# NavProbe

**A factory of verifiable visual-reasoning tasks on robot navigation maps.**
Innodata AI Hackathon, Track 2 (Visual Task Factory).

Hospitals and warehouses are starting to use vision-language models (VLMs) as high-level planners for
service robots: the model looks at a floor map and decides where the robot can go. NavProbe measures
whether those models can actually read a map. It draws hospital floor maps, asks questions whose answers
it computes exactly (shortest paths, reachability, robot clearance, line of sight), proves that every
answer is visible in the image, and scores models against controls.

## Quick start (offline, no GPU, no API key)
```bash
pip install -r requirements.txt
make all          # tests -> generate 600+ tasks -> verify from pixels -> oracle/random controls -> report
```
or with Docker:
```bash
docker build -t navprobe . && docker run --rm -v "$PWD/outputs:/app/outputs" navprobe
```
The same seed always produces byte-identical images and tasks (`tests/test_pipeline.py::test_deterministic`).

## What a task looks like
Each task is a PNG map, a question, a fixed answer format and the exact answer, plus the evidence used.
```json
{"task_id": "F5-00412", "family": "F5_nearest_by_path", "style": "plan", "size": 28,
 "question": "Which goal is closest to the robot by DRIVING distance, not straight-line distance?",
 "answer": "B",
 "evidence": {"path_len": {"A": 41, "B": 29, "C": 37}, "straight_line_nearest": "A", "trap": true}}
```

## Six reasoning families
| Family | Question | Reasoning tested | Why an error matters |
|---|---|---|---|
| F1 count doors | How many open doorways lead out of the robot's room? | perception + counting, ignoring closed doors | wrong exits, so wrong routes |
| F2 left/right | Is goal A on the robot's left or right? | egocentric frame transform | the robot turns the wrong way |
| F3 reachable? | Can the robot drive to goal A? | topology / connectivity | the robot gets stuck behind a closed door |
| F4 fits? | Can a 2x2 robot get to goal A? | metric comparison of footprint vs doorway | collision in a narrow doorway |
| F5 nearest by path | Which goal is nearest by driving distance? | path planning vs straight-line heuristic | wasted trips, late deliveries |
| F6 line of sight | Is goal A visible from the robot? | geometry / occlusion | the robot assumes it can see a patient or obstacle that is hidden |

## How validity is guaranteed
1. **Answers by algorithm.** BFS, configuration-space search, ray casting. Unit-tested on hand-built maps.
2. **Pixel round-trip.** `decode.py` rebuilds the map from the PNG using only pixel colours, and the answer is
   recomputed from that. A task is kept only if both match. `make verify` re-checks the whole set.
3. **Ambiguity margins.** Near-ties are rejected (and logged with a reason): path lengths within 20%,
   goals within 30 degrees of straight ahead or behind, sight lines that graze a corner, and doorways that the robot exactly fits.
4. **Balanced answers.** Every family's base tasks are balanced across answer choices.
5. **Controls.** Oracle (reads the key) = 100%, random = chance, blind (text only, no image) ≈ chance.
6. **Mutation tests.** Flipped answer keys, erased doorways, moved goals, swapped labels and flipped headings
   are all caught (`tests/test_pipeline.py`).

## Variation, beyond rewording
- Six families covering different kinds of reasoning, at three map sizes (20, 28, 36 cells per side).
- **Minimal pairs:** the same map with one change (one door closed, heading reversed, smaller robot) that flips the answer.
- **Trap questions (F5):** in half the tasks, the goal that *looks* nearest is not the nearest by path.
- **Style twins:** the same scene in two visual styles (architectural plan and ROS occupancy grid).

## Running models
See [hpc/README.md](hpc/README.md). Backends: vLLM, transformers, Gemini API. Responses are cached per task,
so runs resume after interruption and the report can be rebuilt offline.

## Repository layout
```
navprobe/  mapgen.py  geometry.py  render.py  decode.py  families.py
           generate.py  verify.py  evaluate.py  report.py
tests/     geometry, pipeline (round-trip, determinism, mutations), scoring
hpc/       Slurm script + instructions
outputs/   tasks.jsonl, images/, generation_report.json, verification_report.json,
           responses/ (cached model replies), results/ (summary, figures)
```
