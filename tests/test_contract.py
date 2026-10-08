"""Contract test per repo dataset multi-dataset (ADR-001).

Verifica la struttura del repo, non il motore del toolkit:
  - layout multi-dataset (datasets/ + compose/)
  - ogni dataset espone un contratto minimo (dataset.yml, SQL dichiarati)
  - i path dichiarati sono relativi e POSIX
  - non si committano output di run (out/)
  - presenza dei componenti condivisi (Makefile, pyproject.toml, workflows)

Markers: contract (contratto pubblico, artifact format).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = REPO_ROOT / "out"
REQUIRED_FILES = [
    REPO_ROOT / "Makefile",
    REPO_ROOT / "pyproject.toml",
    REPO_ROOT / "conftest.py",
    REPO_ROOT / "LICENSE",
    REPO_ROOT / "README.md",
    REPO_ROOT / "CONTRIBUTING.md",
    REPO_ROOT / ".github" / "workflows" / "check.yml",
    REPO_ROOT / ".github" / "workflows" / "pipeline.yml",
]


def _iter_dataset_configs() -> list[Path]:
    configs: list[Path] = []
    for dirname in ("datasets", "compose"):
        base = REPO_ROOT / dirname
        if base.exists():
            configs.extend(sorted(base.glob("*/dataset.yml")))
    return configs


@pytest.fixture(scope="module")
def dataset_configs() -> list[Path]:
    configs = _iter_dataset_configs()
    assert configs, "Il repo deve dichiarare almeno un dataset in datasets/ o compose/"
    return configs


@pytest.mark.contract
def test_required_files_exist() -> None:
    missing = [str(p.relative_to(REPO_ROOT)) for p in REQUIRED_FILES if not p.exists()]
    assert not missing, f"Missing required template files: {missing}"


@pytest.mark.contract
def test_layout_is_multidataset() -> None:
    assert (REPO_ROOT / "datasets").is_dir(), "datasets/ è obbligatoria nel modello multi-dataset"
    assert (REPO_ROOT / "compose").is_dir(), "compose/ deve contenere i cross-dataset"
    root_config = REPO_ROOT / "dataset.yml"
    assert not root_config.exists(), "Nel modello multi-dataset non esiste dataset.yml in root"


@pytest.mark.contract
def test_pyproject_follows_adr8() -> None:
    """toolkit in extra pipeline, non hard-dep; lab-connectors solo extra dashboard."""
    text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'name = "dataciviclab-costituzione-italiana"' in text
    assert "requires-python" in text and ">=3.12" in text
    assert 'setuptools>=68' in text
    # toolkit non deve stare in [project] dependencies
    deps_block = text.split("dependencies = [", 1)[1].split("]", 1)[0]
    assert "dataciviclab-toolkit" not in deps_block, (
        "toolkit deve vivere nell'extra pipeline (ADR-001 §8), non in dependencies"
    )
    assert "pipeline = [" in text and "dataciviclab-toolkit" in text
    # lab-connectors solo nell'extra dashboard (deploy Streamlit standalone)
    assert "lab-connectors" not in deps_block


@pytest.mark.contract
def test_each_dataset_declares_minimum_contract(dataset_configs: list[Path]) -> None:
    for cfg in dataset_configs:
        dataset = yaml.safe_load(cfg.read_text(encoding="utf-8"))
        rel = str(cfg.relative_to(REPO_ROOT))
        assert dataset.get("schema_version") == 1, f"{rel}: schema_version != 1"
        assert "root" in dataset, f"{rel}: manca root (path relativo a out/)"
        assert not str(dataset["root"]).startswith("/"), f"{rel}: root deve essere relativo"
        assert "dataset" in dataset, f"{rel}: manca blocco dataset"
        assert dataset["dataset"].get("name"), f"{rel}: manca dataset.name"
        assert isinstance(dataset["dataset"].get("years"), list), (
            f"{rel}: years deve essere una lista"
        )
        assert dataset["dataset"]["years"], f"{rel}: years non deve essere vuota"
        assert dataset["dataset"].get("source_id"), f"{rel}: manca dataset.source_id"
        assert "raw" in dataset and dataset["raw"].get("sources"), f"{rel}: manca raw.sources"
        assert dataset["raw"]["sources"][0].get("primary") is True, (
            f"{rel}: la prima source deve essere primary"
        )
        assert dataset["clean"]["sql"], f"{rel}: manca clean.sql"
        assert dataset["clean"].get("required_columns"), f"{rel}: manca clean.required_columns"
        assert dataset["clean"]["validate"].get("min_rows"), f"{rel}: manca clean.validate.min_rows"
        assert dataset["mart"]["tables"], f"{rel}: manca mart.tables"
        assert dataset["mart"].get("required_tables"), f"{rel}: manca mart.required_tables"
        assert dataset["mart"]["validate"].get("table_rules"), (
            f"{rel}: manca mart.validate.table_rules"
        )
        assert dataset["validation"]["fail_on_error"] is True, (
            f"{rel}: fail_on_error deve essere true"
        )


def _iter_path_values(node: object):
    if isinstance(node, dict):
        for key, value in node.items():
            if isinstance(value, str) and key in {
                "root",
                "source",
                "sql",
                "target",
                "dir",
                "path",
                "filename",
                "config",
            }:
                yield key, value
            yield from _iter_path_values(value)
    elif isinstance(node, list):
        for item in node:
            yield from _iter_path_values(item)


@pytest.mark.contract
def test_dataset_paths_are_relative_and_posix(dataset_configs: list[Path]) -> None:
    for cfg in dataset_configs:
        dataset = yaml.safe_load(cfg.read_text(encoding="utf-8"))
        rel = str(cfg.relative_to(REPO_ROOT))
        for key, value in _iter_path_values(dataset):
            if value.startswith(("http://", "https://")):
                continue
            assert value, f"{rel}: path vuoto per '{key}'"
            assert "\\" not in value, f"{rel}: path '{key}' deve usare separatori POSIX: {value}"
            assert not value.startswith("/"), f"{rel}: path assoluto POSIX per '{key}': {value}"
            assert not value.startswith("~"), f"{rel}: path home-relative per '{key}': {value}"
            assert not re.match(r"^[A-Za-z]:[\\/]", value), (
                f"{rel}: path Windows per '{key}': {value}"
            )


@pytest.mark.contract
def test_no_absolute_host_paths_in_script_commands(dataset_configs: list[Path]) -> None:
    """Regression: PR #23 — niente path host da sviluppo locale nei command.

    Marcatori stretti (home dir / drive Windows), non "qualsiasi slash":
    evita falsi positivi su URL, `/dev/null`, redirect e path di sistema.
    """
    host_markers = ("/home/", "/Users/", "~/")
    for cfg in dataset_configs:
        dataset = yaml.safe_load(cfg.read_text(encoding="utf-8"))
        rel = str(cfg.relative_to(REPO_ROOT))
        for source in dataset["raw"]["sources"]:
            args = source.get("args") or {}
            command = args.get("command")
            if not command:
                continue
            for marker in host_markers:
                assert marker not in command, (
                    f"{rel}: command con path host '{marker}': {command}"
                )
            assert not re.search(r"[A-Za-z]:[\\/]", command), (
                f"{rel}: command con path Windows: {command}"
            )


@pytest.mark.contract
def test_declared_sql_files_exist(dataset_configs: list[Path]) -> None:
    for cfg in dataset_configs:
        dataset = yaml.safe_load(cfg.read_text(encoding="utf-8"))
        cfg_dir = cfg.parent
        rel = str(cfg.relative_to(REPO_ROOT))

        clean_sql = (cfg_dir / dataset["clean"]["sql"]).resolve()
        assert clean_sql.is_file(), f"{rel}: manca clean SQL dichiarato: {dataset['clean']['sql']}"

        for table in dataset["mart"]["tables"]:
            assert table.get("name"), f"{rel}: ogni mart table deve dichiarare un name"
            assert table.get("sql"), f"{rel}: mart '{table['name']}' deve dichiarare un path SQL"
            sql_path = (cfg_dir / table["sql"]).resolve()
            assert sql_path.is_file(), f"{rel}: manca SQL mart dichiarato: {table['sql']}"


@pytest.mark.contract
def test_mart_table_names_are_unique(dataset_configs: list[Path]) -> None:
    for cfg in dataset_configs:
        dataset = yaml.safe_load(cfg.read_text(encoding="utf-8"))
        names = [t["name"] for t in dataset["mart"]["tables"]]
        rel = str(cfg.relative_to(REPO_ROOT))
        assert len(names) == len(set(names)), f"{rel}: nomi mart duplicati: {names}"


@pytest.mark.contract
def test_required_tables_and_rules_match_declared_marts(dataset_configs: list[Path]) -> None:
    for cfg in dataset_configs:
        dataset = yaml.safe_load(cfg.read_text(encoding="utf-8"))
        rel = str(cfg.relative_to(REPO_ROOT))
        names = {t["name"] for t in dataset["mart"]["tables"]}
        required = set(dataset["mart"]["required_tables"])
        rules = set(dataset["mart"]["validate"]["table_rules"].keys())
        assert required <= names, f"{rel}: mart.required_tables non riferisce tabelle dichiarate"
        assert rules <= names, f"{rel}: mart.validate.table_rules non riferisce tabelle dichiarate"


@pytest.mark.contract
def test_no_run_outputs_committed() -> None:
    """Verifica che i file generati dalla pipeline non siano committati in out/.

    In CI out/ non esiste e il test passa. Localmente, se out/ esiste,
    controlla che i file non siano tracked da git.
    """
    if not OUT_DIR.exists():
        return
    import subprocess

    result = subprocess.run(
        ["git", "ls-files", "out/"],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=False,
    )
    tracked = [line for line in result.stdout.strip().split("\n") if line]
    assert not tracked, f"File generati tracked da git in out/: {tracked}"
