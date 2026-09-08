"""Smoke test — verifica che tutte le pagine si compilano senza errori."""

from __future__ import annotations

import py_compile
from pathlib import Path

import pytest

pytestmark = pytest.mark.smoke

PAGES_DIR = Path(__file__).resolve().parent.parent / "pages"


@pytest.mark.parametrize(
    "page",
    sorted(PAGES_DIR.glob("*.py")),
    ids=lambda p: p.stem,
)
def test_page_compiles(page: Path) -> None:
    """Ogni pagina deve compilarsi senza errori di sintassi."""
    py_compile.compile(str(page), doraise=True)


def test_sources_compiles() -> None:
    """sources.py deve compilarsi senza errori di sintassi."""
    sources = Path(__file__).resolve().parent.parent / "sources.py"
    py_compile.compile(str(sources), doraise=True)


def test_app_compiles() -> None:
    """app.py deve compilarsi senza errori di sintassi."""
    app = Path(__file__).resolve().parent.parent / "app.py"
    py_compile.compile(str(app), doraise=True)
