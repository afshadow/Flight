# Tile Grid Recognition Example

This example shows two concrete operations on the real files already stored in this workspace:

1. Build square metadata from `kyiv-route-google-squares/route-squares.json`.
2. Recognize which square a PNG tile belongs to by comparing its visual descriptor with the reference tiles.

## What "building squares" means here

Each record inside `route-squares.json` already contains the information needed to build one square:

- `label`: human-readable square id such as `O-12` or `W-18`
- `filename`: the PNG file for that square
- `bounds`: north, south, east, west edges of the square
- `center`: square center point

The example script reconstructs:

- four square corners from `bounds`
- `row` and `col` indexes from the unique center latitudes and longitudes
- a preview JSON with several real squares from the dataset

## What "recognition" means here

The script loads a query PNG and computes a compact descriptor from:

- grayscale thumbnail appearance
- RGB histograms
- simple texture features from gradients

Then it compares the query descriptor to every reference square tile using cosine similarity and returns:

- the recognized square
- the nearest alternative squares

## Files

- `tile-grid-recognition-example.py`: runnable example
- `tile-grid-recognition-example.output.json`: generated output after running the script

## Run

```bash
/Users/afshadow/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 \
  /Users/afshadow/workspace/flight\ controller/tile-grid-recognition-example.py
```

You can also pass another query tile:

```bash
/Users/afshadow/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 \
  /Users/afshadow/workspace/flight\ controller/tile-grid-recognition-example.py \
  --query /Users/afshadow/workspace/flight\ controller/kyiv-route-google-squares/20_AA-21.png
```
