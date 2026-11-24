# NavProbe: technical explanation

## 1. Problem and application
Vision-language models (VLMs) are increasingly asked to reason about maps: a hospital delivery robot's
high-level planner reads a floor map and decides which room to go to, whether a corridor is blocked,
or which supply room is closest. Classical planners (A*, Dijkstra) solve those geometric questions exactly,
but when a VLM is in the loop, for example reading a map a person hands it or choosing between goals,
its spatial reasoning decides what the robot does. Errors have physical consequences: a robot sent through
a closed fire door gets stuck, a robot that misjudges a doorway width collides, and a robot that picks the goal
that *looks* closest wastes time on a medication run.

NavProbe is a factory that produces **verifiable** visual-reasoning tasks on such maps and measures how well
VLMs answer them.

**Image family:** 2-D top-down floor maps of hospital wards (rooms, corridors, open and closed doorways,
furniture, a robot with a heading arrow, labelled goals), in two styles: an architectural plan and a
ROS-style occupancy grid. Synthetic maps of this kind are not a stand-in for some other real image: robots
really do plan on rendered occupancy grids and floor plans.

## 2. Pipeline
```
seed -> mapgen (BSP rooms, doors, loops, furniture, markers)
     -> family.answer()  exact answer from the grid (BFS, configuration space, ray casting)
     -> render()         PNG in one of two styles
     -> decode()         PNG -> grid using pixel colours only
     -> checks           round-trip equality, answer recomputed from decoded map, ambiguity margins
     -> balancing        answer distribution per family; trap/no-trap split for F5
     -> minimal pair + style twin
     -> tasks.jsonl + images/        (generation_report.json logs every rejection with its reason)
evaluate (oracle | random | vLLM | transformers | Gemini; with or without the image) -> responses/*.jsonl
report  -> strict JSON parsing, exact match, bootstrap CIs, pair consistency, style agreement, figures
gallery -> worst failures per family with every model's answer
```

## 3. Design decisions
| Decision | Why |
|---|---|
| Answers come from algorithms on the grid, never from a model or annotator | Reference answers are independent of the evaluated model (judging criterion 2) |
| Separate pixel decoder, sharing no state with the generator | Proves the answer's evidence is actually present in the image |
| Ambiguity margins (path-length gap ≥ 20% and ≥ 3 cells; direction 30–150° from heading; sight lines must clear or penetrate blockers by ≥ 0.3 cell; doorways 1 or 3 cells for a 2-cell robot, never an exact fit) | Borderline tasks that a careful human could not answer reliably are excluded |
| Fixed answer formats + strict JSON parsing, exact match | Scoring is deterministic and needs no LLM judge; invalid replies are reported separately |
| Balanced answers per family | Constant guessing scores at chance |
| Controls: oracle, random, blind (no image) | Show the scorer separates right from wrong, and that the image is needed |
| Minimal pairs, style twins, F5 traps | Variation in the underlying visual relationship, not in wording; expose shortcut strategies |
| Responses cached per task | Runs resume after a Slurm time limit; judges rebuild all results offline |
| Pinned Pillow/numpy versions | Rendered PNGs are byte-identical across machines (`test_deterministic`) |

## 4. Variation strategy
| Axis | Values |
|---|---|
| Reasoning family | counting, egocentric direction, connectivity, metric clearance, path planning, occlusion |
| Map size | 20, 28, 36 cells per side (more rooms, longer paths) |
| Visual style | architectural plan / ROS occupancy grid |
| Map structure | random BSP layouts, extra doorways that create loops, closed doors, furniture |
| Minimal pairs | F2 heading reversed; F3 one doorway closed; F4 robot shrunk from 2x2 to 1x1 |
| Traps | F5: half the tasks have a straight-line-nearest goal that is not the path-nearest goal |

## 5. Validation evidence
- `tests/` has 19 tests: geometry on hand-built maps, the pixel round-trip on 60 maps × 2 styles, verification of a
  generated set, byte-level determinism, the scoring parser, and **five mutation tests** (flipped answer key,
  erased doorway pixels, erased goal, swapped goal labels, flipped heading). Every mutation is caught.
- `outputs/verification_report.json`: all 944 tasks re-verified from their PNGs, with 0 failures.
- `outputs/generation_report.json`: 2,385 rejected candidates, counted by reason.
- `outputs/results/summary.json`: oracle 100%, random at chance.
- Manual fixes: **none.** Nothing was hand-edited (see `MANUAL_FIXES.md`).

## 6. Reused components
NumPy, SciPy (`ndimage.label`, `distance_transform_edt`), Pillow (drawing and its bundled font), matplotlib,
pytest. Models are served with vLLM (fallback: Hugging Face transformers). No external dataset is used:
every map is generated.

## 7. Models evaluated
Open-weight VLMs served on Plaksha HPC (NVIDIA RTX PRO 6000 Blackwell MIG slices), temperature 0, maximum 256
new tokens, one image per prompt:
Qwen2.5-VL 3B / 7B / 72B-AWQ, Qwen3-VL 4B / 8B / 32B-FP8, InternVL3.5 8B. Each model is also run
**blind** (same prompt, no image) on the base tasks.

## 8. Tools used to build this
Claude Code (Anthropic) assisted with code and documentation. All design decisions, the domain framing
and the final review were by the author.

## 9. Reproducing
```bash
pip install -r requirements.txt
make all                 # tests, generation, verification, controls, report: offline
# model runs (GPU): see hpc/README.md, then `make report`
```
