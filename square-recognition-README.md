# Square Recognition README

This folder now contains a small, runnable square-recognition set built on top of the real tiles in `kyiv-route-google-squares`.

## Files

- `square_recognition_lib.py`: shared recognition logic
- `square-recognition-example.py`: single-query example
- `square-recognition-example.output.json`: generated single-query result
- `square-recognition-batch.py`: runs recognition on every tile in the dataset
- `square-recognition-batch.output.json`: generated batch summary
- `square-recognition-batch-report.png`: visual report with query and top matches
- `square-recognition-example.md`: short note for the single-query example

## Run The Single Example

```bash
/Users/afshadow/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 \
  /Users/afshadow/workspace/flight\ controller/square-recognition-example.py
```

## Run The Batch Evaluation

```bash
/Users/afshadow/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 \
  /Users/afshadow/workspace/flight\ controller/square-recognition-batch.py
```

## What The Batch Output Contains

- `top1_accuracy`: how often the best match is the correct square
- `top3_accuracy`: how often the correct square appears in the first three matches
- `results`: per-tile predictions and top matches

## Visual Report

`square-recognition-batch-report.png` shows one row per query tile:

- the altered query tile variant
- top-1 match
- top-2 match
- top-3 match

This makes it easy to inspect both the numeric output and the visual neighbors.
