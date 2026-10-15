# Graphics text survey

| Where | Data | Status |
|---|---|---|
| Title logo 奪還屋 box / 邪眼封印！ strip | BG2 8bpp tiles at 0x8505C (dumps tbl/gfx/title.*) | English ("DAKKANYA", "EVIL EYE SEALED!"), tools/gfx.py |
| Katakana ゲットバッカーズ above the logo | same BG | kept (reading aid of the logo) |
| Title copyright line | OBJ strip at 0x1B51A8 | English, tools/gfx.py |
| Act title cards 0-9 | table 0x9BADC (tiles + map), copied to free space with new tiles | English, tools/actcards.py |
| Battle command panels (攻撃, 必殺技, アイテム, 防御) and skill-name labels | built from the 12 px font at battle start; panel resources 0x306000-0x320000 (HP panels 0x3068C4, label strips ~0x307340-0x30CB3C, table 0x30D578) | Japanese (known issue) |
| Opening demo name captions | not located | Japanese (known issue) |
| Shop signs in town maps (トランプ占い, フォーチュンテラー, 新宿のババ) | map tiles | Japanese (known issue) |
