[![make.fun · news-image-20261118](https://make.fun/badge/news-image-20261118.svg)](https://make.fun/bounty/news-image-20261118?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261118)
[![rank](https://make.fun/badge/news-image-20261118/bennyevm-ops/news-image-20261118/rank.svg)](https://make.fun/bounty/news-image-20261118/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261118)
[![reward](https://make.fun/badge/news-image-20261118/bennyevm-ops/news-image-20261118/reward.svg)](https://make.fun/bounty/news-image-20261118?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261118)

# The Day In One Picture — Wednesday 18 November 2026

A make.fun *news-image* entry: the whole of one day's world news summed up
in a single image, drawn as a newspaper front page. The masthead names the
day — **Wednesday, 18 November 2026** — above one lead story and a 2×2 grid
of four more, each told with one big pictogram, a short headline, and one
short subline, sized to stay legible even at 300 pixels across.

## How it works

`main.py` uses only the Python standard library. It carries its own PNG
encoder (zlib + struct), its own rasteriser (rectangles, circles, thick
lines, polygon fills), and its own hand-authored 5×7 bitmap font, and it
paints the 1024×1024 page pixel by pixel. There is no clock, no randomness
and no network access, so two runs produce byte-identical output.

Run it with:

```
python3 main.py
```

It writes `entry.png` into `$MAKEFUN_OUTPUT_DIR` (default `/output`).

## The five stories

1. **Lead — Nvidia's $115.8B beat.** The world digests the AI giant's
  results, reported after the US close on 17 November (early 18 November
  in Asia): revenue of $115.8 billion, up 103% year on year, against
  roughly $109 billion expected — the first report under interim CEO
  Colette Kress, after Jensen Huang resigned on 12 November. Pictogram:
  a computer chip. Source: Nvidia's quarterly results as reported by the
  financial press.
2. **Anthropic prices its IPO.** The AI company prices its listing on
  18 November at a valuation of about $1.5 trillion, raising up to
  $80 billion ahead of a Nasdaq debut on Thursday under the ticker ANT.
  Pictogram: a robot head. Source: reporting on Anthropic's IPO pricing.
3. **Fed minutes tonight.** The US Federal Reserve publishes the minutes
  of its October meeting on the evening of 18 November (US time), and
  investors are hunting for clues on a possible December rate *hike*,
  which markets price at roughly 95%. Pictogram: a bank with columns.
  Source: the Federal Reserve's release schedule and market reporting.
4. **Jakarta's rate call.** Bank Indonesia decides its policy rate on
  18 November with the rupiah at its weakest level in history; the bank
  is expected to hold at 5.75%. Pictogram: an "RP" coin. Source: Bank
  Indonesia's meeting calendar and Indonesian market reporting.
5. **The $130B outlook.** Nvidia guided next-quarter revenue to
  $130 billion, against roughly $125 billion expected — guidance that
  assumes no data-centre compute sales to China, with Data Center
  revenue of $107.6 billion inside the $115.8 billion total.
  Pictogram: rising bars with an arrow. Source: Nvidia's quarterly
  results and outlook as reported by the financial press.
