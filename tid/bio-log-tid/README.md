# Bio Log TID

Bio Log TID is the planned website/viewer layer for the Bio Log project.

The repository root remains the source archive: dated logs, images, issue intake, and processing scripts. This folder is for designing and later building the public TID interface that can make the Bio Log readable as an instrument.

## Working definition

Bio Log TID is a small public observation instrument for viewing a sealed seawater jar over time.

It should show three layers at once:

1. **Jar** — what appears to be happening in the water system.
2. **Observation** — how reliable the photo/log/score is.
3. **Protocol** — whether the logging system itself is working.

The internal joke-name for the third layer is the "Dennis, tag dig sammen-meter". In the public UI this should be framed as protocol discipline or protocol health.

## Current design direction

Version 0.1 should be an observation viewer, not a fake science dashboard.

It should include:

- latest observation
- image viewer
- observation score card
- three-layer interpretation card
- timeline with gaps
- protocol health panel
- source links
- method note

Graphs and correlations should be prepared for, but not oversold before enough data exists.

## Design principle

Gaps are data.

A weak baseline is data.

A restart is data.

The tool should not hide missing observations. It should make the condition of the observation protocol visible.
