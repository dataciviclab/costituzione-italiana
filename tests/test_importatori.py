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
