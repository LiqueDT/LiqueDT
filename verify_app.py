"""Dependency-free structural and gateway checks for LiqueDT."""

from __future__ import annotations

import json
import re
from html.parser import HTMLParser
from pathlib import Path
from unittest.mock import patch

import server


ROOT = Path(__file__).resolve().parent


class AppParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: set[str] = set()
        self.duplicate_ids: set[str] = set()
        self.assets: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        element_id = values.get("id")
        if element_id:
            if element_id in self.ids:
                self.duplicate_ids.add(element_id)
            self.ids.add(element_id)
        if tag == "script" and values.get("src"):
            self.assets.append(values["src"] or "")
        if tag == "link" and values.get("href"):
            self.assets.append(values["href"] or "")


NEWS_FIXTURE = b"""<?xml version='1.0'?><rss><channel>
<item><title>Gold rises as dollar falls on rate cut expectations</title><link>https://example.com/gold</link><pubDate>Sun, 21 Jun 2026 02:00:00 GMT</pubDate></item>
<item><title>Oil steadies while markets await Fed remarks</title><link>https://example.com/oil</link><pubDate>Sun, 21 Jun 2026 01:00:00 GMT</pubDate></item>
</channel></rss>"""

CALENDAR_FIXTURE = b"""<?xml version='1.0'?><weeklyevents>
<event><title>Core PCE Price Index m/m</title><country>USD</country><date>12-31-2099</date><time>8:30am</time><impact>High</impact><forecast>0.2%</forecast><previous>0.3%</previous><url>https://example.com/pce</url></event>
<event><title>Low impact item</title><country>USD</country><date>12-31-2099</date><time>9:00am</time><impact>Low</impact></event>
</weeklyevents>"""


def main() -> None:
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    javascript = (ROOT / "app.js").read_text(encoding="utf-8")
    manifest = json.loads((ROOT / "manifest.webmanifest").read_text(encoding="utf-8"))
    parser = AppParser()
    parser.feed(html)

    assert not parser.duplicate_ids, f"Duplicate HTML ids: {sorted(parser.duplicate_ids)}"
    js_ids = set(re.findall(r'\$\("#([A-Za-z][\w-]*)"\)', javascript))
    missing_ids = sorted(js_ids - parser.ids)
    assert not missing_ids, f"JavaScript references missing HTML ids: {missing_ids}"

    local_assets = [asset for asset in parser.assets if not re.match(r"^[a-z]+:", asset)]
    missing_assets = sorted(asset for asset in local_assets if not (ROOT / asset).exists())
    assert not missing_assets, f"Missing linked assets: {missing_assets}"
    assert manifest["short_name"] == "LiqueDT"
    assert "tradeForm" not in html and "position sizing" not in html.lower()

    bullish_score, bullish_impact, factors = server.headline_score("Gold rises as dollar falls on rate cut expectations")
    bearish_score, bearish_impact, _ = server.headline_score("Gold retreats as higher yields lift the dollar")
    assert bullish_score > 0 and bullish_impact == "bullish" and "Dollar" in factors
    assert bearish_score < 0 and bearish_impact == "bearish"

    with patch.object(server, "fetch_bytes", return_value=NEWS_FIXTURE):
        news = server.load_news()
    with patch.object(server, "fetch_bytes", return_value=CALENDAR_FIXTURE):
        calendar = server.load_calendar()
    assert news["ok"] and len(news["items"]) == 2 and news["pulse"]["score"] > 0
    assert calendar["ok"] and len(calendar["events"]) == 1 and calendar["events"][0]["impact"] == "High"

    print(f"PASS: {len(parser.ids)} unique elements and {len(js_ids)} JavaScript references")
    print("PASS: local assets, manifest, and no-trading product boundary")
    print("PASS: news relevance, narrative classification, and calendar normalization")


if __name__ == "__main__":
    main()
