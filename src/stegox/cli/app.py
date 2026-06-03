"""Typer application factory and global options."""

from __future__ import annotations

import sys
from pathlib import Path

import typer
from rich.console import Console

from stegox import __version__
from stegox.cli import exitcodes
from stegox.cli.commands import (
    audio,
    case,
    config,
    detect,
    doctor,
    image,
    metadata,
    plugin,
    report,
    text,
    version,
    video,
)
from stegox.core.config import load_config
from stegox.core.logging import configure_logging
from stegox.core.paths import user_state_dir
from stegox.plugins.manager import PluginManager

app = typer.Typer(
    no_args_is_help=True,
    add_completion=True,
    rich_markup_mode="rich",
    help="StegoX — local-first steganography, steganalysis, and DFIR toolkit.",
)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"stegox {__version__}")
        raise typer.Exit(code=exitcodes.EXIT_OK)


@app.callback()
def main_callback(
    ctx: typer.Context,
    config: Path | None = typer.Option(None, "--config", help="Path to YAML config file."),
    log_level: str = typer.Option("info", "--log-level", help="Logging level."),
    log_file: Path | None = typer.Option(None, "--log-file", help="Optional log file path."),
    json_logs: bool = typer.Option(False, "--json-logs", help="Emit logs as JSON."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON on stdout."),
    no_color: bool = typer.Option(False, "--no-color", help="Disable ANSI colors."),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Suppress non-error output."),
    allow_network: bool = typer.Option(False, "--allow-network", help="Permit network-requiring plugins."),
    jobs: int = typer.Option(1, "--jobs", "-j", help="Parallel jobs (1 = serial)."),
    no_cache: bool = typer.Option(False, "--no-cache", help="Disable detector result cache."),
    version: bool = typer.Option(False, "--version", callback=_version_callback, is_eager=True, help="Show version."),
) -> None:
    """StegoX global options."""
    config_obj = load_config(config)
    config_obj.plugins_allow_network = allow_network or config_obj.plugins_allow_network
    log_file_path = log_file or (user_state_dir() / "logs" / "stegox.log")
    if not no_cache:
        # Cache is opt-out only; this block exists for future implementation
        pass
    configure_logging(level=log_level, log_file=log_file_path, json_logs=json_logs, quiet=quiet)
    pm = PluginManager(config_obj)
    pm.discover()
    ctx.obj = {
        "config": config_obj,
        "json": json_output,
        "no_color": no_color,
        "quiet": quiet,
        "jobs": jobs,
    }


# Register subcommands
app.add_typer(image.app, name="image")
app.add_typer(audio.app, name="audio")
app.add_typer(video.app, name="video")
app.add_typer(text.app, name="text")
app.add_typer(metadata.app, name="metadata")
app.add_typer(detect.app, name="detect")
app.add_typer(case.app, name="case")
app.add_typer(plugin.app, name="plugin")
app.add_typer(config.app, name="config")
app.add_typer(report.app, name="report")
app.add_typer(doctor.app, name="doctor")
app.add_typer(version.app, name="version")


@app.command("menu")
def menu_cmd(
    ctx: typer.Context,
    no_color: bool = typer.Option(False, "--no-color", help="Disable ANSI colors."),
) -> None:
    """Launch the interactive, options-based menu.

    The menu walks the user through hide, extract, detect, doctor, and
    config operations. All menu actions are thin wrappers over the same
    engine functions the Typer subcommands use.
    """
    from stegox.cli.menu import launch

    cfg = ctx.obj["config"] if ctx.obj else load_config(None)
    console = Console(no_color=no_color, force_terminal=not no_color)
    raise typer.Exit(code=launch(console, cfg))


@app.command("interactive")
def interactive_cmd(
    ctx: typer.Context,
    no_color: bool = typer.Option(False, "--no-color", help="Disable ANSI colors."),
) -> None:
    """Alias for ``stegox menu``."""
    ctx.invoke(menu_cmd, no_color=no_color)


def main(argv: list[str] | None = None) -> int:
    """Console-script entry point.

    When invoked with no arguments, the interactive menu is launched.
    """
    no_args = argv is None and len(sys.argv) == 1
    if no_args:
        cfg = load_config(None)
        configure_logging(level=cfg.logging.level, log_file=user_state_dir() / "logs" / "stegox.log", quiet=False)
        from stegox.cli.menu import launch

        console = Console()
        return launch(console, cfg)
    try:
        app()
    except SystemExit as exc:
        return int(exc.code or 0)
    except Exception as exc:
        from stegox.cli.errors import handle
        return handle(exc)
    return exitcodes.EXIT_OK


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
