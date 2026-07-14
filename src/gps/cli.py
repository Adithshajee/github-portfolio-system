"""
GPS CLI — Command Line Interface
──────────────────────────────────
Usage:
    gps run [OPTIONS]        Run the GPS engine
    gps validate             Validate configuration and README markers
    gps status               Show provider status and rate limits
    gps export [OPTIONS]     Export provider data

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
"""

from __future__ import annotations

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
    GPS — GitHub Portfolio System v2

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
        err_console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)
    except Exception as e:
        err_console.print(f"[red]Unexpected error:[/red] {e}")
        if verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)


@main.command("validate")
@click.option("--config", default=None, metavar="PATH", help="Path to gps.yml config file.")
@click.option("--verbose", "-v", is_flag=True, help="Enable debug logging.")
def cmd_validate(config: str | None, verbose: bool) -> None:
    """Validate configuration and README markers."""
    engine = _load_engine(config, verbose)
    ok = engine.validate()
    sys.exit(0 if ok else 1)


@main.command("status")
@click.option("--config", default=None, metavar="PATH", help="Path to gps.yml config file.")
def cmd_status(config: str | None) -> None:
    """Show provider status, rate limits, and configuration summary."""
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
    engine = _load_engine(config, verbose)

    if fmt == "json":
        engine.settings.outputs.json = True
        engine.run(dry_run=False)
        console.print("[green]✓ JSON export complete.[/green]")
    elif fmt == "html":
        console.print(
            "[yellow]HTML export is not yet fully implemented in GPS v2.0.[/yellow]\n"
            "Track progress at: https://github.com/Adithshajee/github-portfolio-system/issues"
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
    if not non_interactive:
        if not username:
            username = click.prompt("GitHub Username", type=str)
        if not hf_user:
            if click.confirm("Do you want to enable Hugging Face provider?", default=False):
                hf_user = click.prompt("Hugging Face Username", type=str, default="")
        if not kaggle_user:
            if click.confirm("Do you want to enable Kaggle provider?", default=False):
                kaggle_user = click.prompt("Kaggle Username", type=str, default="")
        if not leetcode_user:
            if click.confirm("Do you want to enable LeetCode provider?", default=False):
                leetcode_user = click.prompt("LeetCode Username", type=str, default="")
        if not blog_url:
            if click.confirm("Do you want to enable Blog RSS provider?", default=False):
                blog_url = click.prompt("Blog RSS Feed URL", type=str, default="")

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

    # Scaffolding directories
    Path("profile").mkdir(parents=True, exist_ok=True)
    readme = Path("profile/README.md")
    if not readme.exists():
        readme.write_text(
            f"# {username}\n\n"
            "<!-- REPOS_START -->\n"
            "<!-- REPOS_END -->\n",
            encoding="utf-8",
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


if __name__ == "__main__":
    main()
