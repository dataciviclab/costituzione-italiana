"""Test conversione Wikisource → Markdown."""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_costituzione_md_esiste():
    """Il file Costituzione.md deve esistere."""
    assert (REPO_ROOT / "Costituzione.md").exists()


def test_costituzione_md_frontmatter():
    """Il frontmatter YAML deve contenere i campi obbligatori."""
    content = (REPO_ROOT / "Costituzione.md").read_text("utf-8")
    assert "tipo: COSTITUZIONE" in content
    assert "urn: urn:nir:stato:costituzione:1947-12-27" in content
    assert "codice_redazionale: 047U0001" in content
    assert "vigente: true" in content


def test_costituzione_md_articoli():
    """Devono esserci 139 articoli."""
    content = (REPO_ROOT / "Costituzione.md").read_text("utf-8")
    n = content.count("## Art.")
    assert n == 139, f"Trovati {n} articoli, attesi 139"


def test_costituzione_md_disposizioni():
    """Devono esserci 18 disposizioni transitorie."""
    content = (REPO_ROOT / "Costituzione.md").read_text("utf-8")
    n = content.count("### ")
    # Tolgo le sezioni (che sono anche ###) e conto solo quelle dopo
    # "Disposizioni transitorie e finali"
    idx = content.find("Disposizioni transitorie e finali")
    if idx > 0:
        resto = content[idx:]
        n_disp = len([l for l in resto.split("\n") if l.startswith("### ")])
        assert n_disp >= 18, f"Trovate {n_disp} disposizioni, attese almeno 18"


def test_costituzione_md_senza_ref():
    """Non devono esserci tag <ref> residui."""
    content = (REPO_ROOT / "Costituzione.md").read_text("utf-8")
    assert "<ref>" not in content
    assert "<br" not in content
