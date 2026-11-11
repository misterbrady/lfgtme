"""Fetch the full text of every posting in the Lane Scout sheet into jobs/<slug>.md.

Stdlib only. Re-run any time: postings already saved are skipped, closed ones are marked.
    python3 fetch.py            # reads lane-scout-sheet.csv (export of Grok Bots/Lane Scout)
Ashby, Greenhouse and Lever go through their public job-board APIs; everything else is the
page's JobPosting JSON-LD, else its visible text.
"""
import csv, html, json, os, re, sys, time, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "jobs")
UA = {"User-Agent": "Mozilla/5.0 (Macintosh) lfgtme-jd-library"}
_ashby = {}


def get(url, as_json=False):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=40) as r:
        b = r.read().decode("utf-8", "replace")
    return json.loads(b) if as_json else b


def strip(h):
    h = re.sub(r"(?is)<(script|style|noscript).*?</\1>", " ", h)
    h = re.sub(r"(?i)<br\s*/?>|</p>|</li>|</h\d>|</div>", "\n", h)
    h = re.sub(r"(?i)<li[^>]*>", "\n- ", h)
    t = html.unescape(re.sub(r"<[^>]+>", " ", h))
    t = re.sub(r"[ \t\xa0]+", " ", t)
    return re.sub(r"\n\s*\n+", "\n\n", t).strip()


def ashby(u):
    p = urllib.parse.urlparse(u).path.strip("/").split("/")
    org, jid = urllib.parse.unquote(p[0]), p[1]
    if org not in _ashby:
        _ashby[org] = get(f"https://api.ashbyhq.com/posting-api/job-board/{urllib.parse.quote(org)}?includeCompensation=true", True)
    for j in _ashby[org].get("jobs", []):
        if j.get("id") == jid:
            return j.get("descriptionPlain") or strip(j.get("descriptionHtml", ""))
    return None


def greenhouse(u):
    q = urllib.parse.parse_qs(urllib.parse.urlparse(u).query)
    m = re.search(r"greenhouse\.io/([^/]+)/jobs/(\d+)", u)
    if m:
        board, jid = m.group(1), m.group(2)
    elif "gh_jid" in q:
        board, jid = urllib.parse.urlparse(u).netloc.split(".")[1].replace("toasttab", "toast"), q["gh_jid"][0]
    else:
        return None
    j = get(f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs/{jid}", True)
    return strip(html.unescape(j.get("content", "")))


def lever(u):
    m = re.search(r"lever\.co/([^/]+)/([0-9a-f-]{36})", u)
    j = get(f"https://api.lever.co/v0/postings/{m.group(1)}/{m.group(2)}", True)
    parts = [j.get("descriptionPlain", "")]
    for l in j.get("lists", []):
        parts.append(l.get("text", "") + "\n" + strip(l.get("content", "")))
    parts.append(j.get("additionalPlain", ""))
    return "\n\n".join(p for p in parts if p)


def page(u):
    h = get(u)
    for block in re.findall(r'(?is)<script[^>]+ld\+json[^>]*>(.*?)</script>', h):
        try:
            d = json.loads(block)
        except Exception:
            continue
        for x in (d if isinstance(d, list) else d.get("@graph", [d])):
            if isinstance(x, dict) and x.get("@type") == "JobPosting" and x.get("description"):
                return strip(html.unescape(x["description"]))
    t = strip(h)
    return t if len(t) > 800 else None


def slug(r):
    s = f"{r['company']}-{r['job title']}".lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")[:80]


def one(r):
    u, ats = r["posting URL"], r["ATS"].lower()
    path = os.path.join(OUT, slug(r) + ".md")
    if os.path.exists(path):
        return r, "saved", path
    try:
        if "ashby" in u:
            t = ashby(u)
        elif "greenhouse" in u or "gh_jid" in u:
            t = greenhouse(u)
        elif "lever.co" in u:
            t = lever(u)
        else:
            t = page(u)
    except Exception as e:
        return r, f"error: {str(e)[:80]}", None
    if not t or len(t) < 300:
        return r, "closed or unreadable", None
    meta = {k: r[k] for k in ("company", "job title", "location", "remote", "salary", "posting URL", "ATS", "hiring team title", "first posted", "date found")}
    fm = "\n".join(f"{k.replace(' ', '_')}: {json.dumps(v, ensure_ascii=False)}" for k, v in meta.items())
    with open(path, "w") as f:
        f.write(f"---\n{fm}\nfetched: \"{time.strftime('%Y-%m-%d')}\"\n---\n\n# {r['job title']} at {r['company']}\n\n{t}\n")
    return r, "saved", path


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    rows = list(csv.DictReader(open(os.path.join(HERE, "lane-scout-sheet.csv"))))
    # Ashby boards are cached per company, so fetch them first in one thread per company
    with ThreadPoolExecutor(8) as ex:
        res = list(ex.map(one, rows))
    status = [{"company": r["company"], "job title": r["job title"], "posting URL": r["posting URL"], "status": s,
               "file": os.path.basename(p) if p else None} for r, s, p in res]
    json.dump(status, open(os.path.join(HERE, "status.json"), "w"), indent=1, ensure_ascii=False)
    from collections import Counter
    print(Counter(s["status"].split(":")[0] for s in status))
