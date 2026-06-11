# Everlane Discourse Analysis

A modular NLP pipeline measuring whether Everlane's sustainability and transparency
language has become more **concrete and accountable** over time, and whether public
discourse (consumers, media) reflects that shift.

---

## Table of Contents

- [Research Question](#research-question)
- [Background](#background)
- [Analytical Framework](#analytical-framework)
- [Time Periods](#time-periods)
- [Data Sources](#data-sources)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Setup](#setup)
- [Run Order](#run-order)
- [Methodology Notes](#methodology-notes)
- [Limitations and Future Extensions](#limitations-and-future-extensions)

---

## Research Question

> **Has Everlane's sustainability language become more concrete and accountable over
> time, and does public discourse reflect that shift?**

This project does not set out to prove Everlane is "good" or "bad." It treats the
question as an open empirical one: does the brand's own language show measurable
movement from vague aspiration toward verifiable commitment, and do consumers and
media perceive, or fail to perceive, that movement?

## Background

Everlane built its identity on **"Radical Transparency"**, publishing cost breakdowns,
naming factories, and positioning itself as the antidote to opaque fast fashion. In
2020, that positioning collided with reality: reporting surfaced unionization disputes,
a poor response to racial equity concerns during the BLM movement, and gaps in the
company's own sustainability disclosures relative to its marketing claims. The brand
spent the following years rebuilding, publishing impact reports, pursuing science-based
emissions targets, and eventually repositioning around a "clean luxury" identity,
including a 2025 brand campaign with musician Laufey.

This arc (claim, crisis, rehabilitation) is a useful natural experiment for discourse
analysis: it gives the project a clear "before," "during," and "after" to compare.

## Analytical Framework

The project borrows three concepts from international relations and corporate
accountability literature:

- **Normative claims vs. hard accountability**: voluntary corporate pledges exist in
  a "soft law" space with no enforcement mechanism (the Ruggie framework on business
  and human rights). Everlane's transparency claims are a private-sector analog.
- **Legitimacy and legitimacy crisis**: organizations construct credibility through
  language, and that credibility can collapse when claims and observed behavior
  diverge. 2020 functions as a legitimacy crisis in this sense.
- **Discourse alignment**: whether internal (brand) and external (consumer, media)
  language converge or diverge over time is itself a signal of accountability.

These frames are used to interpret the NLP outputs, not to predetermine a conclusion.

## Time Periods

| Period | Label | Date Range | Context |
|---|---|---|---|
| 1 | **Pre-controversy** | 2018-2019 | Peak "Radical Transparency" branding |
| 2 | **Crisis** | 2020-2021 | Unionization disputes, BLM fallout, leadership turnover |
| 3 | **Rehabilitation** | 2022-present | New CEO, published impact reports, "Clean Luxury" repositioning, Laufey campaign |

Three periods (rather than a simple before/after split) were chosen deliberately:
the crisis period is where language change is most likely to be visible in real time,
and collapsing it into "before" or "after" would erase the most analytically
interesting signal.

## Data Sources

| Source | Tool | What it captures | Volume (target) |
|---|---|---|---|
| Everlane's sustainability/factory pages | **Selenium** + Wayback Machine | The brand's own language, frozen at 3 points in time | 1 snapshot x 3 periods |
| Reddit (`r/femalefashionadvice`, `r/Everlane`, `r/ethicalfashion`) | **PRAW** | Consumer sentiment and discourse | up to 200 posts/subreddit |
| News coverage | **GDELT** + `newspaper3k` | External media framing and accountability reporting | up to 50 articles/period |

All sources are normalized to a shared schema:

```json
{
  "source": "everlane_site | reddit | news",
  "period": "pre_controversy | crisis | rehabilitation",
  "period_label": "human-readable label",
  "url": "...",
  "date": "...",
  "text": "..."
}
```

This standardization means every downstream analysis script is source-agnostic: it
operates on the schema, not on where the data came from.

### Why Selenium specifically

Wayback Machine snapshots of Everlane's site are JavaScript-rendered. Static
`requests` + BeautifulSoup calls don't reliably capture content that loads after page
render, so Selenium drives a real (headless) browser to ensure the archived page is
fully loaded before text extraction. Reddit and GDELT, by contrast, are accessed via
official APIs and don't need browser automation; Selenium is scoped narrowly to the
one source that actually requires it.

### Why GDELT over NewsAPI

NewsAPI's free tier only covers the last month of articles, which would make it
useless for the 2018-2019 period. GDELT is free, has no API key requirement, and
indexes global news back to 2013, making it a better fit for a multi-year historical
comparison, at the cost of needing a second tool (`newspaper3k`) to fetch full article
text from the URLs GDELT returns.

## Tech Stack

**Data collection**
- `selenium` + `webdriver-manager`: browser automation for Wayback snapshots
- `praw`: Reddit API wrapper
- `gdeltdoc` + `newspaper3k`: news article discovery and full-text extraction

**NLP / Analysis**
- `transformers` (HuggingFace): BERT-based sentiment classification
  (`distilbert-base-uncased-finetuned-sst-2-english`) and named entity recognition
  (`dslim/bert-base-NER`)
- `anthropic`: Claude API for structured discourse summarization and zero-shot
  accountability classification
- `pandas`, `nltk`, `scikit-learn`: data wrangling and keyword frequency analysis

**Presentation**
- `streamlit` + `plotly`: interactive dashboard
- `jupyter`: narrative analysis notebooks

## Project Structure

```
everlane_deepdive/
├── data/
│   ├── intermediate/         # Normalized outputs from the scraping stage
│   │   ├── gdelt_articles.csv
│   │   ├── gdelt_historical.csv
│   │   └── gdelt_news.csv
│   └── raw/                  # Raw scraper outputs
│       ├── everlane_web.csv
│       ├── gdelt_articles_usable.csv
│       ├── reddit_comments.csv
│       └── reddit_posts.csv
├── notebooks/
│   ├── 01_scraping.ipynb     # Data collection: Wayback Machine, PRAW, GDELT
│   └── 02_analysis.ipynb     # NLP analysis: sentiment, NER, keyword tracking, LLM scoring
├── analysis/                 # Modular script equivalents of notebook stages (in progress)
└── README.md
```

## Setup

```bash
git clone https://github.com/mwc2150/everlane-sustainability-analysis
cd everlane-sustainability-analysis

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt
cp .env.example .env            # then fill in your API keys
```

**Required credentials** (see `.env.example`):

- `REDDIT_CLIENT_ID` / `REDDIT_CLIENT_SECRET`: create an app at
  [reddit.com/prefs/apps](https://www.reddit.com/prefs/apps) (script-type app)
- `ANTHROPIC_API_KEY`: from [console.anthropic.com](https://console.anthropic.com)

GDELT and the Wayback Machine require no authentication.

**ChromeDriver** for Selenium is handled automatically via `webdriver-manager`: no
manual driver installation needed, but a Chrome/Chromium installation must be present.

## Run Order

The pipeline has a strict dependency order; each stage reads files written by the
previous one.

```bash
# 1. Data collection (writes to data/raw/ and data/intermediate/)
jupyter notebook notebooks/01_scraping.ipynb

# 2. NLP analysis (reads from data/intermediate/, writes to data/processed/)
jupyter notebook notebooks/02_analysis.ipynb
```

> **Before running `01_scraping.ipynb`:** verify the Wayback Machine snapshot URLs in
> the notebook's `SNAPSHOTS` list actually resolve to the intended pages for each
> period. Site structure changes mean a single hardcoded URL pattern won't necessarily
> work across all three years; check each snapshot manually first.

## Methodology Notes

**Sentiment** uses DistilBERT fine-tuned on SST-2, returning binary POSITIVE/NEGATIVE
labels with confidence scores. This is a coarse signal, intended to show directional
shifts in tone across periods and sources, not to make fine-grained emotional claims.

**NER** uses `dslim/bert-base-NER` (CoNLL-2003 fine-tuned BERT) to extract LOC, ORG,
PER, and MISC entities. The analysis also tracks a curated list of analytically
relevant entities: factory-country names (Vietnam, China, Portugal, etc.),
accountability bodies (Fair Labor Association, Better Cotton, SBTi), and
crisis-period actors, to see how their mention frequency shifts across periods.

**LLM analysis** uses the Claude API for two distinct tasks:
1. *Discourse summarization*: a structured per-period summary across all three
   sources, framed using the IR concepts above.
2. *Accountability classification*: a zero-shot prompt that scores text samples 1-5
   on "concreteness" and "accountability," with structured JSON output for
   quantitative comparison. This demonstrates prompt-as-classifier design without any
   model fine-tuning.

**Keyword/theme tracking** counts normalized mentions of five thematic clusters
(transparency claims, accountability language, sustainability terminology, crisis
markers, rehabilitation markers) per document, averaged by source and period.

## Limitations and Future Extensions

This is a proof-of-concept pipeline built to a 1-2 week scope, not a comprehensive
longitudinal study. Known limitations:

- **Single-page snapshots**: only one Everlane page (sustainability/factory) is
  captured per period. The scraper is written to accept any Wayback URL, so extending
  to additional pages (About, Impact Report) is a configuration change, not a rewrite.
- **Sample sizes**: Reddit and news collection are capped (200 posts/subreddit, 50
  articles/period) for runtime reasons; results should be read as directional, not
  statistically definitive.
- **Binary sentiment**: DistilBERT/SST-2 doesn't capture sarcasm, mixed sentiment, or
  domain-specific tone (e.g., skepticism framed politely).
- **Period boundaries are approximate**: real discourse doesn't reset cleanly at year
  boundaries; the periods are analytical conveniences, not hard cutoffs.

Possible extensions: additional Wayback snapshots per period for trend lines within a
period, broader subreddit/news coverage, fine-tuned domain-specific sentiment models,
or topic modeling (e.g., BERTopic) to surface themes not captured by the curated
keyword list.
