#!/usr/bin/env python3
"""Importa le leggi di revisione costituzionale da italia-corpus.

Estrae gli articoli della Costituzione modificati con approccio ibrido:
1. Prima dal titolo (pattern espliciti: "Modifica all'articolo N", …)
2. Se il titolo non basta, dai blocchi ## Art. N. del testo che contengono
   keyword di modifica (escludendo le sezioni NOTE).

Produce data/revisioni.csv e .parquet.

Uso:
    python3 strumenti/importa-revisioni.py [--corpus-dir DIR] [--output-dir DIR]
"""

from __future__ import annotations

import argparse
import csv
import logging
import re
import sys
from pathlib import Path

logger = logging.getLogger("importa-revisioni")

DEFAULT_CORPUS = (
    Path(__file__).resolve().parent.parent.parent
    / "italia-corpus"
    / "Leggi costituzionali"
)

# ---------------------------------------------------------------------------
# 1. Estrazione dal TITOLO
# ---------------------------------------------------------------------------

# "all'articolo N della Costituzione", "dell'articolo N della Costituzione"
RE_UNO = re.compile(r"(?:all['\u2019]|dell['\u2019])articolo\s+(\d+)\s+della\s+Costituzione", re.IGNORECASE)

# "Modifiche agli articoli N, M e O della Costituzione"
# "Modificazioni agli articoli N, M e O della Costituzione"
# "Modifiche degli articoli N, M e O della Costituzione"
RE_PIU = re.compile(
    r"(?:Modifica|Modifiche|Modificazioni|Modificazione)\s+"
    r"(?:all['\u2019]|degli|agli)\s+articol[oi]\s+"
    r"((?:\d+(?:,\s*|\s+e\s+)*)+)",
    re.IGNORECASE,
)

# "Revisione dell'articolo N della Costituzione"
RE_REV = re.compile(r"Revisione\s+dell['\u2019]articolo\s+(\d+)", re.IGNORECASE)

# "Modifiche al titolo V della parte seconda della Costituzione"
RE_TIT_V = re.compile(r"Modifiche\s+al\s+titolo\s+([VX]+)\s+della\s+parte\s+seconda", re.IGNORECASE)

NUM_RE = re.compile(r"\d+")

TITOLO_MAP: dict[str, list[int]] = {
    "V": list(range(114, 133 + 1)),
}


def _numeri(testo: str) -> list[int]:
    return [int(n) for n in NUM_RE.findall(testo)]


def _estrai_dal_titolo(titolo: str) -> list[int]:
    m = RE_PIU.search(titolo)
    if m:
        return _numeri(m.group(1))
    m = RE_UNO.search(titolo)
    if m:
        return [int(m.group(1))]
    m = RE_REV.search(titolo)
    if m:
        return _numeri(m.group(1))
    m = RE_TIT_V.search(titolo)
    if m:
        return TITOLO_MAP.get(m.group(1), [])
    return []


# ---------------------------------------------------------------------------
# 2. Estrazione dal TESTO (fallback)
# ---------------------------------------------------------------------------

# Keyword che indicano una modifica costituzionale
MOD_KW = [
    "sostituit", "modificat", "aggiunt", "soppress", "apportat",
    "inserit", "abrogat", "premesso",
]

# Header ## Art. N.
ART_HDR = re.compile(r"^##\s+Art\.\s+\d+[^\n]*", re.M)

# Inizio NOTE
NOTE_START = re.compile(r"^Note\s", re.M)

# Link markdown a un articolo della Costituzione: il testo del link
# deve contenere "della Costituzione" o "Costituzione"
ART_LINK = re.compile(
    r"\[([^\]]*(?:della\s+)?Costituzione[^\]]*)\]\([^)]*#art_(\d+)[^)]*\)",
    re.IGNORECASE,
)


def _estrai_dal_testo(testo_completo: str) -> list[int]:
    """Cerca articoli modificati nei blocchi ## Art. N. del testo.

    Esclude frontmatter e sezioni NOTE. Considera solo blocchi con keyword.
    """
    # Rimuovi frontmatter
    testo = re.sub(r"^---.*?---\n*", "", testo_completo, count=1, flags=re.DOTALL)

    headers = list(ART_HDR.finditer(testo))
    if not headers:
        return []

    articoli: set[int] = set()

    for i, h in enumerate(headers):
        start = h.start()
        end = headers[i + 1].start() if i + 1 < len(headers) else len(testo)
        blocco = testo[start:end]

        # Taglia NOTE
        nm = NOTE_START.search(blocco)
        if nm:
            blocco = blocco[: nm.start()]

        # Controlla keyword di modifica
        blocco_lower = blocco.lower()
        if not any(kw in blocco_lower for kw in MOD_KW):
            continue

        # Estrai link #art_N
        for link_m in ART_LINK.finditer(blocco):
            articoli.add(int(link_m.group(2)))

    return sorted(articoli)


# ---------------------------------------------------------------------------
# 3. Classificazione
# ---------------------------------------------------------------------------


def _classifica(titolo: str, articoli_modificati: list[int]) -> str:
    if re.search(
        r"Statuto\s+speciale|statut[oi]\s+speciali|"
        r"Statuto\s+della\s+Regione\s+siciliana|"
        r"Conversione in legge costituzionale dello Statuto|"
        r"Modifica\s+dell['\u2019]articolo\s+\d+\s+dello\s+Statuto|"
        r"Modifiche\s+ed\s+integrazioni\s+agli\s+statuti",
        titolo, re.IGNORECASE,
    ):
        return "statuto_speciale"

    if re.search(
        r"referendum|Proroga del termine|Cessazione degli effetti|"
        r"Soppressione del Senato|Scadenza del termine|"
        r"Norme integrative|Norme sui giudizi|"
        r"Commissione parlamentare|Commissione per le riforme|"
        r"Assegnazione di tre Senatori|Indizione di un",
        titolo, re.IGNORECASE,
    ):
        return "altra_legge_costituzionale"

    if articoli_modificati:
        return "modifica_costituzione"

    return "altra_legge_costituzionale"


# ---------------------------------------------------------------------------
# 4. Frontmatter
# ---------------------------------------------------------------------------


def parse_frontmatter(text: str) -> dict[str, str]:
    m = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not m:
        return {}
    result: dict[str, str] = {}
    for line in m.group(1).split("\n"):
        line = line.strip()
        if ":" in line:
            key, _, value = line.partition(":")
            result[key.strip()] = value.strip().strip('"').strip("'")
    return result


# ---------------------------------------------------------------------------
# 5. I/O
# ---------------------------------------------------------------------------


def scrivi_csv(revisioni: list[dict], path: Path) -> None:
    campi = [
        "urn", "codice_redazionale", "data", "titolo",
        "articoli_modificati", "n_articoli", "tipo",
    ]
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=campi)
        w.writeheader()
        for rev in revisioni:
            row = {k: rev.get(k, "") for k in campi}
            if isinstance(row["articoli_modificati"], list):
                row["articoli_modificati"] = ", ".join(str(a) for a in row["articoli_modificati"])
            w.writerow(row)
    logger.info("Scritto %s con %d righe", path, len(revisioni))


def scrivi_parquet(revisioni: list[dict], path: Path) -> None:
    import pyarrow as pa
    import pyarrow.parquet as pq

    table = pa.table(
        {
            "urn": [r.get("urn", "") for r in revisioni],
            "codice_redazionale": [r.get("codice_redazionale", "") for r in revisioni],
            "data": [r.get("data", "") for r in revisioni],
            "titolo": [r.get("titolo", "") for r in revisioni],
            "articoli_modificati": [r.get("articoli_modificati", []) for r in revisioni],
            "n_articoli": [r.get("n_articoli", 0) for r in revisioni],
            "tipo": [r.get("tipo", "") for r in revisioni],
        }
    )
    pq.write_table(table, str(path))
    logger.info("Scritto %s", path)


# ---------------------------------------------------------------------------
# 6. Main
# ---------------------------------------------------------------------------


def importa_revisioni(corpus_dir: Path) -> list[dict]:
    if not corpus_dir.exists():
        logger.error("Directory non trovata: %s", corpus_dir)
        return []

    md_files = sorted(corpus_dir.glob("*.md"))
    logger.info("Trovati %d file in %s", len(md_files), corpus_dir)

    revisioni: list[dict] = []

    for fpath in md_files:
        text = fpath.read_text("utf-8")
        meta = parse_frontmatter(text)
        titolo = meta.get("titolo", fpath.stem)

        # Ibrido: prima dal titolo, poi fallback sul testo
        articoli = _estrai_dal_titolo(titolo)
        if not articoli:
            articoli = _estrai_dal_testo(text)

        tipo = _classifica(titolo, articoli)

        revisioni.append(
            {
                "urn": meta.get("urn", ""),
                "codice_redazionale": meta.get("codice_redazionale", ""),
                "data": meta.get("data", ""),
                "titolo": titolo,
                "articoli_modificati": articoli,
                "n_articoli": len(articoli),
                "tipo": tipo,
            }
        )

    return revisioni


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus-dir", type=Path, default=DEFAULT_CORPUS)
    parser.add_argument("--output-dir", "-o", type=Path, default=Path("data"))
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s [%(name)s] %(message)s")

    revisioni = importa_revisioni(args.corpus_dir)
    if not revisioni:
        sys.exit(1)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    scrivi_csv(revisioni, args.output_dir / "revisioni.csv")
    scrivi_parquet(revisioni, args.output_dir / "revisioni.parquet")

    n_mod = sum(1 for r in revisioni if r["tipo"] == "modifica_costituzione")
    n_stat = sum(1 for r in revisioni if r["tipo"] == "statuto_speciale")
    n_altre = sum(1 for r in revisioni if r["tipo"] == "altra_legge_costituzionale")
    logger.info(
        "Importate %d leggi: %d modifiche Costituzione, %d statuti speciali, %d altre",
        len(revisioni), n_mod, n_stat, n_altre,
    )


if __name__ == "__main__":
    main()
