"""Test conversione Wikisource → Markdown e output pipeline."""
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


def test_dataset_yml_per_slug():
    """Ogni dataset deve avere il proprio dataset.yml."""
    datasets_dir = REPO_ROOT / "datasets"
    expected = [
        "articoli", "revisioni", "atti-promovimento", "massime",
        "citazioni-legislative", "pronunce", "giudici",
    ]
    for slug in expected:
        cfg = datasets_dir / slug / "dataset.yml"
        assert cfg.exists(), f"{cfg} mancante"


def test_compose_sentenze_complete():
    """Il compose sentenze-complete deve avere dataset.yml e SQL."""
    compose = REPO_ROOT / "compose" / "sentenze-complete"
    assert (compose / "dataset.yml").exists()
    assert (compose / "sql" / "clean.sql").exists()
    assert (compose / "sql" / "mart_relatore_esiti.sql").exists()
    assert (compose / "sql" / "mart_sentenze_per_articolo.sql").exists()


def test_makefile_esiste():
    """Il Makefile deve avere i target principali."""
    mk = REPO_ROOT / "Makefile"
    assert mk.exists()
    content = mk.read_text()
    assert "run-all" in content
    assert "registry" in content
    assert "check" in content


def test_registry_esiste():
    """Il registry.json deve esistere e avere i dataset."""
    import json
    reg = REPO_ROOT / "registry" / "registry.json"
    assert reg.exists()
    data = json.loads(reg.read_text())
    slugs = {ds["slug"] for ds in data["datasets"]}
    assert "sentenze_complete" in slugs
    assert "massime_corte_costituzionale" in slugs
