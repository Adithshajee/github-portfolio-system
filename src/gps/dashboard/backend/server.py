"""
GPS Dashboard Backend FastAPI Server
─────────────────────────────────────
Defines API endpoints for layout preview, config updates, auto-detection,
career agent optimizations, health audits, and static UI file serving.
"""

from __future__ import annotations

import logging
import webbrowser
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from gps.config.manager import ConfigurationManager, GPSSettings
from gps.engine.core import GPSEngine
from gps.storage.manager import StorageManager
from gps.utils.discovery import DiscoveryEngine
from gps.verify.core import VerificationEngine

logger = logging.getLogger(__name__)

app = FastAPI(title="GPS Developer Identity Platform Dashboard", version="3.0.0")

# Setup CORS for development convenience
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Shared subsystems instances
config_mgr = ConfigurationManager()
storage_mgr = StorageManager()
verify_engine = VerificationEngine()
discovery_engine = DiscoveryEngine()


class ConfigSaveRequest(BaseModel):
    settings: dict[str, Any]


class AIAskRequest(BaseModel):
    name: str = "Developer"
    role: str = "Software Engineer"
    skills: list[str] = []
    repos: list[dict[str, Any]] = []


@app.get("/api/config")
def get_config() -> dict[str, Any]:
    """Load and return current configuration settings."""
    try:
        settings = config_mgr.load()
        # Return serialized config
        return settings.model_dump()
    except FileNotFoundError:
        # Return sensible default settings dictionary
        return {
            "username": "",
            "readme_path": "profile/README.md",
            "timezone": "UTC",
            "theme": {"name": "swe_general", "variant": "dark"},
            "providers": {
                "github": {"enabled": True, "repo_count": 5},
                "huggingface": {"enabled": False},
                "kaggle": {"enabled": False},
                "leetcode": {"enabled": False},
                "blog": {"enabled": False},
            },
            "sections": {
                "order": ["hero", "professional_overview", "skills", "active_repos", "contact"]
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to load config: {e}") from e


@app.post("/api/config")
def save_config(req: ConfigSaveRequest) -> dict[str, str]:
    """Save modified settings back to gps.yml configuration file."""
    try:
        settings = GPSSettings.model_validate(req.settings)
        config_mgr.save(settings)
        return {"status": "success", "message": "Configuration saved successfully."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Validation failed: {e}") from e


@app.post("/api/preview")
def get_preview(settings_dict: dict[str, Any]) -> dict[str, str]:
    """Render preview README layout without writing to filesystem."""
    try:
        settings = GPSSettings.model_validate(settings_dict)
        engine = GPSEngine(settings)

        # Build mock dataset to bypass real API calls during rapid UI editing
        from datetime import datetime

        from gps.providers.github.models import GitHubRepo
        mock_repos = [
            GitHubRepo(
                name="AI-Driven-Tool-Tracking",
                html_url="https://github.com",
                description="Real-time tool tracking using YOLOv8",
                stargazers_count=12,
                forks_count=2,
                updated_at=datetime.fromisoformat("2026-07-15T00:00:00"),
                fork=False,
            )
        ]

        # Render using the transient engine
        rendered = engine.renderer.render_sections(
            order=settings.sections.order,
            theme_engine=engine.theme_engine,
            context={"username": settings.username, "repositories": mock_repos},
        )
        return {"markdown": rendered}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Preview compilation error: {e}") from e


@app.post("/api/generate")
def generate_profile(settings_dict: dict[str, Any]) -> dict[str, Any]:
    """Execute full provider data fetch and generate production files."""
    try:
        settings = GPSSettings.model_validate(settings_dict)
        config_mgr.save(settings)

        engine = GPSEngine(settings)
        results = engine.run(dry_run=False)
        return {
            "status": "success",
            "updated_sections": list(results.keys()),
            "message": f"Successfully generated profile. Updated {len(results)} sections."
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Generation failed: {e}") from e


@app.get("/api/doctor")
def run_doctor() -> dict[str, Any]:
    """Run diagnostics checks and return unified status report."""
    try:
        return verify_engine.verify_all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/detect")
def auto_detect(username: str) -> dict[str, Any]:
    """Auto-detect developer profiles and accounts across services."""
    if not username.strip():
        raise HTTPException(status_code=400, detail="Username is required.")
    return discovery_engine.auto_detect(username)


@app.post("/api/ai/optimize")
def optimize_profile(req: AIAskRequest) -> dict[str, Any]:
    """Trigger multi-agent advisors to recommend profile parameters and templates."""
    try:
        from gps.ai.agents import (
            CareerAgent,
            PortfolioAgent,
            ProjectRankingAgent,
            READMEAgent,
            ThemeAgent,
        )

        portfolio = PortfolioAgent()
        readme_agent = READMEAgent()
        theme_agent = ThemeAgent()
        ranking = ProjectRankingAgent()
        career = CareerAgent()

        # 1. Analyze portfolio
        analysis = portfolio.analyze(req.repos)

        # 2. Get theme recommendation
        rec_theme = theme_agent.recommend(req.role)

        # 3. Generate narratives summary
        about_me = readme_agent.generate_about_me(req.name, req.role, req.skills)

        # 4. Rank repositories
        ranked = ranking.rank_repos(req.repos)
        pinned_suggestions = [str(r.get("name")) for r in ranked[:3] if r.get("name") is not None]

        # 5. Build settings configurations proposal
        config_proposal = career.configure_profile(req.role)

        return {
            "role": req.role,
            "theme_recommendation": rec_theme,
            "about_me_narrative": about_me,
            "pinned_suggestions": pinned_suggestions,
            "config_diff": config_proposal,
            "portfolio_analysis": analysis,
            "explanation": (
                f"Optimized profile for '{req.role}' role. Recommending theme '{rec_theme}' "
                f"and prioritizing pinned projects: {', '.join(pinned_suggestions)}."
            ),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

@app.post("/api/ai/health")
def get_ai_health(settings_dict: dict[str, Any]) -> dict[str, Any]:
    """Calculate and return Repository Health, README Quality, and Developer Identity scores."""
    try:
        settings = GPSSettings.model_validate(settings_dict)

        # 1. Compute Developer Identity Score
        from gps.ai.agents import CareerAgent, ProfileOptimizerAgent, ProjectRankingAgent
        career = CareerAgent()
        identity_report = career.compute_developer_identity_score(settings)

        # 2. Compute README Quality Score
        engine = GPSEngine(settings)
        from datetime import datetime

        from gps.providers.github.models import GitHubRepo
        mock_repos = [
            GitHubRepo(
                name="AetherOS",
                html_url="https://github.com",
                description="Next-gen modular microkernel OS in Rust",
                stargazers_count=145,
                forks_count=18,
                updated_at=datetime.fromisoformat("2026-07-15T00:00:00"),
                fork=False,
            )
        ]
        rendered = engine.renderer.render_sections(
            order=settings.sections.order,
            theme_engine=engine.theme_engine,
            context={"username": settings.username, "repositories": mock_repos},
        )

        optimizer = ProfileOptimizerAgent()
        readme_report = optimizer.compute_readme_score(rendered)

        # 3. Compute Repo Health report
        ranker = ProjectRankingAgent()
        repo_data = {
            "name": "AetherOS",
            "description": "Next-gen modular microkernel OS in Rust",
            "stargazers_count": 145,
            "forks_count": 18,
            "fork": False,
            "has_wiki": True,
            "topics": ["rust", "os", "kernel"]
        }
        repo_health = ranker.analyze_repo_health(repo_data)

        return {
            "identity": identity_report,
            "readme": readme_report,
            "repository": repo_health,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


def launch_dashboard(host: str = "127.0.0.1", port: int = 8080) -> None:
    """Start local uvicorn FastAPI server and launch default browser."""
    static_dir = Path(__file__).parent.parent / "static"
    if static_dir.exists():
        app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")

    url = f"http://{host}:{port}"
    logger.info("Starting dashboard at %s", url)
    print(f"\n🚀 Launching GPS Dashboard at: {url}\n")

    webbrowser.open(url)
    uvicorn.run(app, host=host, port=port, log_level="warning")
