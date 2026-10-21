"""Refreshes the latest Coding Overhead posts between the markers in README.md."""
import re
import urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from pathlib import Path

FEED = "https://coding-overhead.com/index.xml"
README = Path(__file__).resolve().parent.parent / "README.md"
COUNT = 5
START, END = "<!-- posts:start -->", "<!-- posts:end -->"


def latest_posts():
    req = urllib.request.Request(FEED, headers={"User-Agent": "github.com/ismd/ismd"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        feed = ET.fromstring(resp.read())
    # The home feed also carries pages like /about/.
    posts = [
        (parsedate_to_datetime(item.findtext("pubDate", "")), item.findtext("title", "").strip(), link)
        for item in feed.iter("item")
        if "/posts/" in (link := item.findtext("link", ""))
    ]
    for published, title, link in sorted(posts, reverse=True)[:COUNT]:
        title = re.sub(r"([\[\]])", r"\\\1", title)
        yield f"- [{title}]({link}) · {published:%Y-%m-%d}"


def main():
    readme = README.read_text()
    block = "\n".join([START, *latest_posts(), END])
    updated, found = re.subn(f"{re.escape(START)}.*?{re.escape(END)}", lambda _: block, readme, flags=re.S)
    if not found:
        raise SystemExit(f"{README.name}: markers {START} / {END} not found")
    README.write_text(updated)


if __name__ == "__main__":
    main()
