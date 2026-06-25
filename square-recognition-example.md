# Square Recognition Example

This is a focused example of square recognition only.

It loads a query PNG tile, computes a compact visual descriptor, compares it with all reference tiles from `kyiv-route-google-squares`, and returns the most likely square label.

The query is intentionally modified before matching:

- central crop
- resize back to the original size

That makes the demo more realistic than a simple exact-file self-match.

## Files

- `square-recognition-example.py`
- `square-recognition-example.output.json`

## Run

```bash
/Users/afshadow/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 \
  /Users/afshadow/workspace/flight\ controller/square-recognition-example.py
```

## Expected result

For the default query `14_W-18.png`, the top recognized square should still be `W-18`, even after the query tile is cropped and rescaled.
