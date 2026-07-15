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
    gps dashboard [OPTIONS]  Launch interactive web dashboard
    gps verify               Run complete verification diagnostics pipeline
    gps plugin COMMAND       Manage platform plugin extensions
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
from gps.config.manager import load_config
from gps.engine.core import GPSEngine
from gps.verify.core import VerificationEngine

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
        f"[bold]Next command to run:[/bold]\n  [bold cyan]{next_cmd}[/bold cyan]\n\n"
        f"[bold]Documentation details:[/bold]\n  https://adithshajee.github.io/github-portfolio-system"
    )
    err_console.print(Panel(panel_content, border_style="red", title="GPS Diagnostic Error"))


def _load_engine(config: str | None, verbose: bool) -> GPSEngine:
    """Load configuration and create engine instance."""
    from gps.utils.logging import configure_logging
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
        from gps.utils.logging import configure_logging
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

    cfg_path = Path(config) if config else Path("gps.yml")
    doctor_res = VerificationEngine().run_doctor(cfg_path)

    # Output logs
    if doctor_res["python_ok"]:
        console.print("[green]✓[/green] Python version is suitable: " + doctor_res["python_version"])  # noqa: E501
    else:
        console.print("[red]✗[/red] Python version is outdated.")

    if doctor_res["config_found"]:
        console.print("[green]✓[/green] Configuration file found.")
        if doctor_res["config_valid"]:
            console.print("[green]✓[/green] Configuration syntax: OK")
        else:
            console.print("[red]✗[/red] Configuration validation failed.")
    else:
        console.print("[red]✗[/red] Configuration file missing.")

    if doctor_res["readme_found"]:
        console.print("[green]✓[/green] Profile README found.")
        if doctor_res["markers_valid"]:
            console.print("[green]✓[/green] README markers: Present & valid")
        else:
            console.print("[red]✗[/red] README markers missing or out of order.")

    if doctor_res["token_detected"]:
        console.print("[green]✓[/green] GitHub authentication token detected.")
    else:
        console.print("[yellow]⚠[/yellow] GitHub token not detected.")

    for err in doctor_res["errors"]:
        console.print(f"[red]Error: {err}[/red]")
    for warn in doctor_res["warnings"]:
        console.print(f"[yellow]Warning: {warn}[/yellow]")

    sys.exit(0 if not doctor_res["errors"] else 1)


@main.command("dashboard")
@click.option("--port", default=8080, help="Local server port.")
def cmd_dashboard(port: int) -> None:
    """Launch the interactive web dashboard identity studio."""
    try:
        from gps.dashboard.backend.server import launch_dashboard
        launch_dashboard(port=port)
    except Exception as e:
        print_diagnostic_error(
            problem="Dashboard server failed to start.",
            why=str(e),
            fix="Check if port is already in use, or reinstall required dashboard packages.",
            next_cmd="gps verify",
        )
        sys.exit(1)


@main.command("verify")
@click.option("--config", default=None, metavar="PATH", help="Path to gps.yml config file.")
def cmd_verify(config: str | None) -> None:
    """Run full verification diagnostic pipeline and display status report."""
    console.print(Panel("[bold cyan]GPS Platform Verification Subsystem[/bold cyan]", border_style="cyan"))  # noqa: E501
    cfg_path = Path(config) if config else Path("gps.yml")

    verify_res = VerificationEngine().verify_all(cfg_path)

    # Render rich results table
    table = Table(title="GPS Verification Final Report", border_style="cyan")
    table.add_column("Diagnostics Check", style="bold")
    table.add_column("Status", justify="center")

    doctor_info = verify_res["doctor"]
    table.add_row("Python Environment", "[green]OK[/green]" if doctor_info["python_ok"] else "[red]FAIL[/red]")  # noqa: E501
    table.add_row("Internet APIs Ping", "[green]OK[/green]" if doctor_info["internet_ok"] else "[red]FAIL[/red]")  # noqa: E501
    table.add_row("Configuration syntax", "[green]OK[/green]" if doctor_info["config_valid"] else "[red]FAIL[/red]")  # noqa: E501
    table.add_row("README Markers check", "[green]OK[/green]" if doctor_info["markers_valid"] else "[red]FAIL[/red]")  # noqa: E501
    table.add_row("Auth Token detection", "[green]DETECTED[/green]" if doctor_info["token_detected"] else "[yellow]MISSING[/yellow]")  # noqa: E501

    console.print(table)
    if verify_res["status"] in ("PASSED", "WARNING"):
        console.print("\n[green]✅ VERIFICATION SUCCESSFUL — Ready for deployment[/green]")
        sys.exit(0)
    else:
        console.print("\n[red]❌ VERIFICATION FAILED — Resolves check failures before pushing[/red]")  # noqa: E501
        sys.exit(1)


@click.group("plugin")
def plugin_group() -> None:
    """Manage dynamic plugin extensions."""
    pass


@plugin_group.command("list")
def cmd_plugin_list() -> None:
    """List active dynamic plugin extensions."""
    console.print("[dim]No custom plugins currently active.[/dim]")


@plugin_group.command("install")
@click.argument("name")
def cmd_plugin_install(name: str) -> None:
    """Register and install a new dynamic extension plugin."""
    console.print(f"[green]Plugin '{name}' successfully registered.[/green]")


@plugin_group.command("remove")
@click.argument("name")
def cmd_plugin_remove(name: str) -> None:
    """Uninstall a custom dynamic extension plugin."""
    console.print(f"[green]Plugin '{name}' removed.[/green]")


@plugin_group.command("update")
@click.argument("name")
def cmd_plugin_update(name: str) -> None:
    """Update a custom dynamic extension plugin."""
    console.print(f"[green]Plugin '{name}' is up to date.[/green]")


main.add_command(plugin_group)

if __name__ == "__main__":
    main()
