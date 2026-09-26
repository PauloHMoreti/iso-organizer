import csv
import json
from pathlib import Path

from iso_organizer.core import classify_iso, discover_isos, organize, write_reports


def test_classification_system_recovery_vendor():
    result = classify_iso("Windows 11 Recovery Dell.iso")
    assert result.category == "Windows"
    assert result.subcategory == "Recuperação/Dell"


def test_classification_fallback_and_linux():
    assert classify_iso("Ubuntu 24.04.iso").category == "Linux"
    assert classify_iso("foto.iso").category == "Outros"


def test_recursive_discovery_is_case_insensitive(tmp_path: Path):
    (tmp_path / "nested").mkdir()
    (tmp_path / "a.ISO").touch()
    (tmp_path / "nested" / "b.iso").touch()
    (tmp_path / "nested" / "ignore.txt").touch()
    assert [item.name for item in discover_isos(tmp_path)] == ["a.ISO", "b.iso"]


def test_dry_run_does_not_move_and_collision_gets_suffix(tmp_path: Path):
    source = tmp_path / "source"
    destination = tmp_path / "destination"
    (source / "one").mkdir(parents=True)
    (source / "two").mkdir()
    (source / "one" / "Ubuntu.iso").touch()
    (source / "two" / "Ubuntu.iso").touch()
    entries = organize(source, destination, dry_run=True)
    assert len(entries) == 2
    assert not (destination / "Linux").exists()
    assert entries[1].caminho_novo.endswith("Ubuntu (1).iso")

    organize(source, destination)
    assert len(list((destination / "Linux").glob("*.iso"))) == 2
    assert not (source / "one" / "Ubuntu.iso").exists()


def test_reports_csv_and_json(tmp_path: Path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "Windows 10.iso").touch()
    entries = organize(source, tmp_path / "dest")
    report_paths = write_reports(entries, tmp_path / "reports")
    assert {path.suffix for path in report_paths} == {".csv", ".json"}
    with (tmp_path / "reports" / "iso-organizer-report.csv").open(encoding="utf-8", newline="") as handle:
        assert list(csv.DictReader(handle))[0]["categoria"] == "Windows"
    data = json.loads((tmp_path / "reports" / "iso-organizer-report.json").read_text(encoding="utf-8"))
    assert data[0]["nome"] == "Windows 10.iso"
