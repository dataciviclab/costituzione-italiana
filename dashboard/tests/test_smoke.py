"""Smoke test — verifica che tutte le pagine si compilano senza errori."""

from __future__ import annotations

import ast
import py_compile
from pathlib import Path

import pytest

pytestmark = pytest.mark.smoke

DASH_DIR = Path(__file__).resolve().parent.parent
PAGES_DIR = DASH_DIR / "pages"


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
    py_compile.compile(str(DASH_DIR / "sources.py"), doraise=True)


def test_app_compiles() -> None:
    """app.py deve compilarsi senza errori di sintassi."""
    py_compile.compile(str(DASH_DIR / "app.py"), doraise=True)


def test_sources_uses_public_lab_connectors_api() -> None:
    """policy: sources non importa API private di lab-connectors (underscore)."""
    src = (DASH_DIR / "sources.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    private = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and "lab_connectors" in node.module:
            for alias in node.names:
                if alias.name.startswith("_"):
                    private.append(f"{node.module}.{alias.name}")
    assert not private, f"API private lab-connectors in sources.py: {private}"
    for needle in ("detect_local_root", "load_clean", "load_mart_table", "load_registry"):
        assert needle in src, f"sources.py manca API pubblica: {needle}"


def test_app_registers_all_pages() -> None:
    """Ogni pagina su disco deve essere registrata in app.py."""
    app = (DASH_DIR / "app.py").read_text(encoding="utf-8")
    pages = sorted(p.name for p in PAGES_DIR.glob("*.py"))
    assert pages, "Nessuna pagina in dashboard/pages/"
    for name in pages:
        assert name in app, f"Pagina {name} non registrata in app.py"


def test_iter_page_registered() -> None:
    """Il compose iter_costituzionale deve avere pagina dedicata."""
    assert (PAGES_DIR / "10_Iter.py").is_file()
    app = (DASH_DIR / "app.py").read_text(encoding="utf-8")
    assert "10_Iter.py" in app
