# Bio Log

Bio Log is a public observation log of a sealed glass container with seawater.

The goal is simple: observe slowly, document consistently, and only write larger notes or articles when something actually changes or becomes interesting enough to analyze.

This repository is the archive and workflow layer for the project. It stores dated observation notes, dated photos, and the small script used for local daily logging.

## Structure

- `incoming/` — local raw image drop zone before sorting
- `logs/` — dated observation notes
- `images/` — photos grouped by date
- `bio-log.py` — interactive daily logging script
- `process-mobile-issue.py` — processor for GitHub mobile issue photo intake
- GitHub Issues — temporary mobile photo intake during the low-friction mobile workflow

## Daily log format

Each daily entry uses the same basic structure:

- date
- six observation scores
- photo reference
- short notes
- notable event, if any

The current score fields are:

- Water clarity
- Visible life
- Smell intensity
- Surface activity
- Sediment / bottom change
- Color shift

Scores are written from `1/10` to `10/10`.

## Local workflow

1. Take one or more photos.
2. Drop raw image files into `incoming/`.
3. Run `./bio-log.py`.
4. Answer the daily prompts.
5. Select which incoming files belong to the entry.
6. Let the script move and rename them automatically.
7. Optionally commit and push to GitHub.

Each run creates or updates:

- `logs/YYYY-MM-DD.md`
- `images/YYYY-MM-DD/01.jpg`
- `images/YYYY-MM-DD/02.jpg`
- etc.

## Mobile workflow

GitHub Issues can be used as a temporary mobile photo drop zone.

A mobile entry issue should contain:

- the date or `today` in the title
- one or more uploaded photos
- short notes, if needed
- smell score, if smell was actually tested

Issues are not the final archive. They are only an intake method.

A processed mobile issue should eventually become normal repository files:

- `images/YYYY-MM-DD/01.jpg`
- `logs/YYYY-MM-DD.md`

After processing, the issue can be closed or marked as processed.

## Processing a mobile issue locally

The mobile issue processor reads a GitHub issue, finds uploaded image attachments, downloads them, saves them into the dated `images/` archive, and updates or creates the matching daily log.

Basic dry run:

```bash
python3 process-mobile-issue.py 1 --dry-run
```

Process issue `#1` and update the existing log:

```bash
python3 process-mobile-issue.py 1 --date 2026-06-11
```

Process, commit, push, comment on the issue, and close it:

```bash
GH_TOKEN=your_token_here python3 process-mobile-issue.py 1 --date 2026-06-11 --commit --push --comment --close
```

A token is only required for private attachments, commenting, closing issues, or authenticated API access.

## Restart baseline

The `2026-06-11` entry is a restart baseline after a dormant period.

All scores were set to `5/10` as a declared neutral reference point. This does not mean that all biological conditions were precisely measured as medium. It means the observation system was restarted without a properly calibrated comparison baseline.

Future entries should be compared against this restart point unless a better calibrated baseline is established.

## Gaps

Missed days should not be backfilled as if they were observed.

If the log stops, the gap remains part of the record.

## Notes

- The script is local-first.
- GitHub push is optional at the end of each local run.
- Mobile issue intake is temporary until the image can be processed into the normal `images/` archive.
- The script assumes the repo is already connected to a GitHub remote.
