# Pellory Ceramics Instagram plan

A 30-day Instagram storytelling plan by Alex Mercer for the fictional one-person pottery studio Pellory Ceramics. It is written for founder June Avery and presented as a portfolio demo for people hiring a social media manager.

## Key features

- A Monday-start, 30-day calendar with daily Stories, 12 Reels, 6 carousels and a Day 26 kiln-opening drop.
- Four editorial pillars, a voice guide, six timed Reel storyboards, three illustrated carousel decks, nine captions and a seven-frame Story sequence.
- Calendar filters, storyboard playback and scrubbing, and carousel navigation. The plan content is readable with JavaScript disabled.
- A weekly measurement checklist and three tests with explicit decision thresholds.
- A static page, a US Letter print edition and a 24-page downloadable PDF.

## Rebuild

Edit [data/plan.json](data/plan.json) to change the plan. Python 3 and its standard library are enough for validation and the HTML build.

```sh
python3 tools/check_plan.py && python3 tools/build.py
python3 -m unittest discover -s tests
```

Run `python3 tools/check_plan.py --json` for the machine-readable report. Open [index.html](index.html) directly in a browser or serve the folder from any static host.

If Node and Google Chrome are installed, the build also prints [plan-print.html](plan-print.html) to `Pellory-Instagram-plan-DEMO.pdf` through `tools/make_pdf.mjs` (headless Chrome over the DevTools protocol). Without them it still writes both HTML pages and leaves any existing PDF alone; you can open the print edition and print it to US Letter yourself.

## Concept demo and fonts

Pellory Ceramics, June Avery, Quarry Bend, the account and every example post are fictional. All measurement numbers are planning targets or test thresholds. No results are claimed.

Fraunces, DM Sans and DM Mono are bundled under the SIL Open Font License, Version 1.1. See [font credits and license information](fonts/LICENSE.txt).
