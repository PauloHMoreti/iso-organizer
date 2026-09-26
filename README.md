# ISO Organizer

Ferramenta de linha de comando, feita apenas com a biblioteca padrão do Python, para organizar imagens `.iso` em Linux Mint, Windows e macOS. Ela pesquisa subpastas, preserva o nome dos arquivos, evita sobrescritas e gera relatórios CSV e JSON.

## Instalação

Requer Python 3.9 ou mais recente. No diretório do projeto:

```bash
python -m venv .venv
# Linux/macOS:
source .venv/bin/activate
# Windows PowerShell:
.venv\Scripts\Activate.ps1
python -m pip install -e .
```

Não há dependências de produção. Para executar os testes, instale `pytest` no ambiente de desenvolvimento (`python -m pip install pytest`).

## Uso

```bash
iso-organizer "/dados/isos" "/dados/organizadas"
iso-organizer "/dados/isos" "/dados/organizadas" --dry-run
iso-organizer "/dados/isos" --in-place --format csv
iso-organizer "C:\ISOs" "D:\Organizadas" --report-dir "D:\Relatorios" --format json
```

`--dry-run` calcula e imprime o plano sem mover nada, mas ainda grava o relatório. Os formatos aceitos são `csv`, `json` e `both` (padrão). Para uso sem instalação, também é possível executar `python -m iso_organizer.cli ...` após definir `PYTHONPATH=src`.

Os relatórios são **inventários cumulativos por padrão**: ao executar novamente, os registros anteriores cujas ISOs ainda existem são preservados e as novas são adicionadas/atualizadas. Se uma ISO for removida do destino, ela deixa de aparecer no próximo relatório. Use `--fresh-report` somente quando quiser substituir o inventário pelo lote atual.

### Categorias e regras

As regras analisam somente o nome do arquivo, sem montar a ISO. A primeira correspondência vence:

- **Windows**: `windows`, `win7`, `win10`, `win11`, `Windows8.1`, `winPreVista`, `xp`, `vista`, `msdn`, `microsoft`, `server 20xx`. Separadores `_`, `-` e pontos são tratados como espaços, então nomes como `br_windows_vista_x64` funcionam.
- **Linux**: `linux`, `ubuntu`, `debian`, `fedora`, `mint`, `arch` e outras distribuições.
- **macOS**: `macOS`, `OS X`, `Snow Leopard`, `Boot Camp`, `iLife` e software Apple.
- **Utilitários**: `rescue`, `recovery`, `clonezilla`, `gparted`, `winpe`, drivers, instaladores, `Visual Studio`, `.NET`, `VMware Tools` e diagnóstico.
- **Jogos**: `game`, `Steam`, `Xbox`, `PlayStation`, `Nintendo`, `Guitar Hero` e alguns títulos conhecidos.
- **Outros**: fallback.

Para Windows e Linux, nomes com `recovery`, `recuperação`, `restore` ou `factory reset` recebem subcategoria `Recuperação`; nomes com `oem` recebem `OEM`. Se o fabricante conhecido aparecer no nome, ele é acrescentado: `Windows/Recuperação/Dell`. Assim, uma mídia `Dell OEM Windows.iso` fica em `Windows/OEM/Dell`. Em caso de colisão, o destino recebe `Nome (1).iso`, `Nome (2).iso` etc.

As regras ficam em `src/iso_organizer/core.py`, na constante `_RULES`, e podem ser ampliadas sem alterar a CLI.

## Segurança e limitações

- A origem é descoberta antes de qualquer movimento; isso evita que o modo in-place processe novamente as pastas criadas.
- Nenhum arquivo existente é sobrescrito.
- Use `--dry-run` e faça backup antes de uma reorganização grande.
- O modo in-place cria subpastas dentro da origem; ele não apaga diretórios vazios nem arquivos que não sejam ISO.
- Classificação por nome pode errar em nomes ambíguos; não há inspeção do conteúdo, checksum ou validação de boot.
- Links simbólicos não são seguidos como arquivos pelo mecanismo de descoberta padrão.

## Relatórios

Cada linha registra caminho original, caminho novo, nome, categoria, subcategoria, descrição leve e motivo/regra usada. O JSON é uma lista de objetos e o CSV usa UTF-8 com cabeçalho. Isso permite sincronizar os arquivos de relatório como fonte de conhecimento de um agente de IA: execute o organizador após adicionar novas ISOs e publique/substitua os dois reports nas fontes do agente.

## Testes

```bash
python -m pytest
```

Os testes cobrem classificação, descoberta recursiva, colisões, dry-run e os dois relatórios. O projeto não inclui arquivos ISO reais.

## Nota de uso de IA

Este projeto foi implementado com auxílio de uma ferramenta de IA generativa. A arquitetura, as regras e os testes devem ser revisados por uma pessoa antes de uso em dados importantes.

## Licença

Distribuído sob a licença MIT. Consulte `LICENSE`.
