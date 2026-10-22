# Translator brief - item and equipment tables (script/items.json)

Read `docs/translator-brief.md` first (style, glossary, output rules). Here you edit `script/items.json` itself:
fill `name_en` and `text_en` for every record, using the Edit tool (or Write the whole file once). Keep the JSON
valid (UTF-8, `\n` inside strings for a line break). Do not touch other fields.

## Fields
- `name_jp` -> `name_en`: the name in the item list. HARD limit: items (id item...) 12 characters (the count is drawn
  right after; abbreviations allowed here, D8: pair cards use the JP nicknames Gin/Himi/Bane/Kazu/Emi/Juu); equipment
  (id equip...) 10 characters (a short label in a narrow slot: "Ban Shades", "Ginji Band", "Kazuki Tie").
- `text_jp` -> `text_en`: shown in the info panel. For consumables it is the effect ("HP回復小(単体)" -> "Restore some
  HP (one ally)"); for key items and cards it is the full name; for equipment it is "full name\neffect" (keep the
  line break). HARD limits: each line at most 36 characters, and all lines together at most 72 characters.
- Names already used in the dialogue (keep them): Human-Face Squid, M Oil, Gut Barley Flour, Dried Newt, Shed
  Snakeskin, Amaterasu Mask, Ban's True Voice (本音 items), Professor's Manuscript, Basement Key, Grappling Rope,
  Connecting Passage Key, ID Pass, Entry Pass, magatama (Red Magatama...), Employee ID, Ban Shades, Hevn's Earring,
  Madoka's Ribbon, Aoki Shades, Ayamine Specs, Kira Glove; 羨木 = Hishiki; ACT n -> "Act n".
- "XYのM" items (ばんぎんのM): "Ban&Ginji M" style; their text is the affinity effect ("Raises Ban & Ginji's affinity").
- Cards (カードN / 蛮&銀次ACT2): name "Card N", text "Ban & Ginji Act 2".

## Validate
`python -X utf8 tools/items_check.py` until it prints OK. Report like the main brief, short.
