import json
import time
import urllib.request
from pathlib import Path

OUT = Path("anime_updates.json")

HEADERS = {
    "User-Agent": "AnimeCatalogTV GitHub updater",
    "Accept": "application/json"
}

def get_json(url: str):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))

def normalize_type(t):
    if not t:
        return "ТВ-сериал"
    t = str(t).upper()
    if t == "TV":
        return "ТВ-сериал"
    if t == "MOVIE":
        return "Фильм"
    if t == "ONA":
        return "ONA"
    if t == "OVA":
        return "OVA"
    if t == "SPECIAL":
        return "Спешл"
    return t

def convert(item):
    mal_id = item.get("mal_id") or 0

    ru = item.get("title") or ""
    en = item.get("title_english") or item.get("title") or ""

    images = item.get("images") or {}
    jpg = images.get("jpg") or {}
    poster = jpg.get("large_image_url") or jpg.get("image_url") or ""

    genres = []
    for g in item.get("genres") or []:
        name = g.get("name")
        if name:
            genres.append(name)

    studios = item.get("studios") or []
    studio = studios[0].get("name", "") if studios else ""

    year = item.get("year")
    if not year:
        aired = item.get("aired") or {}
        prop = aired.get("prop") or {}
        from_ = prop.get("from") or {}
        year = from_.get("year") or ""

    return {
        "id": 900000 + int(mal_id),
        "ru": ru,
        "en": en,
        "year": str(year or ""),
        "type": normalize_type(item.get("type")),
        "episodes": str(item.get("episodes") or ""),
        "status": item.get("status") or "",
        "studio": studio,
        "rating": item.get("score") or 0,
        "poster": poster,
        "genres": genres
    }

def load_existing():
    if not OUT.exists():
        return {"version": 1, "anime": []}
    try:
        data = json.loads(OUT.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return {"version": 1, "anime": data}
        if "anime" not in data:
            data["anime"] = []
        return data
    except Exception:
        return {"version": 1, "anime": []}

def main():
    existing = load_existing()
    anime = existing.get("anime") or []

    known = set()
    for a in anime:
        known.add(str(a.get("id", "")))
        known.add((a.get("en", "") or a.get("ru", "")).lower())

    urls = [
        "https://api.jikan.moe/v4/seasons/now?limit=25",
        "https://api.jikan.moe/v4/seasons/upcoming?limit=25"
    ]

    added = []

    for url in urls:
        data = get_json(url)
        for item in data.get("data") or []:
            a = convert(item)
            k1 = str(a["id"])
            k2 = (a.get("en") or a.get("ru") or "").lower()
            if k1 not in known and k2 not in known:
                anime.append(a)
                added.append(a)
                known.add(k1)
                known.add(k2)
        time.sleep(1)

    def sort_key(x):
        try:
            year = int(x.get("year") or 0)
        except Exception:
            year = 0
        return (year, float(x.get("rating") or 0), int(x.get("id") or 0))

    anime.sort(key=sort_key, reverse=True)

    result = {
        "version": int(existing.get("version", 1)) + (1 if added else 0),
        "anime": anime
    }

    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Added: {len(added)}")
    for a in added[:20]:
        print("-", a.get("ru") or a.get("en"))

if __name__ == "__main__":
    main()
