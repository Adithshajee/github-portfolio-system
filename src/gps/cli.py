"""
GPS CLI — Command Line Interface
──────────────────────────────────
Usage:
    gps run [OPTIONS]        Run the GPS engine
    gps validate             Validate configuration and README markers
    gps status               Show provider status and rate limits
    gps export [OPTIONS]     Export provider data
    gps init [OPTIONS]       Initialize a new GPS configuration
    gps doctor [OPTIONS]     Perform workspace health diagnostic checks

Options for `gps run`:
    --dry-run                Print output without writing files
    --provider NAME          Run a specific provider only
    --config PATH            Path to custom gps.yml
    --verbose / -v           Enable DEBUG logging

Examples:
    gps run --dry-run
    gps run --provider github
    gps validate
    gps export --format json
    gps doctor
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from gps import __version__
from gps.config import load_config
from gps.engine import GPSEngine
from gps.utils.logging import configure_logging

try:
    sys.stdout.reconfigure(errors="replace")  # type: ignore[union-attr]
    sys.stderr.reconfigure(errors="replace")  # type: ignore[union-attr]
except (AttributeError, OSError):
    pass

console = Console()
err_console = Console(stderr=True)


def print_diagnostic_error(problem: str, why: str, fix: str, next_cmd: str) -> None:
    """Print a highly formatted, helpful error diagnostic message using rich panels."""
    panel_content = (
        f"[red][bold]Problem:[/bold] {problem}[/red]\n\n"
        f"[bold]Why it happened:[/bold]\n{why}\n\n"
        f"[bold]How to fix it:[/bold]\n{fix}\n\n"
        f"[bold]Next command to run:[/bold]\n  [bold cyan]{next_cmd}[/bold cyan]"
    )
    err_console.print(Panel(panel_content, border_style="red", title="GPS Diagnostic Error"))


def _load_engine(config: str | None, verbose: bool) -> GPSEngine:
    """Load configuration and create engine instance."""
    settings = load_config(Path(config) if config else None)
    configure_logging(
        level="DEBUG" if verbose else settings.logging.level,
        json_format=settings.logging.json_format,
    )
    return GPSEngine(settings)


@click.group()
@click.version_option(__version__, prog_name="GPS")
def main() -> None:
    """
    GPS — GitHub Portfolio System v3.0.0

    Developer Identity Platform. Automates your GitHub profile,
    documentation site, and developer presence across platforms.

    Documentation: https://adithshajee.github.io/github-portfolio-system
    """


@main.command("run")
@click.option("--dry-run", is_flag=True, help="Print output without writing any files.")
@click.option("--provider", default=None, metavar="NAME", help="Run a specific provider only.")
@click.option("--config", default=None, metavar="PATH", help="Path to gps.yml config file.")
@click.option("--verbose", "-v", is_flag=True, help="Enable debug logging.")
def cmd_run(
    dry_run: bool,
    provider: str | None,
    config: str | None,
    verbose: bool,
) -> None:
    """Run the GPS engine to update your profile README."""
    try:
        engine = _load_engine(config, verbose)

        if dry_run:
            console.print(
                Panel(
                    "[yellow]DRY RUN MODE[/yellow] — No files will be written.",
                    border_style="yellow",
                )
            )

        results = engine.run(dry_run=dry_run, provider_filter=provider)

        if results:
            console.print(
                f"\n[green]✓ GPS run completed.[/green] "
                f"Updated [bold]{len(results)}[/bold] provider section(s)."
            )
        else:
            console.print("[yellow]⚠ No provider data was generated.[/yellow]")
            sys.exit(1)

    except FileNotFoundError as e:
        print_diagnostic_error(
            problem="Configuration or target files not found.",
            why=str(e),
            fix="Run 'gps init' to initialize directories, README, and configuration.",
            next_cmd="gps init",
        )
        sys.exit(1)
    except Exception as e:
        print_diagnostic_error(
            problem="Unexpected error during engine execution.",
            why=str(e),
            fix="Run 'gps doctor' to diagnose workspace configuration and dependencies.",
            next_cmd="gps doctor",
        )
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


@main.command("validate")
@click.option("--config", default=None, metavar="PATH", help="Path to gps.yml config file.")
@click.option("--verbose", "-v", is_flag=True, help="Enable debug logging.")
def cmd_validate(config: str | None, verbose: bool) -> None:
    """Validate configuration and README markers."""
    try:
        engine = _load_engine(config, verbose)
        ok = engine.validate()
        sys.exit(0 if ok else 1)
    except FileNotFoundError as e:
        print_diagnostic_error(
            problem="gps.yml configuration file not found.",
            why=str(e),
            fix="Initialize configuration by running 'gps init'.",
            next_cmd="gps init",
        )
        sys.exit(1)
    except Exception as e:
        print_diagnostic_error(
            problem="Configuration validation check encountered an error.",
            why=str(e),
            fix="Run 'gps doctor' to inspect validation errors in detail.",
            next_cmd="gps doctor",
        )
        sys.exit(1)


@main.command("status")
@click.option("--config", default=None, metavar="PATH", help="Path to gps.yml config file.")
def cmd_status(config: str | None) -> None:
    """Show provider status, rate limits, and configuration summary."""
    try:
        settings = load_config(Path(config) if config else None)
        configure_logging(settings.logging.level, settings.logging.json_format)

        table = Table(title="GPS Provider Status", border_style="blue")
        table.add_column("Provider", style="bold")
        table.add_column("Enabled", justify="center")
        table.add_column("Auth", justify="center")
        table.add_column("Notes")

        provider_info = [
            (
                "GitHub",
                settings.providers.github.enabled,
                bool(settings.github_token),
                f"User: {settings.username or 'not set'}, "
                f"Repos: {settings.providers.github.repo_count}",
            ),
            (
                "Hugging Face",
                settings.providers.huggingface.enabled,
                bool(settings.hf_token),
                f"User: {settings.providers.huggingface.username or 'not set'}",
            ),
            (
                "Kaggle",
                settings.providers.kaggle.enabled,
                bool(settings.kaggle_key),
                f"User: {settings.providers.kaggle.username or 'not set'}",
            ),
            (
                "LeetCode",
                settings.providers.leetcode.enabled,
                False,
                f"User: {settings.providers.leetcode.username or 'not set'}",
            ),
            (
                "Blog",
                settings.providers.blog.enabled,
                False,
                f"Feed: {settings.providers.blog.feed_url or 'not set'}",
            ),
            (
                "LinkedIn",
                False,
                False,
                "Manual updates only — see docs/providers/linkedin.md",
            ),
        ]

        for name, enabled, authed, notes in provider_info:
            table.add_row(
                name,
                "[green]✓[/green]" if enabled else "[dim]✗[/dim]",
                "[green]✓[/green]" if authed else "[yellow]No token[/yellow]",
                notes,
            )

        console.print(table)
        console.print(f"\n[dim]GPS v{__version__} | Config: {settings.readme_path}[/dim]")
    except Exception as e:
        print_diagnostic_error(
            problem="Failed to display provider status.",
            why=str(e),
            fix="Initialize configuration by running 'gps init'.",
            next_cmd="gps init",
        )
        sys.exit(1)


@main.command("export")
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["json", "html"], case_sensitive=False),
    default="json",
    help="Export format.",
)
@click.option("--config", default=None, metavar="PATH", help="Path to gps.yml config file.")
@click.option("--verbose", "-v", is_flag=True, help="Enable debug logging.")
def cmd_export(fmt: str, config: str | None, verbose: bool) -> None:
    """Export provider data in the specified format."""
    try:
        engine = _load_engine(config, verbose)

        if fmt == "json":
            engine.settings.outputs.json = True
            engine.run(dry_run=False)
            console.print("[green]✓ JSON export complete.[/green]")
        elif fmt == "html":
            console.print(
                "[yellow]HTML export is not yet fully implemented in GPS v3.0.0.[/yellow]\n"
                "Track progress at: https://github.com/Adithshajee/github-portfolio-system/issues"
            )
            sys.exit(1)
    except Exception as e:
        print_diagnostic_error(
            problem="Data export failed.",
            why=str(e),
            fix="Run 'gps doctor' to verify workspace settings.",
            next_cmd="gps doctor",
        )
        sys.exit(1)


@main.command("init")
@click.option("--username", "-u", help="GitHub username.")
@click.option(
    "--theme",
    "-t",
    type=click.Choice(["swe_general", "ai_ml", "devops"]),
    default="swe_general",
    help="Portfolio theme design.",
)
@click.option("--hf-user", default="", help="Hugging Face username.")
@click.option("--kaggle-user", default="", help="Kaggle username.")
@click.option("--leetcode-user", default="", help="LeetCode username.")
@click.option("--blog-url", default="", help="Blog/RSS feed URL.")
@click.option("--non-interactive", is_flag=True, help="Disable interactive prompting.")
@click.option("--force", "-f", is_flag=True, help="Force overwrite of existing config.")
def cmd_init(
    username: str | None,
    theme: str,
    hf_user: str,
    kaggle_user: str,
    leetcode_user: str,
    blog_url: str,
    non_interactive: bool,
    force: bool,
) -> None:
    """Initialize a new GPS configuration file and workspace."""
    from gps.utils.validators import validate_github_username

    if not non_interactive:
        # Prompt & validate GitHub username
        if not username:
            while True:
                username = click.prompt("GitHub Username", type=str)
                if validate_github_username(username):
                    break
                console.print(
                    "[red]Invalid GitHub username format (1-39 alphanumeric/hyphens).[/red]"
                )

        # Prompt & validate HF username
        if not hf_user:
            if click.confirm("Do you want to enable Hugging Face provider?", default=False):
                while True:
                    hf_user = click.prompt("Hugging Face Username", type=str)
                    if hf_user.strip() and re.match(r"^[a-zA-Z0-9_\-]+$", hf_user):
                        break
                    console.print("[red]Invalid Hugging Face username format.[/red]")

        # Prompt & validate Kaggle username
        if not kaggle_user:
            if click.confirm("Do you want to enable Kaggle provider?", default=False):
                while True:
                    kaggle_user = click.prompt("Kaggle Username", type=str)
                    if kaggle_user.strip() and re.match(r"^[a-zA-Z0-9_\-]+$", kaggle_user):
                        break
                    console.print("[red]Invalid Kaggle username format.[/red]")

        # Prompt & validate LeetCode username
        if not leetcode_user:
            if click.confirm("Do you want to enable LeetCode provider?", default=False):
                while True:
                    leetcode_user = click.prompt("LeetCode Username", type=str)
                    if leetcode_user.strip() and re.match(r"^[a-zA-Z0-9_\-]+$", leetcode_user):
                        break
                    console.print("[red]Invalid LeetCode username format.[/red]")

        # Prompt & validate Blog Feed URL
        if not blog_url:
            if click.confirm("Do you want to enable Blog RSS provider?", default=False):
                while True:
                    blog_url = click.prompt("Blog RSS Feed URL", type=str)
                    if blog_url.strip() and (blog_url.startswith("http://") or blog_url.startswith("https://")):
                        break
                    console.print("[red]Invalid Feed URL (must start with http:// or https://).[/red]")

    if not username:
        console.print("[red]Error: GitHub username is required to initialize GPS.[/red]")
        sys.exit(1)

    dest = Path("gps.yml")
    if dest.exists() and not force:
        if non_interactive or not click.confirm(
            "gps.yml already exists. Overwrite?", default=False
        ):
            console.print("[yellow]Aborted. Existing gps.yml configuration preserved.[/yellow]")
            sys.exit(0)

    # Scaffolding directories & files
    Path("profile").mkdir(parents=True, exist_ok=True)
    readme = Path("profile/README.md")
    if not readme.exists():
        readme.write_text(
            f"# {username}\n\n"
            "<!-- REPOS_START -->\n"
            "<!-- REPOS_END -->\n",
            encoding="utf-8",
        )
    else:
        # Check and inject markers automatically if they are missing
        content = readme.read_text(encoding="utf-8")
        if "<!-- REPOS_START -->" not in content:
            content += "\n\n<!-- REPOS_START -->\n<!-- REPOS_END -->\n"
            readme.write_text(content, encoding="utf-8")
            console.print(
                "[dim]✓ Inserted missing README markers automatically into "
                "existing profile/README.md[/dim]"
            )

    # Write gps.yml
    content = f"""# GPS — Platform Configuration
# Generated automatically by `gps init`.

platform:
  username: "{username}"
  readme_path: "profile/README.md"
  timezone: "UTC"

theme:
  name: "{theme}"
  variant: "dark"

providers:
  github:
    enabled: true
    repo_count: 5
    include_pinned: true
    exclude_forks: true
    exclude_archived: true
    filter_topics: []
  huggingface:
    enabled: {str(bool(hf_user)).lower()}
    username: "{hf_user}"
    model_count: 5
    space_count: 3
  kaggle:
    enabled: {str(bool(kaggle_user)).lower()}
    username: "{kaggle_user}"
  leetcode:
    enabled: {str(bool(leetcode_user)).lower()}
    username: "{leetcode_user}"
  blog:
    enabled: {str(bool(blog_url)).lower()}
    feed_url: "{blog_url}"
  linkedin:
    enabled: false

outputs:
  markdown: true
  json: false
  html: false

sections:
  order:
    - hero
    - professional_overview
    - skills
    - analytics
    - featured_projects
    - active_repos
    - tech_stack
    - engineering_map
    - contact
  hero:
    enabled: true
  professional_overview:
    enabled: true
  skills:
    enabled: true
  analytics:
    enabled: true
    show_snake: true
    show_metrics: true
  featured_projects:
    enabled: true
  active_repos:
    enabled: true
    start_marker: "<!-- REPOS_START -->"
    end_marker: "<!-- REPOS_END -->"
  tech_stack:
    enabled: true
  engineering_map:
    enabled: true
  contact:
    enabled: true

http:
  timeout: 15
  max_retries: 3
  retry_delay: 1.0
  rate_limit_threshold: 10

logging:
  level: "INFO"
  json_format: false
"""
    dest.write_text(content, encoding="utf-8")
    console.print(f"[green]✓ GPS configuration successfully initialized at {dest}[/green]")
    console.print(
        "[dim]Scaffolded directories and created profile/README.md template markers.[/dim]"
    )


@main.command("doctor")
@click.option("--config", default=None, metavar="PATH", help="Path to gps.yml config file.")
def cmd_doctor(config: str | None) -> None:
    """Perform a comprehensive system health check of your GPS workspace."""
    console.print(
        Panel(
            "[bold blue]GPS System Health Check (Doctor)[/bold blue]",
            border_style="blue",
        )
    )

    import os

    has_issues = False

    # 1. Python Version Check
    py_ver = sys.version_info
    if py_ver >= (3, 10):
        console.print("[green]✓[/green] Python version is suitable: " + sys.version.split(" ")[0])
    else:
        console.print("[red]✗[/red] Python version is outdated. Must be >= 3.10.")
        has_issues = True

    # 2. Config File Check
    cfg_path = Path(config) if config else Path("gps.yml")
    settings = None
    if cfg_path.exists():
        console.print(f"[green]✓[/green] Configuration file found at {cfg_path}")
        try:
            settings = load_config(cfg_path)
            console.print("[green]✓[/green] Configuration syntax and validation: OK")
        except Exception as e:
            console.print(f"[red]✗[/red] Configuration validation failed: {e}")
            has_issues = True
    else:
        console.print(f"[red]✗[/red] Configuration file missing at {cfg_path}")
        has_issues = True

    # 3. Profile README Path & Folders Check
    if settings:
        readme_path = Path(settings.readme_path)
        if readme_path.parent.exists():
            console.print(f"[green]✓[/green] Profile directory exists: {readme_path.parent}")
        else:
            console.print(f"[yellow]⚠[/yellow] Profile directory missing: {readme_path.parent}")

        if readme_path.exists():
            console.print(f"[green]✓[/green] Profile README found at {readme_path}")
            content = readme_path.read_text(encoding="utf-8")
            from gps.utils.validators import validate_readme_markers
            start_m = settings.sections.active_repos.start_marker
            end_m = settings.sections.active_repos.end_marker
            if validate_readme_markers(content, start_m, end_m):
                console.print(
                    f"[green]✓[/green] README markers ({start_m} / {end_m}): Present & valid"
                )
            else:
                console.print(
                    f"[red]✗[/red] README markers missing or out of order in {readme_path}"
                )
                has_issues = True
        else:
            console.print(f"[red]✗[/red] Profile README missing at {readme_path}")
            has_issues = True

    # 4. GitHub Token Detection
    gh_token = os.environ.get("GH_PAT") or os.environ.get("GITHUB_TOKEN")
    if gh_token:
        console.print("[green]✓[/green] GitHub authentication token detected (GH_PAT/GITHUB_TOKEN)")
    else:
        console.print(
            "[yellow]⚠[/yellow] GitHub token not detected. "
            "API rate limit will be constrained (60 requests/hr)."
        )

    # 5. Workflows Check
    setup_workflow = Path(".github/workflows/setup.yml")
    sync_workflow = Path(".github/workflows/cron_sync.yml")
    if setup_workflow.exists() and sync_workflow.exists():
        console.print("[green]✓[/green] GitHub Actions onboarding workflows present")
    else:
        console.print(
            "[yellow]⚠[/yellow] GitHub Actions workflows missing or "
            "incomplete (.github/workflows/)"
        )

    # 6. Documentation build check
    doc_config = Path("mkdocs.yml")
    if doc_config.exists():
        console.print("[green]✓[/green] Documentation config (mkdocs.yml) present")
    else:
        console.print("[yellow]⚠[/yellow] mkdocs.yml configuration file not found")

    # 7. Plugins & Theme loader check
    if settings:
        try:
            from gps.engine import GPSEngine
            engine = GPSEngine(settings)
            console.print("[green]✓[/green] Plugin discovery and dynamic loading: OK")

            # Check theme
            theme_name = settings.theme.name
            if engine.theme_engine:
                console.print(f"[green]✓[/green] Theme resolved and compiled: '{theme_name}'")
        except Exception as e:
            console.print(f"[red]✗[/red] Dynamic plugin/theme loading error: {e}")
            has_issues = True

    # 8. GitHub Actions Readiness (Permissions)
    console.print("\n[bold]GitHub Actions Write Permissions check:[/bold]")
    console.print(
        "  Ensure that under Repository Settings -> Actions -> General -> Workflow permissions:\n"
        "  - 'Read and write permissions' is selected\n"
        "  - 'Allow GitHub Actions to create and approve pull requests' is checked\n"
        "  (This is required to allow daily auto-sync commits to write back to the repo)."
    )

    if has_issues:
        console.print(
            "\n[red]✗ Some system health checks failed. "
            "See instructions above to resolve.[/red]"
        )
        sys.exit(1)
    else:
        console.print(
            "\n[green]✓ All critical system health checks passed successfully. "
            "GPS is ready for production![/green]"
        )
        sys.exit(0)


if __name__ == "__main__":
    main()
