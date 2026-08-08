# Apartment Listing Scraper & Notifier

Continuously scans rental listings, keeps the ones that match your criteria
(budget, city/neighborhood, furnished, square meters, rooms), deduplicates them,
sorts by date, and sends you a **WhatsApp message** for every new match.

- **Source (today):** [Yad2](https://www.yad2.co.il/realestate/rent) — Israel's
  main rental site.
- **Notifications:** WhatsApp Cloud API (same credentials as the root project).
- **Runs as:** a scheduled background script that polls on an interval.
- **Extensible:** each source is a plug-in (`scrapers/`), so Facebook groups /
  Marketplace or other sites can be added later without touching the pipeline.

---

## Setup

```bash
cd apartments

# 1. One-time setup: creates the venv, installs deps, copies config templates.
bash setup.sh

# 2. Fill in your WhatsApp credentials.
nano .env

# 3. Edit your search criteria and Yad2 location codes.
nano config.yaml

# 4. Test without sending anything.
.venv/bin/python run_once.py --dry-run

# 5. Run for real (stores results, sends WhatsApp for new matches).
.venv/bin/python main.py
```

---

## Configuration

### `.env` — WhatsApp credentials

The same three variables as the root WhatsApp bot. See the root `README.md` for
how to get them from the Meta developer console.

```
WHATSAPP_API_URL=https://graph.facebook.com/v19.0/YOUR_PHONE_NUMBER_ID/messages
WHATSAPP_TOKEN=YOUR_ACCESS_TOKEN_HERE
RECIPIENT_PHONE=972501234567
```

### `config.yaml` — what to search for

Copy from `config.example.yaml`. Two parts:

- **`yad2:`** — the numeric location codes Yad2 filters by. To find yours,
  browse [yad2.co.il/realestate/rent](https://www.yad2.co.il/realestate/rent),
  apply the city/neighborhood filters you want, and read the codes off the URL
  query string (e.g. `?city=5000&neighborhood=1483`).
- **`search:`** — your personal criteria (price, rooms, sqm, furnished,
  keywords). These are applied locally to every listing, so they work the same
  for any future source too.

`furnished` can be `true` (only furnished), `false` (only unfurnished), or
`null` (any). When a listing doesn't state furnished status, whether it still
counts is controlled by `notify_unknown_furnished`.

---

## How it works

```
scrapers/*  →  scrape listings  →  matcher  →  SQLite (dedup + notified flag)  →  WhatsApp
```

1. Each scraper in `scrapers/` returns normalized `Listing` objects.
2. `matcher.py` keeps only the ones that satisfy `config.yaml`, newest first.
3. `db.py` (SQLite, `listings.db`) records what's been seen and what's been
   notified, so **you're never messaged about the same listing twice**.
4. `notifier.py` sends a WhatsApp message per genuinely new match.
5. `main.py` repeats this on the `poll_minutes` interval.

---

## Project structure

```
apartments/
├── main.py              # scheduled runner (poll + notify loop)
├── run_once.py          # one-shot CLI (--dry-run supported)
├── pipeline.py          # scrape → match → store → notify
├── models.py            # Listing schema
├── db.py                # SQLite storage, dedup, notified flag
├── matcher.py           # criteria filtering + date sort
├── notifier.py          # WhatsApp formatting/sending
├── scrapers/
│   ├── base.py          # BaseScraper interface (plug-in point)
│   └── yad2.py          # Yad2 scraper
├── config.example.yaml  # search-criteria template
├── .env.example         # WhatsApp credentials template
├── requirements.txt
└── setup.sh
```

---

## Notes & limitations

- **Yad2 bot protection.** Yad2 sits behind PerimeterX. The scraper uses
  browser-like headers, which is fine for light personal polling. If Yad2 starts
  returning HTML challenge pages instead of JSON, you'll see a warning in the
  log; the fallback is to fetch the feed via Playwright (Chromium is available)
  and reuse the same parsing.
- **Facebook is intentionally not included yet.** Meta removed API access to
  public-group posts, so it needs browser automation (fragile, against ToS) or a
  paid scraper. The `BaseScraper` interface is ready for it — adding a source is
  one new file in `scrapers/` plus one line in `scrapers/__init__.py`.
- Be a good citizen: keep `poll_minutes` reasonable (default 15) so you're not
  hammering any site.
