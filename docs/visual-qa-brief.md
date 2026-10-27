# Visual-QA reviewer brief - GetBackers Dakkanya: Jagan Fuuin!

You review contact sheets from a translated build's QA tour and give each one a verdict. Read-only on everything
except your one verdict file: no edits to the repo, no git, no subagents.

## Inputs (in your dispatch)
- A chunk file: one `id<TAB>path` line per sheet. Read every sheet in it; none may be skipped.
- Your verdict file: `work/qa/verdicts/<chunk>.tsv`.
- Optional: the original ROM's sheets (`work/qa/tour_jp/`, same ids) and `glossary.md`.

## How to look
- Read each sheet whole first. Where text is small, zoom into it with
  `python -X utf8 $SKILL/scripts/sheet.py SHEET.png --crop x,y,w,h --zoom 3 --out <scratch>.png` and read that.
- When something looks wrong, open the same id from `tour_jp/` (`sheet.py EN.png --compare JP.png`). If the
  original shows the same thing, it is the game's own behaviour: `ok`, with a note.

## Judge
An `issue` is any of:
- Japanese still visible;
- text overflowing a box, clipped by a frame, or running off screen;
- garbage tiles, wrong or missing glyphs, a strike or stray pixels across letters;
- broken line breaks: a word split mid-line, a page ending mid-sentence, a one-word last line;
- an empty box where text belongs;
- a name that differs from `glossary.md`.

Standing non-bugs, `ok` (the controller adds the game's own below):
- text still typing out, a box mid-fade or mid-scroll, a cursor caught mid-blink;
- a map or scene still loading after a warp;
- anything identical in the original's sheet. English pages don't line up with the JP sheet of the same id (English
  auto-paginates into extra boxes): look for the line across the group's `tour_jp/<group>/sheet_*.png`.
- a page ending mid-sentence on ▼ when that sentence alone is longer than one box (2 lines): the paginator
  (tools/layout.py) ends pages on sentence ends wherever that costs no extra box. A page ending mid-sentence
  where the sentence would fit on its own page is still an issue.
- `~` at line ends (Ginji, Maria and others): kept on purpose (D10).
- battle groups (`b*`): stale text from the previous line left in the box past a shorter line's end (the tour jumps
  between scripts without the game's box clear). Text that is wrong in itself is still an issue.
- English is drawn two letters per 12 px cell (digraph glyphs), so letter spacing is tight and pairs can look joined;
  only a wrong or unreadable letter is an issue.
- the save screen's TIME position and the touching stat rows on the status screen (both as in the original);
- left on purpose (D5): the takoyaki sign letters are erased, not translated (shared tiles); dot-pattern poster text
  stays Japanese;
- 55 shortened item names in the field item list, e.g. "H-Face Squid" (D8).

## Verdicts
Write your verdict file once you have read every sheet, one line per id in the chunk:
`id<TAB>ok|issue<TAB>what and where` (for an issue: which tile, which text, what is wrong).
Then return a short summary: counts, and the issues one per line.
