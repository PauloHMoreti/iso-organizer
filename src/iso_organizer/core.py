from __future__ import annotations

import csv
import json
import re
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Sequence, Union


DEFAULT_CATEGORIES = ("Windows", "Linux", "macOS", "Utilitários", "Jogos", "Outros")
REPORT_FIELDS = (
    "caminho_original",
    "caminho_novo",
    "nome",
    "categoria",
    "subcategoria",
    "descricao",
    "motivo",
)

_RULES = (
    ("macOS", re.compile(
        r"\b(?:mac\s*os(?:\s*x)?|os\s*x|snow\s*leopard|boot\s*camp|ilife\d*|iboot|"
        r"office\s*mac|officemac|apple)\b",
        re.I,
    ), "nome contém marcador de macOS ou software Apple"),
    ("Windows", re.compile(
        r"\b(?:windows?(?:\s*\d(?:\.\d)?)?|win(?:dows)?|win\s*(?:xp|[23456789](?:\.\d)?|10|11)|"
        r"winpre(?:2k|vista)?|xp|vista|server\s*20\d\d|msdn|microsoft|reinstall|"
        r"client\s+enterprise|lrmc\w*)\b",
        re.I,
    ), "nome contém marcador de Windows, versão ou produto Microsoft"),
    ("Linux", re.compile(
        r"\b(?:linux|linuxmint|ubuntu|debian|fedora|mint|arch|manjaro|kali|centos|"
        r"red\s*hat|opensuse)\b",
        re.I,
    ), "nome contém distribuição ou marcador de Linux"),
    ("Utilitários", re.compile(
        r"\b(?:rescue|recovery|hiren|clonezilla|gparted|utility|utilities|toolkit|"
        r"diagnostic|antivirus|winpe|medicat|driver|drivers|resource\s*cd|applications?\s+disc|"
        r"service\s*pack|servicepack\w*|installer|setup|visual\s*studio|visualstudio|"
        r"visual\s*foxpro|dot\s*net|ndp\d+|hbcd|vmware\s*tools|pdvd\d*|"
        r"pdvd[a-z0-9]*|powerdvd|zune|office)\b",
        re.I,
    ), "nome contém marcador de ferramenta, driver ou software"),
    ("Jogos", re.compile(
        r"\b(?:game|games|jogo|jogos|steam|xbox|playstation|ps[2345]|nintendo|"
        r"guitar\s*hero|miku|pica\s*pau)\b",
        re.I,
    ), "nome contém marcador de jogo ou console"),
)
_RECOVERY = re.compile(
    r"\b(?:recovery|recupera(?:c|ç)[aã]o|restore|factory\s*reset|rescue|"
    r"reinstall|reinstall\s*dvd)\b",
    re.I,
)
_OEM = re.compile(r"\b(?:oem|recovery|restore|factory|reinstall)\b", re.I)
_VENDORS = (
    "Dell", "HP", "Lenovo", "Acer", "ASUS", "Samsung", "Toshiba", "Microsoft",
    "Apple", "Fujitsu", "Positivo", "Multilaser",
)


@dataclass(frozen=True)
class Classification:
    category: str
    subcategory: str = ""
    description: str = ""
    reason: str = ""


@dataclass
class ReportEntry:
    caminho_original: str
    caminho_novo: str
    nome: str
    categoria: str
    subcategoria: str
    descricao: str
    motivo: str


def classify_iso(path: Union[Path, str]) -> Classification:
    """Classifica somente pelo nome do arquivo, de forma previsível e extensível."""
    # ISO names commonly use "_" and "-" as word separators (for example
    # br_windows_vista_x64), but regex word boundaries treat "_" as a letter.
    name = Path(path).stem
    normalized_name = re.sub(r"[\W_]+", " ", name, flags=re.UNICODE)
    category = "Outros"
    reason = "nenhuma regra específica correspondeu ao nome"
    for candidate, pattern, rule_reason in _RULES:
        if pattern.search(normalized_name):
            category, reason = candidate, rule_reason
            break

    subcategory = ""
    if category in {"Windows", "Linux"} and _RECOVERY.search(normalized_name):
        subcategory = "Recuperação"
    elif category in {"Windows", "Linux"} and _OEM.search(normalized_name):
        subcategory = "OEM"

    vendor = next(
        (vendor for vendor in _VENDORS if re.search(rf"\b{re.escape(vendor)}\b", normalized_name, re.I)),
        "",
    )
    if subcategory and vendor:
        subcategory = f"{subcategory}/{vendor}"

    description = f"Imagem ISO classificada como {category}"
    if subcategory:
        description += f" ({subcategory.replace('/', ' / ')})"
    return Classification(category, subcategory, description, reason)


def discover_isos(source: Union[Path, str]) -> list[Path]:
    root = Path(source).expanduser().resolve()
    if not root.is_dir():
        raise NotADirectoryError(f"Pasta de origem inexistente: {source}")
    return sorted(
        (path for path in root.rglob("*") if path.is_file() and path.suffix.lower() == ".iso"),
        key=lambda path: str(path).casefold(),
    )


def _unique_path(path: Path, reserved: set[Path]) -> Path:
    candidate = path
    index = 1
    while candidate.exists() or candidate in reserved:
        candidate = path.with_name(f"{path.stem} ({index}){path.suffix}")
        index += 1
    reserved.add(candidate)
    return candidate


def organize(
    source: Union[Path, str],
    destination: Union[Path, str, None] = None,
    *,
    in_place: bool = False,
    dry_run: bool = False,
) -> list[ReportEntry]:
    """Planeja e, salvo em dry-run, move ISOs sem sobrescrever arquivos."""
    source_path = Path(source).expanduser().resolve()
    if in_place:
        destination_path = source_path
    elif destination is not None:
        destination_path = Path(destination).expanduser().resolve()
    else:
        raise ValueError("Informe destino ou use --in-place")
    if not source_path.is_dir():
        raise NotADirectoryError(f"Pasta de origem inexistente: {source}")
    if not in_place and destination_path == source_path:
        raise ValueError("Destino igual à origem exige --in-place")

    files = discover_isos(source_path)
    reserved: set[Path] = set()
    entries: list[ReportEntry] = []
    for original in files:
        classification = classify_iso(original)
        target_dir = destination_path / classification.category
        if classification.subcategory:
            target_dir /= Path(classification.subcategory)
        target = _unique_path(target_dir / original.name, reserved)
        entries.append(ReportEntry(
            caminho_original=str(original),
            caminho_novo=str(target),
            nome=original.name,
            categoria=classification.category,
            subcategoria=classification.subcategory,
            descricao=classification.description,
            motivo=classification.reason,
        ))

    if not dry_run:
        for entry in entries:
            target = Path(entry.caminho_novo)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(entry.caminho_original, target)
    return entries


def write_reports(
    entries: Sequence[ReportEntry],
    report_dir: Union[Path, str],
    formats: Iterable[str] = ("csv", "json"),
) -> list[Path]:
    target_dir = Path(report_dir).expanduser()
    target_dir.mkdir(parents=True, exist_ok=True)
    data = [asdict(entry) for entry in entries]
    written: list[Path] = []
    selected = {item.lower() for item in formats}
    if "csv" in selected:
        csv_path = target_dir / "iso-organizer-report.csv"
        with csv_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=REPORT_FIELDS)
            writer.writeheader()
            writer.writerows(data)
        written.append(csv_path)
    if "json" in selected:
        json_path = target_dir / "iso-organizer-report.json"
        with json_path.open("w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        written.append(json_path)
    invalid = selected - {"csv", "json"}
    if invalid:
        raise ValueError(f"Formato(s) inválido(s): {', '.join(sorted(invalid))}")
    return written
