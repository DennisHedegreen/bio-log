# Bio Log TID — Design Notes

## Purpose

Design a public website layer for Bio Log that makes the project readable without requiring visitors to understand the GitHub repository.

The site should show the jar, the observation quality, and the reliability of the protocol.

## Primary UI sections

### 1. Header / status panel

Suggested content:

- Bio Log TID
- A slow public observation instrument for a sealed seawater jar.
- Latest observation date
- Current status
- Total entries
- Total photos
- Current streak
- Longest gap
- Source repository link

### 2. Latest observation

Show:

- latest photo
- date
- status tag
- score card
- short note
- source log link

Important: restart baseline entries must be visibly marked.

### 3. Image viewer

Minimum controls:

- previous observation
- next observation
- open image source
- open log source

Later controls:

- compare with first image
- compare with previous image
- compare with restart baseline

### 4. Three-layer interpretation card

For each selected observation, show:

#### Jar signal

What appears to be happening in the jar.

#### Observation condition

How reliable the observation is.

Examples:

- same angle
- mobile photo
- uncalibrated
- smell tested or not tested
- single image only

#### Protocol condition

How reliable the workflow is.

Examples:

- same-day entry
- gap before entry
- mobile GitHub intake
- image normalized
- restart baseline

### 5. Timeline

Show entries and gaps.

The timeline should make dormant periods visible instead of hiding them.

Example status labels:

- START
- NORMAL
- GAP
- RESTART BASELINE
- LOW CONFIDENCE
- MOBILE INTAKE

### 6. Protocol health panel

This is the public version of the internal "Dennis, tag dig sammen-meter".

Suggested fields:

- current streak
- longest gap
- days since last observation
- logged days / total days
- image archive health
- restart count
- manual rescue entries

Suggested status labels:

- STABLE
- FRAGILE
- DORMANT
- RECOVERING
- RESTARTED

### 7. Signal relations

Do not claim causation.

Only show cautious possible relations, for example:

- color shift vs observation gap
- sediment change vs image consistency
- visible life vs surface activity
- score trend vs protocol confidence

Until enough data exists, this section should say that relation analysis is pending.

### 8. Source / method section

Show raw links:

- GitHub repository
- log file
- image file
- issue intake, if available
- generated data file, later

Method note:

Bio Log is not a laboratory measurement system. Manual scores are observer-assigned. Photos may vary in light, angle, and quality. Gaps and restarts are preserved instead of hidden.

## Visual direction

- dark background
- monospace
- thin borders
- HR green/rust accents
- raw images
- no fake laboratory aesthetic
- field instrument, not biohacker app

## MVP boundary

Build first:

1. Header/status
2. Latest observation
3. Image viewer
4. Three-layer interpretation
5. Timeline
6. Protocol health
7. Source links

Wait until more data exists before building strong graphs or correlation claims.
