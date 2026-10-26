# Decisions

The user's rulings on scope, style and trade-offs, newest last. Read before asking the user anything; if a later
decision replaces one, mark the old one "replaced by D<n>" instead of deleting it. Binding term spellings live in
`glossary.md`; this file holds the why.

| # | Date | Question | Options offered | Decision and reason |
|---|---|---|---|---|
| D1 | 2026-10-16 | Honorifics and name order | keep (-san), drop; JP or Western order | Pre-approved: dropped, relationship carried by register; given name first (Ginji Amano, Ban Mido). |
| D2 | 2026-10-16 | Romanization source for names | official art, earlier patch, Hepburn | Pre-approved: official English (Tokyopop manga / anime) > modified Hepburn, no macrons. |
| D3 | 2026-10-16 | Credits | stay Japanese, translate | Pre-approved: English. |
| D4 | 2026-10-16 | Abbreviations | engine work first (default), abbreviate | Pre-approved: engine work first, full names everywhere (digraph font + auto-pagination). |
| D5 | 2026-10-16 | Graphics text left in Japanese | none (default), list | Pre-approved: all graphics text in scope. Left: takoyaki sign letters (shared tiles, erased only), dot-pattern poster text. |
| D6 | 2026-10-16 | Specs and plans | need approval, pre-approved | Pre-approved. |
| D7 | 2026-10-16 | Publishing | publish, local only | Never push/publish/upload without the user; release = local release/getbackers-dakkanya-jagan-fuuin_en.zip (patch + README). |
| D8 | 2026-10-23 | Item names longer than the field item list allows (12 halves before the count; 55 of 346) | shorten/abbreviate, re-layout the list (engine), leave the overlap | Abbreviations allowed for those 55 names (replaces D4 for them only). Done with as little abbreviation as fits: pair cards shorten one name to its JP nickname, collectibles take a short common name (description keeps the full one). |
| D9 | 2026-10-27 | Repo layout | as is, fan-translation-template | Template docs/config (subagent types, docs/screenshots); build.py at the root, tools/ (tests.py, lua/, debug/), script/, tbl/ stay (sibling repos did the same). |
