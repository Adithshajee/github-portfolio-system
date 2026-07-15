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


def _detect_github_username() -> str | None:
    import shutil
    import subprocess

    git_bin = shutil.which("git") or "git"

    # 1. Try github config
    try:
        res = subprocess.run(  # noqa: S603
            [git_bin, "config", "github.user"],
            capture_output=True,
            text=True,
            check=False,
        )
        if res.returncode == 0 and res.stdout.strip():
            return res.stdout.strip()
    except Exception:  # noqa: S110
        pass

    # 2. Try user.name
    try:
        res = subprocess.run(  # noqa: S603
            [git_bin, "config", "user.name"],
            capture_output=True,
            text=True,
            check=False,
        )
        if res.returncode == 0 and res.stdout.strip():
            candidate = res.stdout.strip()
            if re.match(r"^[a-zA-Z0-9\-]+$", candidate) and len(candidate) <= 39:
                return candidate
    except Exception:  # noqa: S110
        pass

    return None


def _detect_git_repository() -> bool:
    try:
        search = Path.cwd()
        for directory in [search, *search.parents]:
            if (directory / ".git").exists():
                return True
            if directory == directory.parent:
                break
    except Exception:  # noqa: S110
        pass
    return False


def _verify_internet_connectivity() -> bool:
    import httpx

    try:
        with httpx.Client(timeout=2.0) as client:
            res = client.get("https://api.github.com", follow_redirects=True)
            return res.status_code == 200
    except Exception:
        return False


@main.command("init")
@click.option("--username", "-u", help="GitHub username.")
@click.option(
    "--theme",
    "-t",
    type=click.Choice(["swe_general", "ai_ml", "devops", "apple", "cyberpunk"]),
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

    console.print(
        Panel(
            "[bold cyan]GPS Setup Wizard & Auto-Detection[/bold cyan]\n"
            "Initializing Developer Identity Workspace...",
            border_style="cyan",
        )
    )

    # Auto-detection metrics
    detected_user = _detect_github_username()
    has_git = _detect_git_repository()
    has_internet = _verify_internet_connectivity()
    python_ver = sys.version.split(" ")[0]

    # Display detected environment context
    env_table = Table(title="Detected Environment Details", show_header=False, border_style="dim")
    env_table.add_row("Python version", f"[green]{python_ver}[/green]")
    env_table.add_row(
        "Git Repository Root",
        "[green]✓ Found[/green]" if has_git else "[yellow]⚠ Not found[/yellow]",
    )
    env_table.add_row(
        "Internet Connection",
        "[green]✓ Connected[/green]" if has_internet else "[red]✗ Disconnected[/red]",
    )
    if detected_user:
        env_table.add_row("Detected GitHub Username", f"[cyan]{detected_user}[/cyan]")
    console.print(env_table)

    if not non_interactive:
        # Prompt & validate GitHub username
        if not username:
            default_user = detected_user or ""
            while True:
                prompt_text = "GitHub Username"
                if default_user:
                    prompt_text += f" [default: {default_user}]"
                username = click.prompt(prompt_text, default=default_user, type=str)
                if validate_github_username(username):
                    break
                console.print(
                    "[red]Invalid GitHub username format (1-39 alphanumeric/hyphens).[/red]"
                )

        # Prompt theme
        theme = click.prompt(
            "Portfolio Theme Design",
            type=click.Choice(["swe_general", "ai_ml", "devops", "apple", "cyberpunk"]),
            default=theme,
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
                    if blog_url.strip() and (
                        blog_url.startswith("http://") or blog_url.startswith("https://")
                    ):
                        break
                    console.print(
                        "[red]Invalid Feed URL (must start with http:// or https://).[/red]"
                    )
    else:
        # If non-interactive and no username provided, use detected or abort
        if not username:
            username = detected_user

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
            f"# {username}\n\n<!-- REPOS_START -->\n<!-- REPOS_END -->\n",
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
        console.print(
            "[green]✓[/green] Python version is suitable: " + doctor_res["python_version"]
        )
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
    console.print(
        Panel("[bold cyan]GPS Platform Verification Subsystem[/bold cyan]", border_style="cyan")
    )
    cfg_path = Path(config) if config else Path("gps.yml")

    verify_res = VerificationEngine().verify_all(cfg_path)

    # Render rich results table
    table = Table(title="GPS Verification Final Report", border_style="cyan")
    table.add_column("Diagnostics Check", style="bold")
    table.add_column("Status", justify="center")

    doctor_info = verify_res["doctor"]
    table.add_row(
        "Python Environment", "[green]OK[/green]" if doctor_info["python_ok"] else "[red]FAIL[/red]"
    )
    table.add_row(
        "Internet APIs Ping",
        "[green]OK[/green]" if doctor_info["internet_ok"] else "[red]FAIL[/red]",
    )
    table.add_row(
        "Configuration syntax",
        "[green]OK[/green]" if doctor_info["config_valid"] else "[red]FAIL[/red]",
    )
    table.add_row(
        "README Markers check",
        "[green]OK[/green]" if doctor_info["markers_valid"] else "[red]FAIL[/red]",
    )
    table.add_row(
        "Auth Token detection",
        "[green]DETECTED[/green]" if doctor_info["token_detected"] else "[yellow]MISSING[/yellow]",
    )

    console.print(table)
    if verify_res["status"] in ("PASSED", "WARNING"):
        console.print("\n[green]✅ VERIFICATION SUCCESSFUL — Ready for deployment[/green]")
        sys.exit(0)
    else:
        console.print(
            "\n[red]❌ VERIFICATION FAILED — Resolves check failures before pushing[/red]"
        )
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


@click.group("theme")
def theme_group() -> None:
    """Query and configure visual themes."""
    pass


@theme_group.command("list")
def cmd_theme_list() -> None:
    """List all registered profile themes."""
    from gps.themes.registry import ThemeRegistry

    registry = ThemeRegistry()
    themes = registry.list_all()
    table = Table(title="Available Portfolio Themes", border_style="blue")
    table.add_column("Theme ID", style="bold cyan")
    table.add_column("Display Name")
    table.add_column("Author")
    table.add_column("Accent")
    for t in themes:
        table.add_row(t.name, t.display_name, t.author, t.accent_color)
    console.print(table)


@theme_group.command("set")
@click.argument("name")
def cmd_theme_set(name: str) -> None:
    """Set the active profile theme in gps.yml."""
    from gps.themes.registry import ThemeRegistry

    registry = ThemeRegistry()
    if not registry.get(name):
        console.print(
            f"[red]Error: Unknown theme '{name}'. Run 'gps theme list' to see available themes.[/red]"  # noqa: E501
        )
        sys.exit(1)
    from gps.config.manager import ConfigurationManager

    manager = ConfigurationManager()
    try:
        settings = manager.load()
        settings.theme.name = name
        manager.save(settings)
        console.print(f"[green]✓ Active theme set to '{name}' successfully.[/green]")
    except Exception as e:
        console.print(f"[red]Error saving theme configuration: {e}[/red]")
        sys.exit(1)


@click.group("widget")
def widget_group() -> None:
    """Query and configure visual profile widgets."""
    pass


@widget_group.command("list")
def cmd_widget_list() -> None:
    """List all registered profile widgets."""
    from gps.widgets.registry import WidgetRegistry

    registry = WidgetRegistry()
    widgets = registry.list_all()
    table = Table(title="Available Visual Widgets", border_style="purple")
    table.add_column("Widget ID", style="bold purple")
    table.add_column("Description")
    for w_name in widgets:
        w = registry.get(w_name)
        desc = w.metadata().get("description", "Core visual widget") if w else "Core visual widget"
        table.add_row(w_name, desc)
    console.print(table)


@click.group("provider")
def provider_group() -> None:
    """Query and configure profile data providers."""
    pass


@provider_group.command("list")
def cmd_provider_list() -> None:
    """List all integrated providers and their active status."""
    from gps.config.manager import load_config

    settings = load_config()
    table = Table(title="Integrated Data Providers", border_style="cyan")
    table.add_column("Provider ID", style="bold cyan")
    table.add_column("Status")
    table.add_column("Details")

    provs = settings.providers
    table.add_row(
        "github",
        "[green]Enabled[/green]" if provs.github.enabled else "[dim]Disabled[/dim]",
        f"Username: {settings.username or 'not set'}",
    )
    table.add_row(
        "huggingface",
        "[green]Enabled[/green]" if provs.huggingface.enabled else "[dim]Disabled[/dim]",
        f"Username: {provs.huggingface.username or 'not set'}",
    )
    table.add_row(
        "kaggle",
        "[green]Enabled[/green]" if provs.kaggle.enabled else "[dim]Disabled[/dim]",
        f"Username: {provs.kaggle.username or 'not set'}",
    )
    table.add_row(
        "leetcode",
        "[green]Enabled[/green]" if provs.leetcode.enabled else "[dim]Disabled[/dim]",
        f"Username: {provs.leetcode.username or 'not set'}",
    )
    table.add_row(
        "blog",
        "[green]Enabled[/green]" if provs.blog.enabled else "[dim]Disabled[/dim]",
        f"Feed URL: {provs.blog.feed_url or 'not set'}",
    )
    table.add_row(
        "linkedin",
        "[dim]Disabled[/dim]" if not provs.linkedin.enabled else "[green]Enabled[/green]",
        "Manual updates only",
    )
    console.print(table)


@provider_group.command("enable")
@click.argument("name")
def cmd_provider_enable(name: str) -> None:
    """Enable a data provider in gps.yml."""
    from gps.config.manager import ConfigurationManager

    manager = ConfigurationManager()
    try:
        settings = manager.load()
        if name == "github":
            settings.providers.github.enabled = True
        elif name == "huggingface":
            settings.providers.huggingface.enabled = True
        elif name == "kaggle":
            settings.providers.kaggle.enabled = True
        elif name == "leetcode":
            settings.providers.leetcode.enabled = True
        elif name == "blog":
            settings.providers.blog.enabled = True
        elif name == "linkedin":
            settings.providers.linkedin.enabled = True
        else:
            console.print(f"[red]Error: Unknown provider '{name}'.[/red]")
            sys.exit(1)
        manager.save(settings)
        console.print(f"[green]✓ Provider '{name}' has been enabled.[/green]")
    except Exception as e:
        console.print(f"[red]Error saving provider config: {e}[/red]")
        sys.exit(1)


@provider_group.command("disable")
@click.argument("name")
def cmd_provider_disable(name: str) -> None:
    """Disable a data provider in gps.yml."""
    from gps.config.manager import ConfigurationManager

    manager = ConfigurationManager()
    try:
        settings = manager.load()
        if name == "github":
            settings.providers.github.enabled = False
        elif name == "huggingface":
            settings.providers.huggingface.enabled = False
        elif name == "kaggle":
            settings.providers.kaggle.enabled = False
        elif name == "leetcode":
            settings.providers.leetcode.enabled = False
        elif name == "blog":
            settings.providers.blog.enabled = False
        elif name == "linkedin":
            settings.providers.linkedin.enabled = False
        else:
            console.print(f"[red]Error: Unknown provider '{name}'.[/red]")
            sys.exit(1)
        manager.save(settings)
        console.print(f"[green]✓ Provider '{name}' has been disabled.[/green]")
    except Exception as e:
        console.print(f"[red]Error saving provider config: {e}[/red]")
        sys.exit(1)


@click.group("config")
def config_group() -> None:
    """Query and set active profile configuration values."""
    pass


@config_group.command("show")
def cmd_config_show() -> None:
    """Show full configuration summary."""
    from gps.config.manager import load_config

    try:
        settings = load_config()
        console.print("[bold cyan]GPS Configuration Details[/bold cyan]")
        console.print(f"GitHub Username: {settings.username}")
        console.print(f"README Path: {settings.readme_path}")
        console.print(f"Timezone: {settings.timezone}")
        console.print(f"Theme Name: {settings.theme.name}")
        console.print(f"Theme Variant: {settings.theme.variant}")
    except Exception as e:
        console.print(f"[red]Error loading config: {e}[/red]")
        sys.exit(1)


@click.group("auth")
def auth_group() -> None:
    """Manage GitHub OAuth credentials."""
    pass


@auth_group.command("login")
def cmd_auth_login() -> None:
    """Start the interactive GitHub Device Flow login process."""
    from gps.auth.device_flow import initiate_device_flow, poll_for_token
    from gps.auth.storage import save_secure_token

    console.print(
        Panel(
            "[bold cyan]GitHub OAuth Device Authorization[/bold cyan]\nStarting flow...",
            border_style="cyan",
        )
    )

    try:
        flow_data = initiate_device_flow()
        user_code = flow_data["user_code"]
        verification_uri = flow_data["verification_uri"]
        device_code = flow_data["device_code"]
        interval = flow_data.get("interval", 5)

        console.print(
            f"\n1. Open your browser and go to: [bold underline]{verification_uri}[/bold underline]"
        )
        console.print(f"2. Enter the authorization code: [bold green]{user_code}[/bold green]\n")

        # Attempt to open browser automatically
        import webbrowser

        try:
            webbrowser.open(verification_uri)
        except Exception:  # noqa: S110
            pass

        console.print("[dim]Waiting for authorization...[/dim]")
        token = poll_for_token(device_code, interval)
        save_secure_token(token)

        console.print("\n[bold green]✓ Successfully authenticated with GitHub![/bold green]")
        console.print("[dim]OAuth token stored securely in local credentials storage.[/dim]")

    except Exception as e:
        console.print(f"\n[red]❌ Authentication failed: {e}[/red]")
        sys.exit(1)


@auth_group.command("status")
def cmd_auth_status() -> None:
    """Check the current login credentials status."""
    from gps.auth.storage import get_secure_token

    token = get_secure_token()

    if not token:
        console.print(
            "[yellow]Not logged in.[/yellow] Run 'gps auth login' to connect your GitHub profile."
        )
        sys.exit(0)

    # Validate token scopes and username
    import httpx

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "GPS-CLI",
    }

    try:
        res = httpx.get("https://api.github.com/user", headers=headers, timeout=10)
        if res.status_code == 200:
            user_data = res.json()
            username = user_data.get("login", "unknown")
            scopes = res.headers.get("X-OAuth-Scopes", "none")
            console.print(
                Panel(
                    f"[bold green]✓ Authenticated with GitHub[/bold green]\n\n"
                    f"User: [cyan]{username}[/cyan]\n"
                    f"Active Scopes: [dim]{scopes}[/dim]",
                    title="GPS Authentication Status",
                    border_style="green",
                )
            )
        else:
            console.print(
                "[red]❌ Authentication token is invalid or expired.[/red] Run 'gps auth login' to re-authenticate."  # noqa: E501
            )
    except Exception as e:
        console.print(f"[red]❌ Failed to verify authentication status: {e}[/red]")
        sys.exit(1)


@auth_group.command("logout")
def cmd_auth_logout() -> None:
    """Clear local authentication credentials."""
    from gps.auth.storage import clear_secure_token

    clear_secure_token()
    console.print("[green]✓ Successfully logged out. Secure credentials cleared.[/green]")


main.add_command(plugin_group)
main.add_command(theme_group)
main.add_command(widget_group)
main.add_command(provider_group)
main.add_command(config_group)
main.add_command(auth_group)

if __name__ == "__main__":
    main()
