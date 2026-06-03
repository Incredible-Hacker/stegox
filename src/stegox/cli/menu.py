"""Interactive menu interface for StegoX.

Provides a guided, options-based front end that walks the user through
common operations (hide, extract, detect, analyze) without needing to
remember CLI flags. The menu reuses the same engine entry points as the
Typer subcommands, so the on-disk behavior is identical.

The menu is launched by ``stegox menu`` and can also be entered
implicitly when ``stegox`` is invoked with no subcommand.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, IntPrompt, Prompt
from rich.table import Table

from stegox import __version__
from stegox.core.config import Config
from stegox.core.errors import StegoXError
from stegox.core.logging import get_logger
from stegox.core.paths import (
    default_config_path,
    user_cache_dir,
    user_config_dir,
    user_plugin_dir,
    user_state_dir,
)

log = get_logger("cli.menu")

MEDIA_TYPES: tuple[str, ...] = ("image", "audio", "video", "text", "metadata")

# Strategies that always need a password (always encrypted framing)
_PASSWORD_REQUIRED: frozenset[str] = frozenset(
    {"password-embed", "pcm-lsb-rand", "echo-hiding", "phase-coding"}
)

# Strategies that take an optional password via an encrypted strategy id
_OPTIONAL_PASSWORD: frozenset[str] = frozenset(
    {"lsb", "lsb-rgb", "randomized-lsb", "pcm-lsb", "frame-lsb", "frame-lsb-rand",
     "motion-region", "zero-width", "whitespace", "homoglyph", "homoglyph-advanced",
     "dct-jpeg", "keyframe-dct", "spread-spectrum"}
)

# Strategies that require payload_bytes on extract
_NEEDS_PAYLOAD_BYTES: frozenset[str] = frozenset(
    {"lsb", "lsb-rgb", "randomized-lsb", "pcm-lsb", "pcm-lsb-rand",
     "frame-lsb", "frame-lsb-rand", "echo-hiding", "phase-coding",
     "dct-jpeg", "keyframe-dct", "spread-spectrum"}
)


# ---------------------------------------------------------------------------
# Strategy catalogue (one per media type)
# ---------------------------------------------------------------------------


def _strategies_for(media: str) -> list[dict[str, Any]]:
    """Return the strategy catalogue for ``media`` from the module API."""
    if media == "image":
        from stegox.modules.image import list_strategies
        return list_strategies()
    if media == "audio":
        from stegox.modules.audio import list_strategies
        return list_strategies()
    if media == "video":
        from stegox.modules.video import list_strategies
        return list_strategies()
    if media == "text":
        from stegox.modules.text import list_strategies
        return list_strategies()
    if media == "metadata":
        from stegox.modules.metadata import list_strategies
        return list_strategies()
    return []


# ---------------------------------------------------------------------------
# Menu class
# ---------------------------------------------------------------------------


class InteractiveMenu:
    """Stateful interactive menu loop."""

    def __init__(self, console: Console, config: Config) -> None:
        self.console = console
        self.config = config
        self.running = True

    # ---- top-level loop -------------------------------------------------

    def run(self) -> None:
        """Display the menu and dispatch to the chosen action until exit."""
        self._print_banner()
        while self.running:
            try:
                self._show_main_menu()
                choice = self._prompt_choice(
                    "Select an action",
                    [
                        ("1", "Hide a payload"),
                        ("2", "Extract a payload"),
                        ("3", "Detect / analyze a file"),
                        ("4", "List available strategies"),
                        ("5", "Run diagnostics (doctor)"),
                        ("6", "Show current configuration"),
                        ("0", "Exit"),
                    ],
                )
                self._dispatch(choice)
            except KeyboardInterrupt:
                self.console.print("\n[dim]interrupted[/dim]")
                if Confirm.ask("Exit StegoX?", default=True):
                    self.running = False
            except EOFError:
                self.console.print("\n[dim]stdin closed; exiting[/dim]")
                self.running = False

    def _print_banner(self) -> None:
        self.console.clear()
        self.console.print(
            Panel.fit(
                f"[bold cyan]StegoX[/bold cyan] [dim]v{__version__}[/dim]\n"
                "[dim]local-first steganography, steganalysis, and DFIR toolkit[/dim]",
                border_style="cyan",
            )
        )

    # ---- main menu ------------------------------------------------------

    def _show_main_menu(self) -> None:
        table = Table.grid(padding=(0, 2))
        table.add_column(style="bold cyan", justify="right")
        table.add_column()
        table.add_row("[1]", "Hide a payload into a cover file")
        table.add_row("[2]", "Extract a payload from a stego file")
        table.add_row("[3]", "Run detectors / build a report on a file")
        table.add_row("[4]", "List available strategies (image/audio/...)")
        table.add_row("[5]", "Run diagnostics ([italic]doctor[/italic])")
        table.add_row("[6]", "Show current configuration")
        table.add_row("[0]", "Exit")
        self.console.print(Panel(table, title="Main menu", border_style="green"))

    def _dispatch(self, choice: str) -> None:
        if choice == "0":
            self.running = False
            self.console.print("[cyan]Goodbye.[/cyan]")
            return
        if choice == "1":
            self._menu_hide()
        elif choice == "2":
            self._menu_extract()
        elif choice == "3":
            self._menu_detect()
        elif choice == "4":
            self._menu_list_strategies()
        elif choice == "5":
            self._menu_doctor()
        elif choice == "6":
            self._menu_show_config()
        self._pause()

    # ---- hide -----------------------------------------------------------

    def _menu_hide(self) -> None:
        self.console.print(Panel("[bold]Hide a payload[/bold]", border_style="blue"))
        media = self._pick_media("Hide into which kind of media?")
        strategies = _strategies_for(media)
        if not strategies:
            self._error(f"no strategies available for {media}")
            return
        strategy_id = self._pick_strategy(strategies, "Select an embed strategy")
        needs_pw = self._strategy_needs_password(strategy_id)
        cover = self._prompt_path("Cover file", must_exist=True, must_be_file=True)
        if cover is None:
            return
        payload = self._prompt_path("Payload file (the data to embed)", must_exist=True, must_be_file=True)
        if payload is None:
            return
        default_out = self._default_stego_path(cover)
        out = self._prompt_path(
            "Output (stego) file",
            must_exist=False,
            default=str(default_out),
        )
        if out is None:
            return
        password: str | None = None
        if needs_pw:
            password = self._prompt_password("Password (required)", confirm=True)
            if password is None:
                return
        elif Confirm.ask("Encrypt the payload with a password?", default=False):
            password = self._prompt_password("Password", confirm=True)
            if password is None:
                return

        try:
            from stegox.engine import hide as engine_hide
            payload_bytes = payload.read_bytes() if isinstance(payload, Path) else Path(payload).read_bytes()
            result = engine_hide(
                cover if isinstance(cover, Path) else Path(cover),
                payload_bytes,
                strategy=strategy_id,
                password=password,
                stego=out if isinstance(out, Path) else Path(out),
                media_type=media,
            )
        except StegoXError as exc:
            self._error(str(exc))
            return
        except Exception as exc:
            self._error(f"unexpected error: {exc}")
            return

        self.console.print(
            f"[green]OK[/green] wrote [bold]{result.stego_path}[/bold]\n"
            f"  strategy:    {result.strategy}\n"
            f"  payload:     {result.payload_bytes} bytes\n"
            f"  capacity:    {result.capacity_bytes} bytes\n"
            f"  encrypted:   {result.encrypted}"
        )

    # ---- extract --------------------------------------------------------

    def _menu_extract(self) -> None:
        self.console.print(Panel("[bold]Extract a payload[/bold]", border_style="blue"))
        media = self._pick_media("Extract from which kind of media?")
        strategies = _strategies_for(media)
        if not strategies:
            self._error(f"no strategies available for {media}")
            return
        strategy_id = self._pick_strategy(strategies, "Select an extract strategy")
        needs_pw = self._strategy_needs_password(strategy_id)
        needs_size = strategy_id in _NEEDS_PAYLOAD_BYTES
        stego = self._prompt_path("Stego file", must_exist=True, must_be_file=True)
        if stego is None:
            return
        default_out = stego.with_suffix(".recovered" + stego.suffix) if hasattr(stego, "with_suffix") else Path(str(stego) + ".recovered")
        out = self._prompt_path(
            "Recovered payload output",
            must_exist=False,
            default=str(default_out),
        )
        if out is None:
            return
        password: str | None = None
        if needs_pw or Confirm.ask("Provide the password used during embed?", default=False):
            password = self._prompt_password("Password", confirm=False)
            if password is None:
                return
        payload_bytes: int | None = None
        if needs_size:
            payload_bytes = self._prompt_int(
                "Payload size in bytes",
                default=self._guess_payload_size(stego if isinstance(stego, Path) else Path(stego)),
            )

        try:
            from stegox.engine import extract as engine_extract
            data = engine_extract(
                stego if isinstance(stego, Path) else Path(stego),
                strategy=strategy_id,
                password=password,
                payload_bytes=payload_bytes,
                out=out if isinstance(out, Path) else Path(out),
                media_type=media,
            )
        except StegoXError as exc:
            self._error(str(exc))
            return
        except Exception as exc:
            self._error(f"unexpected error: {exc}")
            return

        self.console.print(
            f"[green]OK[/green] recovered [bold]{len(data)}[/bold] bytes to "
            f"[bold]{out}[/bold]"
        )

    # ---- detect ---------------------------------------------------------

    def _menu_detect(self) -> None:
        self.console.print(Panel("[bold]Detect / analyze[/bold]", border_style="blue"))
        target = self._prompt_path("Target file", must_exist=True, must_be_file=True)
        if target is None:
            return
        only_filter: list[str] | None = None
        if Confirm.ask("Filter to specific detector ids?", default=False):
            raw = Prompt.ask("Comma-separated detector ids (blank for all)")
            only_filter = [d.strip() for d in raw.split(",") if d.strip()] or None
        jobs = self._prompt_int("Parallel jobs", default=1, minimum=1, maximum=64)

        try:
            from stegox.detectors.registry import DetectorRegistry, register_builtin
            if not DetectorRegistry.ids():
                register_builtin()
            from stegox.engine.detect import detect as engine_detect
            from stegox.reports.console import render_console
            from stegox.reports.model import build_report

            scan = engine_detect(
                target if isinstance(target, Path) else Path(target),
                only=only_filter,
                jobs=jobs,
            )
            report = build_report(scan=scan)
            self.console.print(render_console(report))
        except StegoXError as exc:
            self._error(str(exc))
        except Exception as exc:
            self._error(f"unexpected error: {exc}")

    # ---- list strategies ------------------------------------------------

    def _menu_list_strategies(self) -> None:
        self.console.print(Panel("[bold]Available strategies[/bold]", border_style="blue"))
        for media in MEDIA_TYPES:
            strategies = _strategies_for(media)
            if not strategies:
                continue
            table = Table(title=media, show_header=True, header_style="bold magenta")
            table.add_column("ID", style="cyan")
            table.add_column("Encrypted", justify="center")
            table.add_column("Formats")
            table.add_column("Description")
            for s in strategies:
                table.add_row(
                    str(s.get("id", "")),
                    "[green]yes[/green]" if s.get("encrypted") else "[dim]no[/dim]",
                    ", ".join(s.get("formats", [])),
                    s.get("description", ""),
                )
            self.console.print(table)

    # ---- doctor ---------------------------------------------------------

    def _menu_doctor(self) -> None:
        self.console.print(Panel("[bold]Diagnostics[/bold]", border_style="blue"))
        checks: list[dict[str, str]] = []
        import platform
        checks.append({"name": "python_version", "status": "ok", "detail": platform.python_version()})
        checks.append({"name": "stegox_version", "status": "ok", "detail": __version__})
        for name, path in [
            ("config_dir", user_config_dir()),
            ("state_dir", user_state_dir()),
            ("cache_dir", user_cache_dir()),
            ("plugin_dir", user_plugin_dir()),
            ("config_file", default_config_path()),
        ]:
            checks.append(
                {
                    "name": name,
                    "status": "ok" if path.exists() else "warning",
                    "detail": str(path),
                }
            )
        ffmpeg = shutil.which("ffmpeg")
        checks.append(
            {
                "name": "ffmpeg",
                "status": "ok" if ffmpeg else "warning",
                "detail": ffmpeg or "not found (required for video detection)",
            }
        )
        try:
            import argon2  # type: ignore # noqa: F401
            argon2_status = "ok"
        except ImportError:
            argon2_status = "warning (using scrypt/pbkdf2 fallback)"
        checks.append({"name": "argon2", "status": argon2_status, "detail": ""})

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Check", style="cyan")
        table.add_column("Status", justify="center")
        table.add_column("Detail")
        for c in checks:
            status = c["status"]
            color = "green" if status == "ok" else "yellow"
            table.add_row(c["name"], f"[{color}]{status}[/{color}]", c["detail"])
        self.console.print(table)

    # ---- show config ----------------------------------------------------

    def _menu_show_config(self) -> None:
        self.console.print(Panel("[bold]Current configuration[/bold]", border_style="blue"))
        cfg_path = default_config_path()
        self.console.print(f"[dim]config file:[/dim] {cfg_path}")
        if cfg_path.exists():
            self.console.print(f"[dim]last modified:[/dim] {cfg_path.stat().st_mtime}")
        else:
            self.console.print("[dim](no config file on disk; built-in defaults in use)[/dim]")

        from stegox.core.config import save_config
        # Persist a defaults file if none exists so users can edit it.
        if not cfg_path.exists():
            save_config(self.config, cfg_path)
            self.console.print(f"[green]wrote default config to {cfg_path}[/green]")

        with cfg_path.open("r", encoding="utf-8") as fh:
            text = fh.read()
        # Render as syntax-highlighted YAML if pygments is available.
        try:
            from rich.syntax import Syntax
            self.console.print(Syntax(text, "yaml", theme="monokai", word_wrap=True))
        except Exception:
            self.console.print(text)

    # ---- helpers --------------------------------------------------------

    def _prompt_choice(self, label: str, options: list[tuple[str, str]]) -> str:
        """Prompt the user for a numbered choice from ``options``."""
        valid = {opt[0] for opt in options}
        while True:
            raw = Prompt.ask(label, default=options[0][0]).strip()
            if raw in valid:
                return raw
            self._error(f"please choose one of: {', '.join(sorted(valid))}")

    def _pick_media(self, label: str) -> str:
        """Show a numbered list of media types and return the chosen one."""
        table = Table.grid(padding=(0, 2))
        table.add_column(style="bold cyan", justify="right")
        table.add_column()
        for idx, name in enumerate(MEDIA_TYPES, start=1):
            table.add_row(f"[{idx}]", name)
        self.console.print(table)
        while True:
            raw = Prompt.ask(label, default="1").strip()
            try:
                idx = int(raw)
            except ValueError:
                self._error("please enter a number")
                continue
            if 1 <= idx <= len(MEDIA_TYPES):
                return MEDIA_TYPES[idx - 1]
            self._error(f"please choose 1..{len(MEDIA_TYPES)}")

    def _pick_strategy(self, strategies: list[dict[str, Any]], label: str) -> str:
        table = Table.grid(padding=(0, 2))
        table.add_column(style="bold cyan", justify="right")
        table.add_column()
        for idx, s in enumerate(strategies, start=1):
            enc = " [yellow](encrypted)[/yellow]" if s.get("encrypted") else ""
            table.add_row(f"[{idx}]", f"{s.get('id', '?')}{enc}  [dim]- {s.get('description', '')}[/dim]")
        self.console.print(table)
        while True:
            raw = Prompt.ask(label, default="1").strip()
            try:
                idx = int(raw)
            except ValueError:
                self._error("please enter a number")
                continue
            if 1 <= idx <= len(strategies):
                return str(strategies[idx - 1]["id"])
            self._error(f"please choose 1..{len(strategies)}")

    def _prompt_path(
        self,
        label: str,
        *,
        must_exist: bool,
        must_be_file: bool = True,
        default: str | None = None,
    ) -> Path | None:
        """Prompt for a filesystem path with optional validation.

        Returns ``None`` when the user cancels (empty input with no default).
        """
        while True:
            raw = Prompt.ask(label, default=default or "").strip()
            if not raw:
                if default:
                    raw = default
                else:
                    if Confirm.ask("Cancel this step?", default=True):
                        return None
                    continue
            path = Path(raw).expanduser()
            if must_exist and not path.exists():
                self._error(f"path does not exist: {path}")
                if not Confirm.ask("Try again?", default=True):
                    return None
                continue
            if must_be_file and must_exist and not path.is_file():
                self._error(f"not a regular file: {path}")
                if not Confirm.ask("Try again?", default=True):
                    return None
                continue
            return path

    def _prompt_password(self, label: str, *, confirm: bool) -> str | None:
        while True:
            pw = Prompt.ask(label, password=True, default="")
            if not pw:
                if Confirm.ask("Cancel this step?", default=True):
                    return None
                continue
            if confirm:
                pw2 = Prompt.ask("Confirm password", password=True, default="")
                if pw != pw2:
                    self._error("passwords do not match")
                    if not Confirm.ask("Try again?", default=True):
                        return None
                    continue
            return pw

    def _prompt_int(
        self,
        label: str,
        *,
        default: int,
        minimum: int | None = None,
        maximum: int | None = None,
    ) -> int:
        while True:
            try:
                value = IntPrompt.ask(label, default=default)
            except ValueError:
                self._error("please enter an integer")
                continue
            if minimum is not None and value < minimum:
                self._error(f"must be >= {minimum}")
                continue
            if maximum is not None and value > maximum:
                self._error(f"must be <= {maximum}")
                continue
            return value

    @staticmethod
    def _default_stego_path(cover: Path) -> Path:
        """Return a sensible default for the stego output path."""
        return cover.with_name(f"{cover.stem}.stegox{cover.suffix}")

    @staticmethod
    def _guess_payload_size(stego: Path) -> int:
        """Best-effort guess at the embedded payload size from file size."""
        # Heuristic: assume payload is the smaller of 64KiB or 1% of the file
        try:
            sz = stego.stat().st_size
        except OSError:
            return 1024
        return max(64, min(64 * 1024, sz // 100))

    @staticmethod
    def _strategy_needs_password(strategy_id: str) -> bool:
        if strategy_id in _PASSWORD_REQUIRED:
            return True
        # Heuristic: any "password-embed" style id implies encryption
        return strategy_id.startswith("password-")

    def _error(self, message: str) -> None:
        self.console.print(f"[bold red]error:[/bold red] {message}")

    def _pause(self) -> None:
        """Wait for the user to press enter before redrawing the menu."""
        self.console.print()
        try:
            Prompt.ask("[dim]press enter to return to the menu[/dim]", default="")
        except (KeyboardInterrupt, EOFError):
            self.running = False


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def launch(console: Console, config: Config) -> int:
    """Start the interactive menu and return the process exit code."""
    menu = InteractiveMenu(console, config)
    menu.run()
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(launch(Console(), Config()))
