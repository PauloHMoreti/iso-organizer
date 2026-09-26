from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .core import organize, write_reports


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="iso-organizer",
        description="Organiza imagens ISO recursivamente por categoria.",
    )
    parser.add_argument("origem", type=Path, help="pasta onde as ISOs serão procuradas")
    parser.add_argument("destino", type=Path, nargs="?", help="pasta de destino")
    parser.add_argument("--in-place", action="store_true", help="organiza dentro da própria origem")
    parser.add_argument("--dry-run", action="store_true", help="apenas mostra o plano, sem mover arquivos")
    parser.add_argument("--report-dir", type=Path, help="pasta dos relatórios (padrão: destino ou origem)")
    parser.add_argument("--fresh-report", action="store_true",
                        help="substitui o inventário anterior em vez de acumulá-lo")
    parser.add_argument("--format", choices=("csv", "json", "both"), default="both",
                        help="formatos de relatório (padrão: both)")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.in_place and args.destino:
        print("erro: --in-place não pode ser combinado com destino posicional", file=sys.stderr)
        return 2
    if not args.in_place and not args.destino:
        print("erro: informe destino ou use --in-place", file=sys.stderr)
        return 2
    try:
        entries = organize(args.origem, args.destino, in_place=args.in_place, dry_run=args.dry_run)
        report_dir = args.report_dir or (args.origem if args.in_place else args.destino)
        formats = ("csv", "json") if args.format == "both" else (args.format,)
        reports = write_reports(entries, report_dir, formats, cumulative=not args.fresh_report)
    except (OSError, ValueError) as error:
        print(f"erro: {error}", file=sys.stderr)
        return 1
    for entry in entries:
        print(f"{entry.caminho_original} -> {entry.caminho_novo}")
    suffix = " (dry-run; nenhum arquivo foi movido)" if args.dry_run else ""
    inventory_note = " inventariada(s)" if not args.fresh_report else " processada(s)"
    print(f"{len(entries)} ISO(s){inventory_note}{suffix}. Relatórios: {', '.join(map(str, reports))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
