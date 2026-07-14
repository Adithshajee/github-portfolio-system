"""
GPS Blog/RSS Provider
─────────────────────
Fetches and lists recent blog posts from any RSS feed (Dev.to, Medium, Hashnode, etc.).
"""

from __future__ import annotations

import logging
import xml.etree.ElementTree as ET  # nosec

from pydantic import BaseModel

from gps.providers.base import BaseProvider, register
from gps.utils.http import HTTPClient

logger = logging.getLogger(__name__)


class BlogPost(BaseModel):
    title: str
    link: str
    pub_date: str = ""


class BlogData(BaseModel):
    feed_url: str
    title: str = ""
    posts: list[BlogPost] = []


@register("blog")
class BlogProvider(BaseProvider[str, BlogData]):
    name = "blog"
    display_name = "Blog Feed"

    def __init__(self, feed_url: str) -> None:
        self.feed_url = feed_url
        self._http = HTTPClient(user_agent="GPS/3.0")

    def fetch(self) -> str:
        try:
            # Fetch raw XML feed content
            response = self._http._client.get(self.feed_url, timeout=15)
            response.raise_for_status()
            return response.text
        except Exception as e:
            logger.warning("Failed to fetch RSS blog feed: %s", e)
            return ""

    def transform(self, raw: str) -> BlogData:
        if not raw:
            return BlogData(feed_url=self.feed_url)
        try:
            root = ET.fromstring(raw.encode("utf-8"))  # noqa: S314 # nosec
            channel = root.find("channel")
            if channel is None:
                return BlogData(feed_url=self.feed_url)

            channel_title = getattr(channel.find("title"), "text", "Blog") or "Blog"
            posts = []

            for item in channel.findall("item")[:5]:  # limit to top 5 posts
                title_node = item.find("title")
                link_node = item.find("link")
                pub_date_node = item.find("pubDate")

                title = getattr(title_node, "text", "") or ""
                link = getattr(link_node, "text", "") or ""
                pub_date = getattr(pub_date_node, "text", "") or ""

                if title and link:
                    # Clean up pub date formatting (e.g. "Mon, 01 Jan 2026..." -> "01 Jan 2026")
                    if " " in pub_date:
                        parts = pub_date.split(" ")
                        if len(parts) >= 4:
                            pub_date = f"{parts[1]} {parts[2]} {parts[3]}"
                    posts.append(BlogPost(title=title, link=link, pub_date=pub_date))

            return BlogData(feed_url=self.feed_url, title=channel_title, posts=posts)
        except Exception as e:
            logger.warning("Failed to parse RSS feed xml: %s", e)
            return BlogData(feed_url=self.feed_url)

    def validate(self, data: BlogData) -> bool:
        return len(data.posts) > 0

    def render(self, data: BlogData) -> str:
        title = data.title or "Recent Blog Posts"
        lines = [f"### ✍️ {title}", ""]
        for post in data.posts:
            date_str = f" *({post.pub_date})*" if post.pub_date else ""
            lines.append(f"- **[{post.title}]({post.link})**{date_str}")
        return "\n".join(lines)
