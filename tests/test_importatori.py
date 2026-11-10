"""Contract test sugli importatori XML della Corte costituzionale.

Protegge l'estrazione dei campi annidati del source: ``<collegio>`` contiene
un ``<titolo>`` e ``<testo>`` contiene ``<fatto>``/``<diritto>``. Leggere solo
``.text`` restituisce stringa vuota — era il bug per cui ``collegio`` usciva
100% NULL e il testo integrale si perdeva per il 96% delle pronunce.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
PRONUNCE_SCRIPT = REPO_ROOT / "datasets" / "scripts" / "importa-pronunce.py"
MASSIME_SCRIPT = REPO_ROOT / "datasets" / "scripts" / "importa-massime.py"
ATTI_SCRIPT = REPO_ROOT / "datasets" / "scripts" / "importa-corte-costituzionale.py"

pytestmark = pytest.mark.adapter

XML_PRONUNCIA = """<?xml version="1.0" encoding="UTF-8"?>
<pronunce>
  <pronuncia>
    <pronuncia_testata>
      <anno_pronuncia>2026</anno_pronuncia>
      <numero_pronuncia>192</numero_pronuncia>
      <ecli>ECLI:IT:COST:2026:192</ecli>
      <tipologia_pronuncia>S</tipologia_pronuncia>
      <presidente>AMOROSO</presidente>
      <relatore_pronuncia>ANTONINI</relatore_pronuncia>
      <redattore_pronuncia>ANTONINI</redattore_pronuncia>
      <data_decisione>23/09/2026</data_decisione>
      <data_deposito>09/11/2026</data_deposito>
    </pronuncia_testata>
    <pronuncia_testo>
      <collegio><titolo>LA CORTE COSTITUZIONALE</titolo>composta da:
        Presidente: Giovanni AMOROSO; Giudici: Luca ANTONINI.</collegio>
      <epigrafe>ha pronunciato la seguente<titolo>SENTENZA</titolo>nel giudizio
        di legittimità costituzionale.</epigrafe>
      <testo>
        <fatto>Ritenuto in fatto 1.- Il Tribunale ha sollevato questione.</fatto>
        <diritto>Considerato in diritto 1.- La questione è fondata.</diritto>
      </testo>
      <dispositivo>per questi motivi LA CORTE COSTITUZIONALE dichiara
        l'illegittimità costituzionale.</dispositivo>
    </pronuncia_testo>
  </pronuncia>
</pronunce>
"""


def _load_module(path: Path, name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def pronunce_module() -> ModuleType:
    return _load_module(PRONUNCE_SCRIPT, "importa_pronunce")


def test_collegio_estratto_da_titolo_e_tail(pronunce_module: ModuleType) -> None:
    records = pronunce_module._parse_pronunce_xml(XML_PRONUNCIA.encode("utf-8"))
    assert len(records) == 1
    collegio = records[0]["collegio"]
    assert "LA CORTE COSTITUZIONALE" in collegio
    assert "COSTITUZIONALE composta da:" in collegio
    assert "Presidente: Giovanni AMOROSO" in collegio


def test_epigrafe_estratta(pronunce_module: ModuleType) -> None:
    records = pronunce_module._parse_pronunce_xml(XML_PRONUNCIA.encode("utf-8"))
    epigrafe = records[0]["epigrafe"]
    assert epigrafe.startswith("ha pronunciato la seguente")
    assert "SENTENZA nel giudizio" in epigrafe


def test_testo_include_fatto_e_diritto(pronunce_module: ModuleType) -> None:
    records = pronunce_module._parse_pronunce_xml(XML_PRONUNCIA.encode("utf-8"))
    testo = records[0]["testo"]
    assert "Ritenuto in fatto" in testo
    assert "Considerato in diritto" in testo


def test_dispositivo_estratto(pronunce_module: ModuleType) -> None:
    records = pronunce_module._parse_pronunce_xml(XML_PRONUNCIA.encode("utf-8"))
    assert records[0]["dispositivo"].startswith("per questi motivi")


@pytest.fixture(scope="module")
def massime_module() -> ModuleType:
    return _load_module(MASSIME_SCRIPT, "importa_massime")


XML_MASSIME = """<?xml version="1.0" encoding="UTF-8"?>
<corte_costituzionale_archiviomassime>
  <pronuncia>
    <pronuncia_testata>
      <anno_pronuncia>2015</anno_pronuncia>
      <numero_pronuncia>204</numero_pronuncia>
      <tipologia_pronuncia>S</tipologia_pronuncia>
      <tipologia_giudizio>GIUDIZIO IN VIA PRINCIPALE</tipologia_giudizio>
      <data_decisione>23/09/2015</data_decisione>
      <data_deposito>15/10/2015</data_deposito>
    </pronuncia_testata>
    <massime>
      <massima>
        <numero>38567</numero>
        <titolo>Improcedibilità del ricorso.</titolo>
        <testo>È improcedibile il ricorso.</testo>
        <parametri>
          <parametro><codice>25</codice><descrizione>Costituzione</descrizione><articolo>3</articolo></parametro>
          <parametro><codice>25</codice><descrizione>Costituzione</descrizione><articolo>117</articolo></parametro>
        </parametri>
        <norme>
          <norma><codice>+lrsi</codice><descrizione>delibera legislativa Regione Siciliana</descrizione><numero>782</numero><articolo>17</articolo><comma>2</comma></norma>
          <norma><codice>+lrsi</codice><descrizione>delibera legislativa Regione Siciliana</descrizione><numero>782</numero><articolo>22</articolo></norma>
          <norma><codice>+lrsi</codice><descrizione>delibera legislativa Regione Siciliana</descrizione><numero>782</numero><articolo>23</articolo></norma>
        </norme>
      </massima>
      <massima>
        <numero>38568</numero>
        <titolo>Solo parametro, nessuna norma.</titolo>
        <testo>La questione non è fondata.</testo>
        <parametri>
          <parametro><codice>25</codice><descrizione>Costituzione</descrizione><articolo>24</articolo></parametro>
        </parametri>
      </massima>
      <massima>
        <numero>38569</numero>
        <titolo>Solo norma, nessun parametro.</titolo>
        <testo>Massima di principio.</testo>
        <norme>
          <norma><codice>l</codice><descrizione>legge</descrizione><numero>197</numero><articolo>1</articolo></norma>
        </norme>
      </massima>
    </massime>
  </pronuncia>
</corte_costituzionale_archiviomassime>
"""


def test_massime_una_riga_per_massima(massime_module: ModuleType) -> None:
    """Il parser non deve fare il prodotto cartesiano parametri × norme."""
    records = massime_module._parse_massime_xml(XML_MASSIME.encode("utf-8"))
    assert len(records) == 3
    assert [r["id_massima"] for r in records] == [38567, 38568, 38569]


def test_massime_preserva_le_due_liste(massime_module: ModuleType) -> None:
    records = massime_module._parse_massime_xml(XML_MASSIME.encode("utf-8"))
    first = records[0]
    assert first["n_parametri"] == 2
    assert first["n_norme"] == 3
    assert '"codice": "25"' in first["parametri"]
    assert '"articolo": "117"' in first["parametri"]
    assert '"articolo": "22"' in first["norme"]


def test_massime_non_perde_quelle_con_una_sola_lista(
    massime_module: ModuleType,
) -> None:
    """Le massime con soli parametri o sole norme non devono sparire."""
    records = massime_module._parse_massime_xml(XML_MASSIME.encode("utf-8"))
    solo_parametro = next(r for r in records if r["id_massima"] == 38568)
    solo_norma = next(r for r in records if r["id_massima"] == 38569)
    assert solo_parametro["n_parametri"] == 1
    assert solo_parametro["n_norme"] == 0
    assert solo_norma["n_parametri"] == 0
    assert solo_norma["n_norme"] == 1


@pytest.fixture(scope="module")
def atti_module() -> ModuleType:
    return _load_module(ATTI_SCRIPT, "importa_atti")


XML_ATTI = """<?xml version="1.0" encoding="UTF-8"?>
<registro_ordinanze>
  <atto anno="2026" numero="10">
    <numero_parte>2<norme><norma><descrizione>legge</descrizione><numero>197</numero><articolo>1</articolo><comma>115</comma></norma></norme>
    <parametri>
      <parametro><descrizione>Costituzione</descrizione><articolo>3</articolo></parametro>
      <parametro><descrizione>Convenzione per la salvaguardia diritti dell'uomo</descrizione><articolo>6</articolo></parametro>
    </parametri>
    </numero_parte>
  </atto>
</registro_ordinanze>
"""

XML_CONFLITTO = """<?xml version="1.0" encoding="UTF-8"?>
<confiltto_enti>
  <atto anno="2026" numero="2">
    <norme><norma><descrizione>Decreto</descrizione><numero>20</numero></norma></norme>
    <parametri>
      <parametro><descrizione>Costituzione</descrizione><articolo>117</articolo></parametro>
    </parametri>
  </atto>
</confiltto_enti>
"""


def test_atti_legge_numero_parte(atti_module: ModuleType) -> None:
    records = atti_module.parse_xml(XML_ATTI.encode("utf-8"), "ordinanza")
    assert len(records) == 1
    assert records[0]["numero_parte"] == 2
    assert records[0]["parametro_articolo"] == 3


def test_atti_conflitti_senza_numero_parte(atti_module: ModuleType) -> None:
    """I conflitti hanno norme/parametri direttamente sull'atto (una parte)."""
    records = atti_module.parse_xml(XML_CONFLITTO.encode("utf-8"), "conflitto_enti")
    assert len(records) == 1
    assert records[0]["numero_parte"] == 1
    assert records[0]["tipo"] == "conflitto_enti"
    assert records[0]["parametro_articolo"] == 117
