# Demo video script (about 4 minutes)

Record the screen with QuickTime (File → New Screen Recording) and talk over it. Keep a terminal and the
`outputs/` folder open beforehand.

| Time | Show | Say |
|---|---|---|
| 0:00–0:25 | Title slide | "NavProbe is a factory of verifiable visual-reasoning tasks on robot navigation maps. Hospitals are starting to let AI models read maps and decide where robots go, so we test whether they actually can." |
| 0:25–0:55 | Two sample maps (plan + ROS style) | "Each map is generated from a seed: rooms, open doors in amber, closed doors in red, furniture, the robot with its heading arrow, and goals." |
| 0:55–1:30 | Terminal: `make tasks` (or show `generation_report.json`) | "Six reasoning families. Every answer is computed by an algorithm. 2,385 borderline candidates were rejected automatically, each with a reason." |
| 1:30–2:05 | Terminal: `make verify`, then `pytest` | "This decoder rebuilds the map from the pixels alone and recomputes the answer: 1,405 out of 1,405 tasks pass. And the mutation tests: we break answer keys, erase doors and move goals, and every corruption is caught." |
| 2:05–2:30 | A minimal pair, side by side | "Minimal pairs: one door closed flips the answer. A model that is guessing can't get both right." |
| 2:30–3:00 | Report table: oracle / random / blind / models | "The scorer separates right from wrong: the oracle gets 100%, random gets chance, and a model with no image gets chance, so the image really is required." |
| 3:00–3:40 | Figures + failure gallery | "Findings: [[size ladder]], [[trap result]]. The 3B model collapses to one favourite answer: 95% 'right', 100% 'blocked'." |
| 3:40–4:00 | README / Docker command | "Everything runs from one command, deterministic and Dockerised, and every limitation is documented." |
