"""Count what GTM engineer job descriptions ask for, across every saved posting in jobs/.

Stdlib only. Writes patterns.json; LIBRARY.md is written by hand from it.
    python3 analyze.py
"""
import json, os, re
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
JOBS = os.path.join(HERE, "jobs")

TOOLS = {
    "Clay": r"\bclay\b", "Salesforce": r"salesforce|\bsfdc\b", "HubSpot": r"hubspot", "n8n": r"\bn8n\b",
    "Zapier": r"zapier", "Make": r"\bmake\.com\b|\bmake \(|integromat", "Python": r"\bpython\b",
    "SQL": r"\bsql\b", "JavaScript/TypeScript": r"javascript|typescript|\bnode(\.js)?\b",
    "Apollo": r"\bapollo\b", "Outreach": r"\boutreach\.io\b|\boutreach\b(?= ?(,|/|and|or|\)))",
    "Salesloft": r"salesloft", "Gong": r"\bgong\b", "ZoomInfo": r"zoominfo", "Snowflake": r"snowflake",
    "BigQuery": r"bigquery", "dbt": r"\bdbt\b", "Hightouch/Census": r"hightouch|census", "Segment": r"\bsegment\b(?= ?(,|/|\)|and))",
    "Marketo": r"marketo", "Smartlead/Instantly": r"smartlead|instantly", "Common Room": r"common room",
    "Retool": r"retool", "Airtable": r"airtable", "Webflow": r"webflow", "LLMs (named)": r"openai|anthropic|claude|gpt|gemini",
    "Cursor/Claude Code": r"cursor|claude code", "APIs/webhooks": r"\bapis?\b|webhook", "Unify": r"\bunify\b",
}
THEMES = {
    "AI agents": r"\bagents?\b|agentic", "LLMs": r"\bllms?\b|large language", "first / founding hire": r"first gtm|founding|first hire|first engineer|0 ?(to|->|→) ?1|zero to one",
    "build from scratch": r"from scratch|ground up|greenfield", "outbound": r"outbound", "enrichment": r"enrich",
    "lead scoring / routing": r"scor(e|ing)|rout(e|ing)", "signals / intent": r"signal|intent", "CRM hygiene / data quality": r"hygiene|data quality|clean data|dedup",
    "experimentation": r"experiment|a/b|test and learn", "own end to end": r"end[- ]to[- ]end|own the|ownership", "ship fast": r"\bship(s|ped|ping)?\b|move fast|bias (for|toward) action|speed",
    "scrappy / builder": r"scrappy|builder|hacker|tinker", "works with sales": r"\bsales team|\baes?\b|account executives|sdrs?|bdrs?",
    "works with marketing": r"marketing", "revops": r"revops|revenue operations", "pipeline / revenue metric": r"pipeline|revenue",
    "low ego": r"low[- ]ego|humble|no ego", "documentation": r"document",
}
YEARS = re.compile(r"(\d+)\s*\+?\s*(?:-|to|–)?\s*(\d+)?\s*\+?\s*years?", re.I)


def load():
    for f in sorted(os.listdir(JOBS)):
        t = open(os.path.join(JOBS, f)).read()
        fm, body = t.split("\n---\n", 1)
        meta = {}
        for line in fm.strip("-\n").splitlines():
            k, v = line.split(": ", 1)
            meta[k] = json.loads(v)
        yield f, meta, body


if __name__ == "__main__":
    docs = list(load())
    n = len(docs)
    tools, themes, years = Counter(), Counter(), Counter()
    examples = {}
    for f, meta, body in docs:
        low = body.lower()
        for k, rx in TOOLS.items():
            if re.search(rx, low):
                tools[k] += 1
        for k, rx in THEMES.items():
            if re.search(rx, low):
                themes[k] += 1
                m = re.search(r"[^.\n]*(?:" + rx + r")[^.\n]*", low)
                if m and k not in examples:
                    examples[k] = (meta["company"], m.group(0).strip()[:220])
        ys = [int(a) for a, b in YEARS.findall(body) if a.isdigit() and int(a) <= 15]
        if ys:
            years[min(ys)] += 1
        else:
            years["none stated"] += 1
    out = {"postings": n, "tools": tools.most_common(), "themes": themes.most_common(),
           "min_years_asked": sorted(years.items(), key=lambda x: (isinstance(x[0], str), x[0])), "example_lines": examples}
    json.dump(out, open(os.path.join(HERE, "patterns.json"), "w"), indent=1, ensure_ascii=False)
    print(n, "postings")
    for k, v in tools.most_common():
        print(f"  {k:24} {v:4} {round(100 * v / n)}%")
    print()
    for k, v in themes.most_common():
        print(f"  {k:28} {v:4} {round(100 * v / n)}%")
    print("min years:", out["min_years_asked"])
