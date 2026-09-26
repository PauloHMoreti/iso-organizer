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


def test_classification_handles_real_report_name_patterns():
    assert classify_iso("br_windows_vista_x64_dvd.iso").category == "Windows"
    assert classify_iso("WIN_7_HOMEPREMIUM.iso").category == "Windows"
    assert classify_iso("Dell Inspiron Reinstall DVD.iso").subcategory == "Recuperação/Dell"
    assert classify_iso("DRIVER_CD_DELL_INSPIRON_1545.ISO").category == "Utilitários"
    assert classify_iso("linuxmint-22.2-cinnamon-64bit.iso").category == "Linux"
    assert classify_iso("Windows8.1_EnglishInternational.iso").category == "Windows"
    assert classify_iso("winPreVista.iso").category == "Windows"
    assert classify_iso("HBCD_PE_x64.iso").category == "Utilitários"
    assert classify_iso("PDVD81_DX_DELL_INSPIRON_1545.ISO").category == "Utilitários"


def test_classification_detects_macos_and_games():
    assert classify_iso("Mac OS X Snow Leopard 10.6.iso").category == "macOS"
    assert classify_iso("iLife_11_Retail.iso").category == "macOS"
    assert classify_iso("Guitar.Hero.3.PC.iso").category == "Jogos"


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
