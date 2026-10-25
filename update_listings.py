#!/usr/bin/env python3
"""Refreshes listings.json.

1. Removes open listings whose deadline_iso is in the past.
2. If APIFY_TOKEN and APIFY_ACTOR are set, runs the Apify Tootukassa scraper
   once per keyword below and merges the results in. Auto-added items that are
   no longer returned are removed, so closed jobs disappear.
Standard library only.
"""
import datetime
import hashlib
import json
import os
import urllib.request

PATH = "listings.json"
TODAY = datetime.date.today().isoformat()

# Estonian search words (the Tootukassa search needs Estonian). Edit freely.
KEYWORDS = ["müüja", "kaubapaigutaja", "koristaja", "klienditeenindaja", "abitööline", "köögiabiline"]
MAX_PER_KEYWORD = 30   # results per keyword (this is what you pay for)
MAX_AUTO = 60          # most auto-added listings kept on the site


def load():
    with open(PATH, encoding="utf-8") as f:
        return json.load(f)


def save(data):
    with open(PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write("\n")


def run_actor(query):
    token = os.environ["APIFY_TOKEN"]
    actor = os.environ["APIFY_ACTOR"].replace("/", "~")
    body = json.dumps({
        "searchQuery": query,
        "maxResults": MAX_PER_KEYWORD,
        "proxyConfiguration": {"useApifyProxy": True},
    }).encode("utf-8")
    req = urllib.request.Request(
        f"https://api.apify.com/v2/acts/{actor}/run-sync-get-dataset-items",
        data=body,
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + token},
    )
    with urllib.request.urlopen(req, timeout=300) as resp:
        return json.load(resp)


def fmt(iso):
    return f"{iso[8:10]}.{iso[5:7]}.{iso[:4]}"


def convert(item):
    """Maps one Tootukassa scraper item to our listing format."""
    url = (item.get("url") or "").strip()
    title = (item.get("jobTitle") or "").strip()
    if not url or not title:
        return None
    if item.get("jobTitleDetail"):
        title += " (" + str(item["jobTitleDetail"]).strip() + ")"
    iso = (item.get("deadline") or "")[:10]
    if iso and iso < TODAY:
        return None
    kinds_en, kinds_et, kinds_ru = [], [], []
    if item.get("fullTime"):
        kinds_en.append("Full-time"); kinds_et.append("Täiskoormus"); kinds_ru.append("Полная занятость")
    if item.get("partTime"):
        kinds_en.append("Part-time"); kinds_et.append("Osaline koormus"); kinds_ru.append("Неполная занятость")
    if item.get("remoteWork"):
        kinds_en.append("Remote work"); kinds_et.append("Kaugtöö"); kinds_ru.append("Удалённая работа")
    return {
        "id": "a" + hashlib.md5(url.encode()).hexdigest()[:10],
        "title": title,
        "employer": (item.get("company") or "").strip(),
        "town": (item.get("location") or "").strip(),
        "status": "open",
        "deadline": ("Apply by " + fmt(iso)) if iso else "See the listing",
        "deadline_iso": iso,
        "minAge": None,
        "pay": "",
        "note": "From Töötukassa. " + (", ".join(kinds_en) + ". " if kinds_en else "") + "Check the age requirement and details in the listing.",
        "url": url,
        "source": "auto",
        "tr": {
            "et": {
                "deadline": ("Kandideeri kuni " + fmt(iso)) if iso else "Vaata kuulutust",
                "note": "Töötukassa kuulutus. " + (", ".join(kinds_et) + ". " if kinds_et else "") + "Vaata vanusepiiri ja täpsemat infot kuulutusest.",
            },
            "ru": {
                "deadline": ("Подать заявку до " + fmt(iso)) if iso else "Смотрите объявление",
                "note": "Объявление Töötukassa. " + (", ".join(kinds_ru) + ". " if kinds_ru else "") + "Возраст и детали смотрите в объявлении.",
            },
        },
    }


def fetch_all():
    if not os.environ.get("APIFY_TOKEN") or not os.environ.get("APIFY_ACTOR"):
        print("APIFY_TOKEN / APIFY_ACTOR not set: skipping fetch")
        return []
    found = {}
    for kw in KEYWORDS:
        try:
            for item in run_actor(kw):
                c = convert(item)
                if c:
                    found[c["url"]] = c
            print(f"'{kw}': ok")
        except Exception as e:  # one failing keyword must not break the site
            print(f"'{kw}': failed ({e})")
    return list(found.values())


def main():
    data = load()
    items = data.get("listings", [])
    before = len(items)
    items = [l for l in items if not (l.get("status") == "open" and l.get("deadline_iso") and l["deadline_iso"] < TODAY)]
    print(f"Removed {before - len(items)} expired listings")

    new = fetch_all()
    if new:
        new.sort(key=lambda n: n["deadline_iso"] or "9999")
        new = new[:MAX_AUTO]
        manual = [l for l in items if l.get("source") != "auto"]
        known = {l["url"] for l in manual}
        auto = [n for n in new if n["url"] not in known]
        items = manual + auto
        data["updated"] = TODAY
        print(f"Auto listings now: {len(auto)}")
    else:
        print("Nothing fetched: kept the existing listings, 'updated' date unchanged")

    data["listings"] = items
    save(data)


if __name__ == "__main__":
    main()
