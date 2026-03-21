# bio-log

A simple public observation log of a large glass container with seawater.

The point is to observe slowly, document consistently, and only write larger articles when something actually changes or becomes interesting enough to analyze.

## Structure

- `incoming/` raw image drop zone before sorting
- `logs/` daily observation notes
- `images/` photos grouped by date
- `bio-log.py` interactive daily logging script

## Daily workflow

1. Take photos
2. Drop raw image files into `incoming/`
3. Run `./bio-log.py`
4. Answer the daily prompts
5. Select which incoming files belong to today
6. Let the script move and rename them automatically
7. Optionally commit and push to GitHub

## Prompt scales

- Water clarity: `1 = opaque`, `10 = very clear`
- Visible life: `1 = none visible`, `10 = abundant visible activity`
- Smell intensity: `1 = none`, `10 = very strong`
- Surface activity: `1 = still`, `10 = highly active`
- Sediment / bottom change: `1 = none`, `10 = major visible change`
- Color shift: `1 = none`, `10 = major visible change`

## Output format

Each run creates or updates:

- `logs/YYYY-MM-DD.md`
- `images/YYYY-MM-DD/01.jpg`
- `images/YYYY-MM-DD/02.jpg`
- etc.

## Notes

- The script is local-first.
- GitHub push is optional at the end of each run.
- The script assumes the repo is already connected to a GitHub remote.
