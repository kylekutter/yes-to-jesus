# Yes to Jesus

A free, 21-day devotional microsite for new believers — adapted from Life.Church's
[*You Said Yes*](https://open.life.church/) (Open Network), with scripture linked
to and live-fetched from the [YouVersion Platform](https://platform.youversion.com/).

## Stack

Plain static HTML/CSS, no JS framework — a Python + Jinja2 script (`build.py`)
renders `content/days.py` through `templates/*.html` into `public/`, which is
what gets deployed. Live scripture on each day page is fetched client-side
straight from the YouVersion Platform REST API (`static/js/live-scripture.js`).

## Local development

```bash
pip3 install -r requirements.txt
python3 build.py
cd public && python3 -m http.server 4321
```

## Deploy

Deployed on Vercel (`vercel.json` sets the build command and output directory).
Domain: `yestojesus.us` (registered via DreamHost).
