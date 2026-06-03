"""Doctor CLI subcommand."""

from __future__ import annotations

import json
import shutil
import sys

import typer

from stegox import __version__
from stegox.core.paths import user_cache_dir, user_config_dir, user_plugin_dir, user_state_dir

app = typer.Typer(help="Diagnose the StegoX environment.")


def _emit(payload: dict) -> None:
    sys.stdout.write(json.dumps(payload, indent=2, default=str))
    sys.stdout.write("\n")


@app.callback()
def doctor_callback() -> None:
    pass


@app.command("run")
def doctor_run(json_output: bool = typer.Option(False, "--json")) -> None:
    """Run all diagnostic checks."""
    checks: list[dict] = []
    checks.append({"name": "python_version", "status": "ok", "detail": sys.version.split()[0]})
    checks.append({"name": "stegox_version", "status": "ok", "detail": __version__})
    for name, path in [
        ("config_dir", user_config_dir()),
        ("state_dir", user_state_dir()),
        ("cache_dir", user_cache_dir()),
        ("plugin_dir", user_plugin_dir()),
    ]:
        checks.append({
            "name": name,
            "status": "ok" if path.exists() else "warning",
            "detail": str(path),
        })
    # ffmpeg probe
    ffmpeg = shutil.which("ffmpeg")
    checks.append({
        "name": "ffmpeg",
        "status": "ok" if ffmpeg else "warning",
        "detail": ffmpeg or "not found (required for video detection)",
    })
    # argon2
    try:
        import argon2  # type: ignore # noqa: F401
        argon2_status = "ok"
    except ImportError:
        argon2_status = "warning (using scrypt/pbkdf2 fallback)"
    checks.append({"name": "argon2", "status": argon2_status, "detail": ""})
    if json_output:
        _emit({"checks": checks})
    else:
        for c in checks:
            typer.echo(f"[{c['status']}] {c['name']}: {c.get('detail', '')}")


__all__ = ["app"]
