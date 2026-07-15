"""
GPS Widget Subsystem
────────────────────
Defines standard widgets and manages the catalog inside WidgetRegistry.
Provides decoupling between theme visualization layout and widget content logic.
"""

from __future__ import annotations

import logging
from typing import Any, ClassVar

logger = logging.getLogger(__name__)


class BaseWidget:
    """Base class for all GPS widgets. Avoids ABC concrete type abstract errors in MyPy."""

    name: str = ""
    version: str = "1.0.0"
    author: str = "GPS Core"
    dependencies: ClassVar[list[str]] = []

    def __init__(self, settings: dict[str, Any] | None = None) -> None:
        self._settings = settings or {}

    def register(self, registry: WidgetRegistry) -> None:
        """Register the widget in the global registry."""
        registry.register(self.__class__)

    def settings(self) -> dict[str, Any]:
        """Expose widget options and their schema/values."""
        return self._settings

    def render(self, data: dict[str, Any]) -> str:
        """Render widget content as Markdown or HTML."""
        raise NotImplementedError("Widget must implement render()")

    def preview(self) -> str:
        """Return a placeholder markdown representation for UI preview panels."""
        raise NotImplementedError("Widget must implement preview()")

    def metadata(self) -> dict[str, Any]:
        """Return widget metadata."""
        return {
            "name": self.name,
            "version": self.version,
            "author": self.author,
            "dependencies": self.dependencies,
        }

    def to_dict(self) -> dict[str, Any]:
        """Convert widget state to dictionary representation."""
        return {
            "name": self.name,
            "version": self.version,
            "author": self.author,
            "settings": self._settings,
        }


# ─── Built-in Widget Implementations ──────────────────────────────────────────

class GitHubStatsWidget(BaseWidget):
    name = "github_stats"

    def render(self, data: dict[str, Any]) -> str:
        username = data.get("username", "Adithshajee")
        accent = self._settings.get("accent_color", "2563eb").replace("#", "")
        return (
            f"<p align=\"center\">\n"
            f"  <img src=\"https://github-readme-stats.vercel.app/api?username={username}"
            f"&show_icons=true&theme=dark&title_color={accent}&icon_color={accent}\" "
            f"alt=\"GitHub Stats\" />\n"
            f"</p>"
        )

    def preview(self) -> str:
        return "### 📊 GitHub Analytics Dashboard [Stats Mock]"


class SnakeWidget(BaseWidget):
    name = "snake"

    def render(self, data: dict[str, Any]) -> str:
        username = data.get("username", "Adithshajee")
        return (
            f"<picture>\n"
            f"  <source media=\"(prefers-color-scheme: dark)\" "
            f"srcset=\"https://raw.githubusercontent.com/{username}/{username}/main/assets/github-contribution-grid-snake-dark.svg\">\n"
            f"  <source media=\"(prefers-color-scheme: light)\" "
            f"srcset=\"https://raw.githubusercontent.com/{username}/{username}/main/assets/github-contribution-grid-snake.svg\">\n"
            f"  <img alt=\"Snake eating contributions\" "
            f"src=\"https://raw.githubusercontent.com/{username}/{username}/main/assets/github-contribution-grid-snake.svg\" "  # noqa: E501
            f"width=\"100%\">\n"
            f"</picture>"
        )

    def preview(self) -> str:
        return "🐍 [Contribution Grid Snake Mock Illustration]"


class BlogWidget(BaseWidget):
    name = "blog"

    def render(self, data: dict[str, Any]) -> str:
        blog_data = data.get("blog", {})
        posts = blog_data.get("posts", [])
        if not posts:
            return "<!-- GPS: No recent blog posts found -->"
        lines = ["### ✍️ Latest Blog Articles", ""]
        for p in posts[:3]:
            title = p.get("title", "Untitled")
            link = p.get("link", "#")
            date = p.get("published", "")[:10]
            lines.append(f"- **[{title}]({link})** — *{date}*")
        return "\n".join(lines)

    def preview(self) -> str:
        return "### ✍️ Latest Blog Articles\n- [Example Article](https://myblog.com) — *2026-07-15*"


class RoadmapWidget(BaseWidget):
    name = "roadmap"

    def render(self, data: dict[str, Any]) -> str:
        items = self._settings.get("items", ["Advanced LLMs", "MLOps Automation"])
        lines = ["### 🗺️ Learning Roadmap", ""]
        for item in items:
            lines.append(f"- [x] {item}")
        return "\n".join(lines)

    def preview(self) -> str:
        return "### 🗺️ Learning Roadmap\n- [x] Next-Gen MLOps"


class TechStackWidget(BaseWidget):
    name = "tech_stack"

    def render(self, data: dict[str, Any]) -> str:
        skills = self._settings.get("skills", ["Python", "FastAPI", "Docker"])
        lines = ["### 🛠️ Technology Stack", "", "<p align=\"center\">"]
        for skill in skills:
            lines.append(f"  <img src=\"https://img.shields.io/badge/{skill}-1E293B?style=flat-square\" alt=\"{skill}\" />")  # noqa: E501
        lines.append("</p>")
        return "\n".join(lines)

    def preview(self) -> str:
        return "### 🛠️ Technology Stack\n[Python] [Docker] [FastAPI]"


class VisitorsWidget(BaseWidget):
    name = "visitors"

    def render(self, data: dict[str, Any]) -> str:
        username = data.get("username", "Adithshajee")
        return (
            f"<p align=\"center\">\n"
            f"  <img src=\"https://komarev.com/ghpvc/?username={username}&label=Visitor+Views&color=2563eb&style=flat-square\" "  # noqa: E501
            f"alt=\"Visitor Counter\" />\n"
            f"</p>"
        )

    def preview(self) -> str:
        return "[Visitor Counter Shield]"


class ContributionGraphWidget(BaseWidget):
    name = "contribution_graph"

    def render(self, data: dict[str, Any]) -> str:
        username = data.get("username", "Adithshajee")
        return (
            f"<p align=\"center\">\n"
            f"  <img src=\"https://github-readme-activity-graph.vercel.app/graph?username={username}&bg_color=0f172a&color=2563eb\" "  # noqa: E501
            f"alt=\"Contribution Graph\" />\n"
            f"</p>"
        )

    def preview(self) -> str:
        return "[Contribution Graph Mock]"


class MetricsWidget(BaseWidget):
    name = "metrics"

    def render(self, data: dict[str, Any]) -> str:
        username = data.get("username", "Adithshajee")
        return (
            f"<p align=\"center\">\n"
            f"  <img src=\"https://metrics.lecoq.io/{username}?template=classic&config.timezone=UTC\" "  # noqa: E501
            f"alt=\"GitHub Metrics\" />\n"
            f"</p>"
        )

    def preview(self) -> str:
        return "[GitHub Metrics Mock Card]"


class LanguagesWidget(BaseWidget):
    name = "languages"

    def render(self, data: dict[str, Any]) -> str:
        username = data.get("username", "Adithshajee")
        return (
            f"<p align=\"center\">\n"
            f"  <img src=\"https://github-readme-stats.vercel.app/api/top-langs/?username={username}&layout=compact&theme=dark\" "  # noqa: E501
            f"alt=\"Top Languages\" />\n"
            f"</p>"
        )

    def preview(self) -> str:
        return "### 🛠️ Languages Stat Pie Mock"


class PinnedRepositoriesWidget(BaseWidget):
    name = "pinned_repositories"

    def render(self, data: dict[str, Any]) -> str:
        repos = data.get("repos", [])
        lines = ["### 📌 Featured Showcase", ""]
        for r in repos[:3]:
            name = r.get("name", "Repository")
            url = r.get("html_url", "#")
            desc = r.get("description", "Showcase project")
            lines.append(f"- **[{name}]({url})** — {desc}")
        return "\n".join(lines)

    def preview(self) -> str:
        return "### 📌 Featured Showcase\n- [Awesome-Project](https://github.com) — Top Project"


class TimelineWidget(BaseWidget):
    name = "timeline"

    def render(self, data: dict[str, Any]) -> str:
        events = self._settings.get("events", ["2024: Started GPS development", "2026: Released GPS v3.0.0"])  # noqa: E501
        lines = ["### ⏳ Activity Timeline", ""]
        for event in events:
            lines.append(f"- *{event}*")
        return "\n".join(lines)

    def preview(self) -> str:
        return "### ⏳ Activity Timeline\n- *2026: Released v3.0.0*"


class SponsorsWidget(BaseWidget):
    name = "sponsors"

    def render(self, data: dict[str, Any]) -> str:
        username = data.get("username", "Adithshajee")
        return (
            f"<p align=\"center\">\n"
            f"  <a href=\"https://github.com/sponsors/{username}\">\n"
            f"    <img src=\"https://img.shields.io/badge/Sponsor-{username}-pink?style=for-the-badge&logo=GitHub-Sponsors\" alt=\"Sponsor\" />\n"  # noqa: E501
            f"  </a>\n"
            f"</p>"
        )

    def preview(self) -> str:
        return "[Sponsors Shield Badge]"


class AchievementsWidget(BaseWidget):
    name = "achievements"

    def render(self, data: dict[str, Any]) -> str:
        username = data.get("username", "Adithshajee")
        return (
            f"<p align=\"center\">\n"
            f"  <img src=\"https://github-profile-trophy.vercel.app/?username={username}&theme=onedark\" alt=\"Achievements Trohpy\" />\n"  # noqa: E501
            f"</p>"
        )

    def preview(self) -> str:
        return "[Achievements Trophy Shield Mock]"


class CurrentProjectWidget(BaseWidget):
    name = "current_project"

    def render(self, data: dict[str, Any]) -> str:
        project = self._settings.get("project", "GPS v3.0.0 Release")
        link = self._settings.get("link", "https://github.com/Adithshajee/github-portfolio-system")
        return f"💡 **Currently working on:** [{project}]({link})"

    def preview(self) -> str:
        return "💡 **Currently working on:** GPS v3.0.0 Release"


class SocialLinksWidget(BaseWidget):
    name = "social_links"

    def render(self, data: dict[str, Any]) -> str:
        links = self._settings.get("links", {"LinkedIn": "https://linkedin.com", "Twitter": "https://twitter.com"})
        lines = ["### 🤝 Connect with me", "", "<p align=\"left\">"]
        for platform, url in links.items():
            lines.append(f"  <a href=\"{url}\" target=\"_blank\"><img src=\"https://img.shields.io/badge/{platform}-0077B5?style=flat-square\" alt=\"{platform}\" /></a>")  # noqa: E501
        lines.append("</p>")
        return "\n".join(lines)

    def preview(self) -> str:
        return "### 🤝 Connect with me\n[LinkedIn] [Twitter]"


class QuoteWidget(BaseWidget):
    name = "quote"

    def render(self, data: dict[str, Any]) -> str:
        quote = self._settings.get("quote", "Talk is cheap. Show me the code.")
        author = self._settings.get("author", "Linus Torvalds")
        return f"> \"{quote}\"\n>\n> — *{author}*"

    def preview(self) -> str:
        return "> \"Talk is cheap. Show me the code.\"\n> — Linus Torvalds"


class ActivityGraphWidget(BaseWidget):
    name = "activity_graph"

    def render(self, data: dict[str, Any]) -> str:
        username = data.get("username", "Adithshajee")
        return (
            f"<p align=\"center\">\n"
            f"  <img src=\"https://github-readme-activity-graph.vercel.app/graph?username={username}&theme=github-dark\" alt=\"Activity Graph\" />\n"  # noqa: E501
            f"</p>"
        )

    def preview(self) -> str:
        return "[Activity Graph Mock Diagram]"


class GitHubStreakWidget(BaseWidget):
    name = "github_streak"

    def render(self, data: dict[str, Any]) -> str:
        username = data.get("username", "Adithshajee")
        return (
            f"<p align=\"center\">\n"
            f"  <img src=\"https://github-readme-streak-stats.herokuapp.com/?user={username}&theme=dark\" alt=\"GitHub Streak\" />\n"  # noqa: E501
            f"</p>"
        )

    def preview(self) -> str:
        return "[GitHub Streak Mock Statistics]"


class CustomMarkdownWidget(BaseWidget):
    name = "custom_markdown"

    def render(self, data: dict[str, Any]) -> str:
        markdown = self._settings.get("markdown", "### 🚀 Custom Section\nWrite whatever you want here!")  # noqa: E501
        return str(markdown)

    def preview(self) -> str:
        return "### 🚀 Custom Markdown Section"


# ─── Widget Registry Catalog Manager ──────────────────────────────────────────

class WidgetRegistry:
    """Registry catalogs and instantiates themes/widgets configurations."""

    def __init__(self) -> None:
        self._widgets: dict[str, type[BaseWidget]] = {}
        self._load_builtins()

    def _load_builtins(self) -> None:
        """Register GPS built-in core widgets."""
        builtins = [
            GitHubStatsWidget,
            SnakeWidget,
            BlogWidget,
            RoadmapWidget,
            TechStackWidget,
            VisitorsWidget,
            ContributionGraphWidget,
            MetricsWidget,
            LanguagesWidget,
            PinnedRepositoriesWidget,
            TimelineWidget,
            SponsorsWidget,
            AchievementsWidget,
            CurrentProjectWidget,
            SocialLinksWidget,
            QuoteWidget,
            ActivityGraphWidget,
            GitHubStreakWidget,
            CustomMarkdownWidget,
        ]
        for w in builtins:
            self.register(w)

    def register(self, widget_class: type[BaseWidget]) -> None:
        """Register a new widget class in the registry."""
        self._widgets[widget_class.name] = widget_class

    def get(self, name: str, settings: dict[str, Any] | None = None) -> BaseWidget | None:
        """Instantiate widget by name with settings."""
        widget_class = self._widgets.get(name)
        if not widget_class:
            return None
        return widget_class(settings)

    def list_all(self) -> list[str]:
        """List names of all registered widgets."""
        return list(self._widgets.keys())
