PY ?= python3
OUT ?= outputs
SEED ?= 0
N ?= 100

.PHONY: all test tasks verify controls report clean

## Full offline pipeline: tests -> generate -> verify from pixels -> control agents -> report
all: test tasks verify controls report

test:
	$(PY) -m pytest -q

tasks:
	$(PY) -m navprobe.generate --out $(OUT) --per-family $(N) --seed $(SEED)

verify:
	$(PY) -m navprobe.verify $(OUT)

## Oracle (must be 100%) and random (should be chance). No GPU or API key needed.
controls:
	$(PY) -m navprobe.evaluate --tasks $(OUT) --model oracle
	$(PY) -m navprobe.evaluate --tasks $(OUT) --model random

## Scores every cached response in $(OUT)/responses (including model runs done on the HPC)
report:
	$(PY) -m navprobe.report --tasks $(OUT)

clean:
	rm -rf $(OUT)/images $(OUT)/tasks.jsonl $(OUT)/*_report.json $(OUT)/results
