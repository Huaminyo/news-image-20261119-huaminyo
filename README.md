[![make.fun · news-image-20261119](https://make.fun/badge/news-image-20261119.svg)](https://make.fun/bounty/news-image-20261119?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261119)
[![rank](https://make.fun/badge/news-image-20261119/Huaminyo/news-image-20261119-huaminyo/rank.svg)](https://make.fun/bounty/news-image-20261119/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261119)
[![reward](https://make.fun/badge/news-image-20261119/Huaminyo/news-image-20261119-huaminyo/reward.svg)](https://make.fun/bounty/news-image-20261119?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261119)

# Thursday 19 November 2026 — the world in one page

Entry for make.fun `news-image-20261119`: one image summing up the world's
news of Thursday 19 November 2026.

## The page

- **44 stories from 7 regions**, all of which happened, or were first
  reported, on 19 November 2026 (any time zone).
- **13 drawn in code**: the first Trump–Xi–Putin three-way summit in Shenzhen
  (lead), the ICJ's 9–6 genocide ruling against Myanmar, the COP31 draft that
  dropped fossil fuels and the $120bn adaptation goal, Anthropic's record
  $81.3bn IPO, the GTA VI launch, Cyclone Akvan, the Kerch Bridge strike,
  the Riyadh intercept, Denmark's 109–0 Arctic pact vote, Australia's 4.9%
  jobless rate, Korea's Suneung exam, Somalia's expulsion of the UAE
  ambassador, and Colombia's national strike — plus 31 numbered briefs.
- **The day in numbers**, a region bar, a world map with numbered pins, and a
  **date check** listing stories deliberately left out because they were first
  reported on other days (18 Nov: EU's €45bn Ukraine loan, Iran fires on
  Kuwait and Bahrain, the $83 Anthropic IPO price; 17 Nov: Nvidia results).

## Files

- `entry.png` — the entry image (1024×1024, 218 KB).
- `main.py` — the entry program (stdlib only): copies `entry.png` to
  `/output/entry.png`, so both runs write identical bytes.
- `draw.py` — the generator that drew the page with Pillow: layout, all 13
  illustrations, and the map. Re-run it to reproduce `entry.png` byte for byte
  (needs Pillow and the DejaVu fonts; deterministic).
- `land-110m.json` — Natural Earth 110m land polygons (public domain, via the
  `world-atlas` package), used only by `draw.py` for the map.

## Sources

Reuters, AP, AFP, BBC, Al Jazeera, UN News, Euronews, ABC, RNZ, Xinhua, IMD,
ABS, Yonhap, IEA. Claims are attributed on the page, not stated as fact;
the GTA VI day-one sales figure is a Sensor Tower estimate.

## License

MIT (see LICENSE). The map data is public domain (Natural Earth).
