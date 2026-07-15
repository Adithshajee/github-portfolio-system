"""
GPS AI Assistant Subsystem — Multi-Agent Portfolio Advisors
─────────────────────────────────────────────────────────────
Implements Career, README, Theme, Project Ranking, and Documentation agents.
Supports offline heuristic matching and optional external LLM integrations.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class PortfolioAgent:
    """Evaluates repositories list to summarize technologies and recommend showcase configurations."""  # noqa: E501

    def analyze(self, repos: list[dict[str, Any]]) -> dict[str, Any]:
        techs: set[str] = set()
        for r in repos:
            lang = r.get("language")
            if lang:
                techs.add(lang)
            topics = r.get("topics", [])
            for t in topics:
                techs.add(str(t).lower())

        # Propose skills categorizations
        ai_ml = {"pytorch", "tensorflow", "keras", "yolo", "opencv", "numpy", "pandas", "python"}
        devops = {"docker", "kubernetes", "aws", "terraform", "github-actions", "ansible"}

        has_ai = bool(techs.intersection(ai_ml))
        has_devops = bool(techs.intersection(devops))

        if has_ai:
            focus = "Artificial Intelligence & Machine Learning"
            role = "AI Engineer"
        elif has_devops:
            focus = "Cloud Architecture & DevOps Systems"
            role = "DevOps Engineer"
        else:
            focus = "Full-Stack Software Engineering"
            role = "Software Engineer"

        return {
            "focus": focus,
            "role": role,
            "detected_technologies": list(techs)[:15],
        }


class READMEAgent:
    """Generates tailored About Me summaries based on skills and career focus."""

    def generate_about_me(self, name: str, role: str, skills: list[str]) -> str:
        skills_str = ", ".join(skills[:5])
        return (
            f"👋 Hi, I'm {name}! I am a passionate {role} specializing in building scalable systems. "  # noqa: E501
            f"My expertise spans across {skills_str}. "
            f"I focus on writing clean, maintainable code and solving complex software engineering challenges."  # noqa: E501
        )


class ThemeAgent:
    """Recommends portfolio theme templates based on technologies and role."""

    def recommend(self, role: str) -> str:
        role_lower = role.lower()
        if "ai" in role_lower or "ml" in role_lower or "data" in role_lower:
            return "ai_ml"
        elif "devops" in role_lower or "cloud" in role_lower or "infra" in role_lower:
            return "devops"
        return "swe_general"


class ProjectRankingAgent:
    """Ranks and recommends repositories to pin based on quality metrics (stars, activity)."""

    def rank_repos(self, repos: list[dict[str, Any]]) -> list[dict[str, Any]]:
        scored = []
        for r in repos:
            stars = r.get("stargazers_count", 0)
            forks = r.get("forks_count", 0)
            has_desc = 1 if r.get("description") else 0
            is_fork = r.get("fork", False)

            if is_fork:
                score = stars * 0.5
            else:
                score = stars * 1.5 + forks * 1.0 + has_desc * 5.0

            scored.append((score, r))

        # Sort descending by score
        scored.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in scored]

    def analyze_repo_health(self, repo: dict[str, Any]) -> dict[str, Any]:
        """Expose quality scores (0-100) and actionable improvement suggestions for a repo."""
        score = 70
        improvements = []

        if repo.get("description"):
            score += 10
        else:
            improvements.append("Add a description to the repository.")

        has_docs = repo.get("has_wiki", False) or "docs" in repo.get("topics", [])
        if has_docs:
            score += 10
        else:
            improvements.append("Add a documentation folder or enable Wiki.")

        if repo.get("stargazers_count", 0) > 0:
            score += 10
        else:
            improvements.append("Add a Roadmap or architectural diagram to attract stargazers.")

        score = min(score, 100)
        return {
            "name": repo.get("name", "Unknown"),
            "score": score,
            "documentation": "9/10" if score > 80 else "6/10",
            "tests": "8/10" if score > 75 else "5/10",
            "ci": "10/10" if score > 80 else "5/10",
            "improvements": improvements or [
                "Add Architecture Diagram",
                "Add Benchmark Section",
                "Add Contributing Guide",
                "Add Roadmap"
            ]
        }


class CareerAgent:
    """Configures career-specific settings for templates variables (DevOps vs AI)."""

    def configure_profile(self, role: str) -> dict[str, Any]:
        if role.lower() == "devops":
            return {
                "theme": {"name": "devops", "variant": "dark"},
                "sections": {
                    "analytics": {"show_snake": True, "show_metrics": True},
                    "tech_stack": {"enabled": True},
                },
            }
        elif role.lower() == "ai_engineer":
            return {
                "theme": {"name": "ai_ml", "variant": "dark"},
                "sections": {
                    "analytics": {"show_snake": False, "show_metrics": True},
                    "engineering_map": {"enabled": True},
                },
            }
        return {
            "theme": {"name": "swe_general", "variant": "dark"},
            "sections": {"analytics": {"show_metrics": True}},
        }

    def compute_developer_identity_score(self, settings: Any) -> dict[str, Any]:  # noqa: ANN401
        """Compute overall developer profile identity score (0-100) with recommendations."""
        score = 50
        strengths = []
        weaknesses = []
        recommendations = []

        if settings.username:
            score += 15
            strengths.append("GitHub profile username is set")
        else:
            weaknesses.append("GitHub username is empty")
            recommendations.append("Set your GitHub username in the profile page")

        p_list = (
            settings.providers.huggingface,
            settings.providers.leetcode,
            settings.providers.blog,
        )
        providers_count = sum(1 for p in p_list if p.enabled)
        if providers_count >= 2:
            score += 20
            strengths.append("Diverse multi-platform presence enabled")
        elif providers_count == 1:
            score += 10
            strengths.append("Basic platform integrations configured")
        else:
            weaknesses.append("No secondary developer platforms enabled")
            recommendations.append("Enable Hugging Face, LeetCode, or Blog Feed integrations")

        if settings.providers.github.include_pinned:
            score += 15
            strengths.append("Flagship project showcases enabled")
        else:
            weaknesses.append("Pinned repositories showcase disabled")
            recommendations.append("Enable pinned repositories showcase to display key projects")

        score = min(score, 100)
        return {
            "score": score,
            "strengths": strengths or ["Consistent commits", "Flagship project configured"],
            "weaknesses": weaknesses or ["Sparse secondary descriptions"],
            "recommendations": recommendations or [
                "Add a portfolio website",
                "Enable discussion tab",
            ]
        }


class DocumentationAgent:
    """Advises on documentation structures and reports checklist warnings."""

    def advise(self, workspace_path: str) -> list[str]:
        return [
            "Add a design decisions document under docs/design-decisions.md",
            "Generate setup guide reference using mkdocs templates",
        ]


class ProfileOptimizerAgent:
    """Analyzes profile elements, identifies skill gaps, and recommends updates."""

    def analyze_gaps(self, current_skills: list[str], detected_techs: list[str]) -> list[str]:
        missing = [t for t in detected_techs if t.lower() not in [s.lower() for s in current_skills]]  # noqa: E501
        return missing

    def compute_readme_score(self, content: str) -> dict[str, Any]:
        """Compute README quality score (0-100) based on content indicators."""
        score = 60
        if "badge" in content.lower() or "img.shields.io" in content.lower():
            score += 10
        if "install" in content.lower() or "setup" in content.lower():
            score += 10
        if "example" in content.lower() or "usage" in content.lower() or "```" in content:
            score += 15
        if "screenshot" in content.lower() or "preview" in content.lower():
            score += 5

        score = min(score, 100)
        return {
            "score": score,
            "badges_rating": "Excellent" if "img.shields.io" in content else "Missing",
            "installation_rating": "Detailed" if "install" in content.lower() else "Basic",
            "examples_rating": "Rich" if "```" in content else "None",
            "recruiter_friendliness": f"{score - 5}%"
        }
