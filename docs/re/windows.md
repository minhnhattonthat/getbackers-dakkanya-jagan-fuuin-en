# Width gate (measured in the marker build, MesenCE 2.2.1)

Units: halves = 6 px English letters (two per 12 px glyph cell).

| Kind | Where | Limit | Measured |
|---|---|---|---|
| msg (8000000A/B) | dialogue box, portrait or not | 36 halves x 2 lines per box; more lines become extra boxes | yes: 18 cells, page arrow sits in cell 19 of line 2 |
| name (80000008) | name tag above the box | 12 halves | yes: 6 cells |
| prompt (A0000001) | question line under a choice | 36 halves, 1 line | yes |
| choice (8000000C) | choice window | 34 halves; build widens the window (x/w args, 8 px tiles) | yes |
| bline / bname (9F000004, A0000002) | battle cut-in | 34 / 24 halves (provisional) | not yet: needs a battle scene |
| bank | battle messages, menus | per use, to do | not yet |
