# Translator brief - string bank (battle, menus, sound test, credits, database)

Read `docs/translator-brief.md` first: style, glossary, voices and output rules are the same. Differences:

## Input: `work/tl/<batch>.tsv` (batches k01..k11)
`id<TAB>context<TAB>bank<TAB>max Nch<TAB>Japanese`. The context column says where the string appears; it replaces
the speaker column. Leading/trailing alignment spaces were removed: write only the text (the build re-aligns).

## Limits are HARD
`max Nch` = English characters (letters, spaces, punctuation) the field can show; it is the width the Japanese used.
If the natural translation is too long, use a shorter natural wording (synonym, drop articles, "&" for "and"),
never a truncated word. If it truly cannot fit, write your best fit and report `LONG: id`.

## Kinds of strings
- Battle message fragments are glued straight after a name or a number: 「蛮」+「は毒をうけた！」 -> "Ban" + "_was
  poisoned!". Start with `_` (underscore) where a space must follow the name; it becomes a space.
  `EXP` / `入手！` style fragments: make "[number] EXP" + "_obtained!" read naturally.
- Speaker tags in battle voice lines: 「蛮:」 -> "Ban:".
- Skill and item names: Title Case, glossary names; moves keep the style used in the dialogue batches
  (薔玉の楯 -> Rose Bead Shield, 秋雨 -> Autumn Rain, 流星 -> Shooting Star, 蛇咬/スネークバイト -> Snake Bite,
  ベノムファング -> Venom Fang, 雷帝降臨 -> Raitei Descends).
- Credits: real staff and voice actors: given name first, Hepburn without macrons (神奈延年 -> Nobutoshi Canna,
  森久保祥太郎 -> Showtaro Morikubo: use the commonly known English spelling when you know it). Konami company names
  in English (Konami Computer Entertainment Japan).
- Name readings (みどうばん): write the English name ("Ban Mido").
- Song lyrics: translate singably; keep the English phrases already in the Japanese.

## Validate / report
`python -X utf8 tools/bankbatch.py check <batch>` until OK. Report as in the main brief.
