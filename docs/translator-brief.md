# Translator brief - GetBackers Dakkanya: Jagan Fuuin! (GBA, Konami 2003)

You translate part of the Japanese script of a GetBackers RPG into English for a fan patch. Shonen action-comedy:
the retrieval agents Ban Mido and Ginji Amano ("the GetBackers") take jobs in Shinjuku, always broke and hungry,
fighting sorcerers, Noh-mask demons and old rivals. Lots of banter, gags and trash talk.
Work only on the batch named in your dispatch. Do all translation yourself; do not dispatch subagents.
Repo root: H:\translation\batch\projects\getbackers-dakkanya-jagan-fuuin (run commands from there).

## Read first
1. `docs/style-reference.md` - character voices and approved example pairs. Match this voice.
2. `work/tl/terms_<batch>.txt` - binding glossary rows for this batch (full table + rulings in `glossary.md`).

## Input: `work/tl/<batch>.tsv`
`id<TAB>speaker<TAB>form<TAB>limit<TAB>Japanese`, in story order (use neighbouring lines for context).
- speaker = the name tag shown with the line ("-" = none: narration, signs, system or the player's own thoughts).
- form: `msg` dialogue box; `choice` a menu option; `prompt` the question shown with a choice; `bline` a battle
  cut-in shout (one short line).
- ` / ` separates the lines of one Japanese box: translate the box as ONE utterance and do not copy the break; the
  build wraps English itself (36 characters per line, 2 lines per box) and opens extra boxes when needed.
- limit: msg boxes take about 72 characters; longer text is allowed (it spills into another box) but keep one
  Japanese box to at most ~2 English boxes. choice/prompt/bline are HARD single-line limits (34/36/34 characters).
- The Japanese was transcribed from the game font by eye: a rare kanji may be wrong. If a line makes no sense,
  translate the obvious intent and report `UNSURE: id - glyph?`.

## Output: `work/tl/<batch>.out.tsv`, written with your file-write tool (not a shell heredoc)
`id<TAB>English`, every input id exactly once, same order. Plain ASCII: straight quotes, `...`, `--`; no tabs inside
the English, no Japanese or fullwidth characters, no `\uXXXX`. Allowed extras: ♥ ♪ ☆ (the game font has them).
Never write a line break.

## Fit / validate
- `python -X utf8 tools/fit.py "English text"` prints how a msg wraps into boxes (`--kind choice` etc. for others).
- Run `python -X utf8 tools/batches.py check <batch>` and fix every reported error until it prints OK. Warnings:
  glossary warnings are fine when a pronoun or natural omission is used; "boxes" warnings mean trim if you can.

## Style
- Faithful: keep the information and order of ideas; adapt idiom, not meaning. Don't add details the Japanese doesn't
  state; don't summarise or skip. Adapt jokes and wordplay so the gag still lands (no translator notes).
- Names and terms exactly as in the glossary; given name first; honorifics dropped (蛮ちゃん -> "Ban", 銀次さん ->
  "Ginji", 〜様 -> "Lord/Lady" only for a servant addressing a master). Never abbreviate a name or term.
- Furigana in parentheses after a name (天野　銀次(あまの　ぎんじ)) are reading aids: write the name once.
- Punctuation: 「」『』 -> "...", … -> "...", ！！ -> "!!", ！? -> "?!", ～/~ -> drop or stretch a vowel ("Baaan").
- Grunts and sound effects: English equivalents ("Ngh!", "Munch munch..."); don't romanize them.
- Swearing at TV-anime level. Keep each character's register (see the style reference).

## Consistency
Never edit `glossary.md` or any file other than your own output file. For a recurring name or term not in the
glossary, pick a form (official English if you know it, else Hepburn), use it consistently, and report it.

## Notes from earlier batches (binding)
- Edit your output only with the Write/Edit tools (no sed), as the ground rules require.
- Terms already chosen: カルタス -> Cartas; ハイパー・バトル・シンク -> Hyper Battle Sync; 気力アップ -> Spirit Up;
  綾峰先生 -> Professor Ayamine; 新宿のババ -> Hag of Shinjuku; 人面イカ -> Human-Face Squid; ルン -> Run.
- Battle skills: 風鳥院流絃術 -> "String Arts" is acceptable inside a battle cut-in only when the full form can't fit
  (the cut-in limit is hard); 薔玉の楯 -> Rose Bead Shield; 秋雨 -> Autumn Rain; 流星 -> Shooting Star;
  白扇の舞 -> White Fan Dance; 〜面の舞 -> "Okina/Kami/Otoko/Onna/Kurui/Miko Mask Dance"; 地嶽変 -> Hell Screen.
- 神門 is read Mikado (Kyosuke Mikado, Daisuke Mikado). 窪田清十郎 -> Seijuro Kubota; 清ジイ -> "Old Man Sei";
  窪ちん -> "Kubo"; カヅっちゃん -> "Kazu"; 絃巻き (Ban about Kazuki) -> "Spool Boy"; 催眠香 -> Hypno Incense;
  百獣擬態 -> Hundred Beast Mimicry; ブルマン -> Blue Mountain; ウグイス廊下 -> nightingale floor; 招き猫 -> beckoning cat;
  カギ爪ロープ -> Grappling Rope; 地下室のカギ -> Basement Key; 清十郎 -> Seijuro.
- More glyph misreads: 獄散 = 蹴散, 胤 = 脱, 菅 = 管, 綿 = 絡 (連絡), 頷 = 額, 勾 = 句 (文句), 閲 = 閉.
- 小判 -> gold coins; ジャッカル (Ban about Akabane) -> Jackal; 巫面(かんなぎめん) -> Kannagi masks (Okina, Kami, Otoko,
  Onna, Kurui, Oni); 能楽 -> Noh; てんとう虫 -> the Ladybug (Ban's car); ミスターノーブレーキ -> Mr. No Brakes;
  ウニ頭 -> urchin head; 面ヤロー -> Mask Boy; 秀夫 -> Hideo; 猿マワシ -> monkey trainer; 白ヘビのバン -> Ban the white snake
  (a pet snake named Ban: a "Ban" speaker tag can be the snake); 連絡通路キー -> Connecting Passage Key; IDパス -> ID Pass.
- MAI songs: 還らないこと -> Never Coming Back; ゲットイットオン！奪還BABY -> Get It On! Get-Back Baby;
  裏新宿……みれん -> Ura-Shinjuku... Lingering Love.
- More glyph misreads (already fixed in later TSVs): 寮 = 察, 婿 = 婚, 鵠 = 設, 諌 = 読, 瞼 = 般, 披 = 彼.
- Ginji's たれ (tare) form = "droopy" chibi Ginji ("go all droopy"). Mecha Hiruta speaks in ALL CAPS.
- Known glyph misreads in the Japanese: 責様 = 貴様 (you bastard), 閲 = 閉, 誉 = 響, 薇 = 猿 (monkey; 猿擬 = Monkey
  Mimicry), 濤 = 議, 獺 = 殲. Kira's Italian stays Italian ("Benissimo!", "Tutto chiaro?").

## Report (reply with only this)
Files written and entry count; then any lines: `NEW TERM: jp -> en`, `UNSURE: id - note`, `LONG: id - note`.
