# lfgtme

The site for lfgtme, a recruiting agency for GTM engineers run by Steven Brady.

The homepage is a seek-and-find game. A packed SaaS conference hall hides one GTM engineer.
Click the wrong person and you get a joke built from what 179 real GTM engineer job posts ask
for. Find the right one and the page says what the rest of the site is about: we find them for
you.

Open `site/index.html` in a browser to play it. It works on phones too (the hall scrolls
sideways).

## What's here

| Path | What it is |
|---|---|
| `site/` | The homepage: the crowd game, the four characters (Seller, Outbound, Systems, Engineer), a sample shortlist, the fee and who runs it. Plain HTML, CSS and JavaScript, no build step. |
| `tools/hotspot-tagger.html` | The tool used to make the game: drop in an image, drag a box around the target and each near miss, type a joke for each, play-test it, then copy the boxes out as JSON. |
| `jd-library/` | Scripts that pull the full text of GTM engineer job posts from Ashby, Greenhouse and Lever's public job-board APIs and count the tools, themes and years they ask for. `patterns.json` holds the counts from 179 posts (October and November 2026). The posts themselves aren't in this repo. |

## How it was made

1. **Positioning and five design directions.** Written and mocked up with Claude, then narrowed
   to one: Spot the GTM Engineer.
2. **The crowd art.** Generated in ChatGPT Images, starting from a sketch of the layout, then
   edited until the hall was busy enough and the near misses were in place.
3. **The hotspots.** Tagged by hand in `tools/hotspot-tagger.html`, with the boxes stored as
   percentages of the image so they hold at any screen size.
4. **The jokes.** Each near miss is tied to a number from the job post library (60% name Clay,
   78% mention AI agents, 92% measure the role by pipeline or revenue) or to something learned
   while ranking 1,945 GTM engineers.

## The job post numbers

| Asked for | Share of 179 posts |
|---|---|
| APIs or webhooks | 75% |
| Clay | 60% |
| SQL | 58% |
| Salesforce | 54% |
| AI agents | 78% |
| Pipeline or revenue as the measure | 92% |
| A founding or first GTM hire | 28% |

The typical post names 6 tools. Counts come from keyword matching, so treat them as close.

To rebuild them: put a CSV of postings (company, job title, posting URL and the other columns
`fetch.py` reads) at `jd-library/lane-scout-sheet.csv`, then run `python3 fetch.py` and
`python3 analyze.py`. Python 3, standard library only.
