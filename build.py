#!/usr/bin/env python3
"""Static site generator for the Yes to Jesus 21-day devotional.
Renders /public from templates/ + content/days.py. No JS framework, no build
step beyond this script — plain HTML/CSS so both browsers and AI crawlers can
read every page directly.
"""
import json
import os
import re
import shutil
import sys

from jinja2 import Environment, FileSystemLoader

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "content"))
import days as content  # noqa: E402

# Extracts "JHN.3.16-17" out of ".../bible/116/JHN.3.16-17.NLT"
API_REF_RE = re.compile(r"/bible/\d+/([A-Z0-9]+\.[\d.\-]+)\.[A-Z]+$")


def api_ref_from_link(link):
    m = API_REF_RE.search(link)
    return m.group(1) if m else None


# Bible version IDs in the YouVersion Platform API's shared catalog (same
# numbering as bible.com). Only versions listed here are actually present in
# the Platform's catalog under this app key — the booklet also cites NLT and
# MSG, but neither exists in the Platform catalog, so those days fall back to
# NIV instead.
NIV_VERSION_ID = 111
BOOKLET_VERSION_IDS = {"NIV": NIV_VERSION_ID}
FALLBACK_VERSION_ID = NIV_VERSION_ID


def default_version_id_for(translation):
    return BOOKLET_VERSION_IDS.get(translation, FALLBACK_VERSION_ID)

SITE_URL = os.environ.get("SITE_URL", "https://yestojesus.us")
ROOT = os.path.dirname(os.path.abspath(__file__))
PUBLIC = os.path.join(ROOT, "public")
BUILD_YEAR = "2026"

META_KEYS = {"day", "week", "slug", "title", "summary", "scripture"}

BLOCK_PARAGRAPH_KEYS = ("body", "body2", "body3", "body4")
BLOCK_QUOTE_KEYS = ("quote", "quote2", "quote3", "quote4")
BLOCK_LIST_HEADED_KEYS = ("list_headed", "list_headed2")


def blocks_for_day(day):
    """Walk the day dict in insertion order and emit typed render blocks.

    Each `quote*` key pairs 1:1, in order, with the day's `scripture` list
    (verified by content authoring) — so we can reuse that entry's already
    -parsed api_ref/default_version_id for the live widget instead of
    re-parsing the free-text quote reference.
    """
    blocks = []
    scripture = day.get("scripture", [])
    quote_idx = 0
    for key, value in day.items():
        if key in META_KEYS:
            continue
        if key in BLOCK_PARAGRAPH_KEYS:
            blocks.append({"type": "paragraphs", "entries": value})
        elif key in BLOCK_QUOTE_KEYS:
            s = scripture[quote_idx] if quote_idx < len(scripture) else None
            quote_idx += 1
            blocks.append({
                "type": "quote",
                "text": value["text"],
                "ref": value["ref"],
                "api_ref": s["api_ref"] if s else None,
                "default_version_id": s["default_version_id"] if s else FALLBACK_VERSION_ID,
            })
        elif key == "list":
            blocks.append({"type": "list", "entries": value})
        elif key in BLOCK_LIST_HEADED_KEYS:
            blocks.append({"type": "list_headed", "entries": value})
        elif key == "closing":
            blocks.append({"type": "paragraphs", "entries": [value]})
        elif key == "reflection":
            if isinstance(value, dict):
                blocks.append({"type": "reflection", "text": value["text"], "journal_lines": value.get("journal_lines")})
            else:
                blocks.append({"type": "reflection", "text": value, "journal_lines": None})
        elif key in ("prayer", "prayer_intro"):
            blocks.append({"type": "prayer", "text": value})
        elif key == "next_steps":
            blocks.append({"type": "next_steps", "entries": value})
    return blocks


def reading_minutes_for(blocks):
    """Rough estimate at ~200 wpm, counting body/quote/list text only."""
    word_count = 0
    for blk in blocks:
        if blk["type"] == "paragraphs":
            word_count += sum(len(p.split()) for p in blk["entries"])
        elif blk["type"] == "quote":
            word_count += len(blk["text"].split())
        elif blk["type"] in ("list", "next_steps"):
            word_count += sum(len(item.split()) for item in blk["entries"])
        elif blk["type"] == "list_headed":
            word_count += sum(len(item["head"].split()) + len(item["body"].split()) for item in blk["entries"])
        elif blk["type"] in ("reflection", "prayer"):
            word_count += len(blk["text"].split())
    return max(1, round(word_count / 200))


def write(path, text):
    full = os.path.join(PUBLIC, path.lstrip("/"))
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(text)


def answer_text_for_day(day, blocks, limit=600):
    """Concatenate paragraph text into a substantive plain-text answer for
    FAQPage/QAPage schema — the day's title is already phrased as the exact
    question a reader (or an AI answer engine) would ask."""
    parts = []
    total = 0
    for blk in blocks:
        if blk["type"] == "paragraphs":
            for p in blk["entries"]:
                parts.append(p)
                total += len(p)
                if total >= limit:
                    break
        if total >= limit:
            break
    text = " ".join(parts)
    return (text[:limit].rsplit(" ", 1)[0] + "…") if len(text) > limit else text


def day_article_jsonld(day, url, blocks):
    answer = answer_text_for_day(day, blocks)
    return json.dumps({
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "Article",
                "headline": day["title"],
                "description": day["summary"],
                "url": url,
                "datePublished": "2026-01-01",
                "author": {"@type": "Organization", "name": "Life.Church", "url": "https://www.life.church"},
                "publisher": {"@type": "Organization", "name": "Yes to Jesus"},
                "isPartOf": {"@type": "CreativeWorkSeries", "name": "Yes to Jesus: A 21-Day Devotional"},
                "position": day["day"],
            },
            {
                "@type": "FAQPage",
                "mainEntity": [
                    {
                        "@type": "Question",
                        "name": day["title"],
                        "acceptedAnswer": {
                            "@type": "Answer",
                            "text": answer,
                        },
                    }
                ],
            },
        ],
    }, indent=None)


def website_jsonld():
    return json.dumps({
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": "Yes to Jesus",
        "url": SITE_URL,
        "description": "A free 21-day devotional for new believers, adapted from Life.Church's You Said Yes, with scripture from the YouVersion Bible App.",
    })


def main():
    if os.path.exists(PUBLIC):
        shutil.rmtree(PUBLIC)
    os.makedirs(PUBLIC)

    env = Environment(loader=FileSystemLoader(os.path.join(ROOT, "templates")), autoescape=True)

    days = content.DAYS
    weeks = {}
    for d in days:
        weeks.setdefault(d["week"], []).append(d)
    weeks_sorted = sorted(weeks.items())

    base_ctx = {"site_url": SITE_URL, "year": BUILD_YEAR, "first_day_slug": days[0]["slug"]}
    week_colors = {1: "blue", 2: "terracotta", 3: "sage"}

    # ---- Home page ----
    tmpl = env.get_template("home.html")
    html = tmpl.render(
        **base_ctx,
        page_title="Yes to Jesus — A Free 21-Day Devotional for New Believers",
        page_description="You said yes to Jesus. Now what? A free, day-by-day devotional answering the real questions new believers ask, with scripture from the YouVersion Bible App.",
        canonical_path="/",
        json_ld=website_jsonld(),
        days=days,
        weeks=weeks_sorted,
        week_titles=content.WEEK_TITLES,
        week_colors=week_colors,
        body_class="week-3",
    )
    write("index.html", html)

    # ---- Day pages ----
    tmpl = env.get_template("day.html")
    for i, day in enumerate(days):
        for s in day.get("scripture", []):
            s["api_ref"] = api_ref_from_link(s["link"])
            s["default_version_id"] = default_version_id_for(s["translation"])
        blocks = blocks_for_day(day)
        prev_day = days[i - 1] if i > 0 else None
        next_day = days[i + 1] if i < len(days) - 1 else None
        url = f"{SITE_URL}/day/{day['slug']}/"
        html = tmpl.render(
            **base_ctx,
            page_title=f"{day['title']} — Day {day['day']} | Yes to Jesus",
            page_description=day["summary"],
            canonical_path=f"/day/{day['slug']}/",
            og_type="article",
            json_ld=day_article_jsonld(day, url, blocks),
            day=day,
            blocks=blocks,
            week_title=content.WEEK_TITLES[day["week"]],
            prev_day=prev_day,
            next_day=next_day,
            reading_minutes=reading_minutes_for(blocks),
            body_class=f"week-{day['week']}",
        )
        write(f"day/{day['slug']}/index.html", html)

    # ---- About page ----
    tmpl = env.get_template("about.html")
    html = tmpl.render(
        **base_ctx,
        page_title="About — Yes to Jesus Devotional",
        page_description="This devotional is adapted from Life.Church's free You Said Yes resource, with scripture linked to the YouVersion Bible App.",
        canonical_path="/about/",
        json_ld=None,
        body_class="week-3",
    )
    write("about/index.html", html)

    # ---- Static assets ----
    shutil.copytree(os.path.join(ROOT, "static", "css"), os.path.join(PUBLIC, "css"))
    shutil.copytree(os.path.join(ROOT, "static", "img"), os.path.join(PUBLIC, "img"))
    shutil.copytree(os.path.join(ROOT, "static", "js"), os.path.join(PUBLIC, "js"))

    # ---- robots.txt: explicitly welcome AI crawlers ----
    robots = """User-agent: *
Allow: /

User-agent: GPTBot
Allow: /

User-agent: ChatGPT-User
Allow: /

User-agent: OAI-SearchBot
Allow: /

User-agent: ClaudeBot
Allow: /

User-agent: anthropic-ai
Allow: /

User-agent: Claude-Web
Allow: /

User-agent: PerplexityBot
Allow: /

User-agent: Google-Extended
Allow: /

User-agent: CCBot
Allow: /

Sitemap: {site}/sitemap.xml
""".format(site=SITE_URL)
    write("robots.txt", robots)

    # ---- sitemap.xml ----
    urls = ["/", "/about/"] + [f"/day/{d['slug']}/" for d in days]
    sitemap_entries = "\n".join(
        f"  <url><loc>{SITE_URL}{u}</loc></url>" for u in urls
    )
    sitemap = f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{sitemap_entries}\n</urlset>\n'
    write("sitemap.xml", sitemap)

    # ---- llms.txt: plain-text index for LLM/AI-answer-engine ingestion ----
    lines = [
        "# Yes to Jesus — A Free 21-Day Devotional for New Believers",
        "",
        "> Adapted from Life.Church's free 'You Said Yes' resource (Open Network), paired with scripture from the YouVersion Bible App. Independent, non-commercial project.",
        "",
        "This site answers the real questions people ask after deciding to follow Jesus, one short reading per day, organized into three weeks:",
        "",
    ]
    for week_num, week_title in content.WEEK_TITLES.items():
        lines.append(f"## Week {week_num}: {week_title}")
        for d in weeks[week_num]:
            lines.append(f"- [Day {d['day']}: {d['title']}]({SITE_URL}/day/{d['slug']}/) — {d['summary']}")
        lines.append("")
    lines.append(f"## About")
    lines.append(f"- [About this project & attribution]({SITE_URL}/about/)")
    lines.append("")
    lines.append("Original source: Life.Church Open Network (https://open.life.church/). Scripture: YouVersion Bible App (https://www.bible.com).")
    write("llms.txt", "\n".join(lines) + "\n")

    print(f"Built {len(days)} day pages + home + about to {PUBLIC}")


if __name__ == "__main__":
    main()
