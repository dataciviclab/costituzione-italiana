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


def test_parquet_articoli():
    """Il parquet deve avere 139 articoli non-null e Art. 32 queryabile."""
    import pyarrow.parquet as pq

    t = pq.read_table(str(REPO_ROOT / "data/articoli.parquet"))
    assert t.num_rows == 157, f"{t.num_rows} righe, attese 157"

    articoli = t.column("articolo")
    non_null = sum(1 for i in range(len(articoli)) if articoli[i].as_py() is not None)
    assert non_null == 139, f"{non_null} articoli, attesi 139"

    # Art. 32 deve essere presente
    mask = [articoli[i].as_py() == 32 for i in range(len(articoli))]
    assert any(mask), "Art. 32 non trovato nel parquet"

        # Tipo colonna deve essere intero
    assert str(articoli.type) == "int64", f"Tipo {articoli.type}, atteso int64"


def test_corte_csv_esiste():
    """Il file atti-promovimento.csv deve esistere e avere almeno 1000 righe."""
    csv_path = REPO_ROOT / "data" / "atti-promovimento.csv"
    assert csv_path.exists()
    lines = csv_path.read_text("utf-8").strip().split("\n")
    assert len(lines) >= 1001, f"{len(lines)} righe, attese almeno 1001"


def test_corte_parquet():
    """Il parquet deve avere ~1100 record e art. 3 tra i parametri."""
    import pyarrow.parquet as pq

    t = pq.read_table(str(REPO_ROOT / "data" / "atti-promovimento.parquet"))
    assert t.num_rows >= 1000, f"{t.num_rows} righe, attese >= 1000"

    # Art. 3 deve essere presente
    artt = t.column("parametro_articolo")
    assert any(artt[i].as_py() == 3 for i in range(len(artt))), "Art. 3 non trovato"

    # Deve avere entrambi i tipi
    tipi = set(t.column("tipo").to_pylist())
    assert "ordinanza" in tipi
    assert "ricorso" in tipi


def test_revisioni_csv_esiste():
    """Il file revisioni.csv deve esistere e avere 50 righe."""
    csv_path = REPO_ROOT / "data" / "revisioni.csv"
    assert csv_path.exists()
    lines = csv_path.read_text("utf-8").strip().split("\n")
    assert len(lines) == 51, f"{len(lines)} righe (inclusa header), attese 51"


def test_revisioni_parquet():
    """Il parquet revisioni deve avere 50 leggi e almeno 15 modifiche alla Costituzione."""
    import pyarrow.parquet as pq

    t = pq.read_table(str(REPO_ROOT / "data" / "revisioni.parquet"))
    assert t.num_rows == 50, f"{t.num_rows} righe, attese 50"

    tipi = t.column("tipo")
    n_mod = sum(1 for i in range(len(tipi)) if tipi[i].as_py() == "modifica_costituzione")
    assert n_mod >= 15, f"{n_mod} modifiche, attese almeno 15"

    # Art. 9 deve essere presente tra le modifiche
    articoli = t.column("articoli_modificati")
    art9_presente = False
    for i in range(len(articoli)):
        vals = articoli[i].as_py()
        if vals and 9 in vals:
            art9_presente = True
            break
    assert art9_presente, "Art. 9 non trovato tra le modifiche (legge ambiente 2022)"
