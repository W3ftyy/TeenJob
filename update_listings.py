#!/usr/bin/env python3
"""Refreshes listings.json.

1. Removes open listings whose deadline_iso is in the past.
2. If APIFY_TOKEN and APIFY_ACTOR are set, pulls new listings from that Apify
   actor and merges them in (items from earlier auto-runs that are no longer
   returned are removed).
Uses only the Python standard library.
"""
import datetime
import hashlib
import json
import os
import re
import urllib.request

PATH = "listings.json"
TODAY = datetime.date.today().isoformat()


def load():
    with open(PATH, encoding="utf-8") as f:
        return json.load(f)


def save(data):
    with open(PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write("\n")


def fetch_apify():
    token, actor = os.environ.get("APIFY_TOKEN"), os.environ.get("APIFY_ACTOR")
    if not token or not actor:
        return []
    body = (os.environ.get("APIFY_INPUT") or "{}").encode("utf-8")
    url = f"https://api.apify.com/v2/acts/{actor}/run-sync-get-dataset-items?token={token}"
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=290) as resp:
        return json.load(resp)


def pick(item, *names):
    for n in names:
        v = item.get(n)
        if v:
            return str(v).strip()
    return ""


def convert(item):
    """Maps one scraped item to our format. Field names are guesses:
    check the first run's output and adjust the names below if needed."""
    url = pick(item, "url", "link", "jobUrl", "applyUrl")
    title = pick(item, "title", "jobTitle", "name", "position")
    if not url or not title:
        return None
    text = " ".join(str(v) for v in item.values() if isinstance(v, str)).lower()
    min_age = None
    m = re.search(r"(?:alates|from|от|vähemalt|at least)\s*(1[3-8])", text)
    if m:
        min_age = int(m.group(1))
    elif re.search(r"\b18\s*\+", text):
        min_age = 18
    iso = ""
    m = re.search(r"\d{4}-\d{2}-\d{2}", pick(item, "deadline", "validThrough", "expires", "expiryDate", "endDate"))
    if m:
        iso = m.group(0)
    return {
        "id": "a" + hashlib.md5(url.encode()).hexdigest()[:10],
        "title": title,
        "employer": pick(item, "employer", "company", "companyName", "organization"),
        "town": pick(item, "location", "city", "town", "address"),
        "status": "open",
        "deadline": ("Apply by " + iso) if iso else "See the listing",
        "deadline_iso": iso,
        "minAge": min_age,
        "pay": pick(item, "salary", "pay", "wage"),
        "note": pick(item, "description", "summary")[:220],
        "url": url,
        "source": "auto",
    }


def main():
    data = load()
    items = data.get("listings", [])
    before = len(items)
    items = [l for l in items if not (l.get("status") == "open" and l.get("deadline_iso") and l["deadline_iso"] < TODAY)]
    print(f"Removed {before - len(items)} expired listings")

    try:
        fetched = fetch_apify()
    except Exception as e:  # keep the site working if the source fails
        print("Fetch failed:", e)
        fetched = []
    new = [c for c in (convert(i) for i in fetched) if c]
    if new:
        urls = {n["url"] for n in new}
        items = [l for l in items if l.get("source") != "auto" or l["url"] in urls]
        known = {l["url"] for l in items}
        added = [n for n in new if n["url"] not in known]
        items += added
        data["updated"] = TODAY
        print(f"Fetched {len(new)} items, added {len(added)}")
    else:
        print("No new items fetched; 'updated' date left unchanged")

    data["listings"] = items
    save(data)


if __name__ == "__main__":
    main()
