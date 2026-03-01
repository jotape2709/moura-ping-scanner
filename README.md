<!--
MOURA-TOOLS Ping Scanner - README (PT/EN)
Repo: jotape2709/lab-test
Main script: ping_scan.py
-->

<div align="center">

# 🔴 MOURA-TOOLS Ping Scanner

**ICMP Ping Sweep** em Python para descoberta de hosts em redes locais — rápido, concorrente e com saída estilizada no terminal.  
**Python ICMP Ping Sweep** for local-network host discovery — fast, concurrent, and with a stylish terminal output.

<br/>

<!-- Badges -->
![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-555555)
![CLI](https://img.shields.io/badge/Type-CLI-4c1)
![Threads](https://img.shields.io/badge/Concurrency-ThreadPoolExecutor-blue)
![ICMP](https://img.shields.io/badge/Network-ICMP%20Ping-orange)
![Zero deps](https://img.shields.io/badge/Dependencies-Zero%20external-red)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

</div>

---

## Português

### Visão geral

O **MOURA-TOOLS Ping Scanner** é um utilitário em Python que realiza **varredura ICMP (ping sweep)** em uma subnet (CIDR) para identificar **hosts online**.  
Ele usa **execução concorrente** (`ThreadPoolExecutor`), varredura em **streaming** (sem materializar todos os hosts em memória), exibe uma **barra de progresso aprimorada** e pode exportar resultados em arquivo ou JSON.

> Ferramenta pensada para **laboratórios** e **inventário/reconhecimento autorizado** de rede.

### Recursos

- Branding **MOURA-TOOLS** com tema de cores vermelho
- Suporte a **CIDR** (ex.: `192.168.1.0/24`)
- **Multi-thread** com `concurrent.futures.ThreadPoolExecutor`
- Varredura em **streaming** — janela de futures limitada, sem alocar toda a lista de hosts
- **Timeout** por host configurável (arredondamento correto no Unix via `math.ceil`)
- **Concorrência** configurável
- **Compatibilidade** Windows / Linux / macOS
- **Saída com cores ANSI** (opção para desativar via `--no-color`)
- **Emojis opcionais** via `--no-emoji` (para terminais com suporte Unicode limitado)
- **Barra de progresso** com percentual, velocidade (hosts/s) e ETA estimado
- Atualização de progresso limitada a **50 ms** para evitar flickering
- Modo `--quiet`: imprime somente IPs online, ideal para pipes/scripts
- Modo `--json`: saída estruturada em JSON para automação
- `--version`: exibe versão da ferramenta
- **Exportação** de hosts online para arquivo (`--output`)

### Estrutura do repositório

- `ping_scan.py` — script principal (CLI)
- `README.md` — documentação

### Requisitos

- **Python 3.8+**
- Comando **`ping`** disponível no sistema (verificado automaticamente)

### Instalação

Este projeto **não possui dependências externas** (somente biblioteca padrão do Python).

#### Windows (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python ping_scan.py -h
```

#### Linux/macOS (bash/zsh)

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 ping_scan.py -h
```

### Uso

#### Ajuda

```bash
python ping_scan.py -h
```

#### Versão

```bash
python ping_scan.py --version
```

#### Scan básico

```bash
python ping_scan.py --subnet 192.168.1.0/24
```

#### Ajustando timeout e concorrência

```bash
python ping_scan.py --subnet 10.0.0.0/24 --timeout 0.5 --concurrency 20
```

#### Modo silencioso (somente IPs online — ideal para pipes)

```bash
python ping_scan.py --subnet 10.0.0.0/24 --quiet
# ou redirecionar:
python ping_scan.py --subnet 10.0.0.0/24 --quiet > hosts_online.txt
```

#### Saída em JSON

```bash
python ping_scan.py --subnet 10.0.0.0/24 --json
```

Exemplo de saída:

```json
{
  "subnet": "10.0.0.0/24",
  "total_hosts": 254,
  "online": 3,
  "offline": 251,
  "duration_seconds": 2.541,
  "hosts": [
    "10.0.0.1",
    "10.0.0.5",
    "10.0.0.10"
  ]
}
```

#### Salvando resultado em arquivo

```bash
python ping_scan.py --subnet 10.0.0.0/24 --output
python ping_scan.py --subnet 10.0.0.0/24 --output --output-file found_hosts.txt
```

#### Desativando cores e/ou emojis

```bash
python ping_scan.py --subnet 192.168.1.0/24 --no-color
python ping_scan.py --subnet 192.168.1.0/24 --no-emoji
python ping_scan.py --subnet 192.168.1.0/24 --no-color --no-emoji
```

### Argumentos (CLI)

| Flag | Padrão | Descrição |
|------|--------|-----------|
| `--subnet` | *(obrigatório)* | Subnet em CIDR (ex.: `192.168.1.0/24`) |
| `--timeout` | `1.0` | Timeout por host em segundos. No Unix, arredondado para cima. |
| `--concurrency` | `8` | Número de pings em paralelo |
| `--output` | desativado | Salva IPs online em arquivo |
| `--output-file` | `results.txt` | Caminho do arquivo de saída |
| `--no-color` | desativado | Desativa cores ANSI |
| `--no-emoji` | desativado | Desativa emojis (para terminais com suporte limitado) |
| `--quiet` | desativado | Imprime somente IPs online, sem decoração (bom para pipes) |
| `--json` | desativado | Saída em JSON. Mutuamente exclusivo com `--quiet`. |
| `--version` | — | Exibe versão e sai |

### Observações e limitações

- O script envia **1 ping por host**.
- Em Unix-like, o parâmetro `-W` do `ping` trabalha com **segundos inteiros**; valores fracionários são arredondados para cima (`math.ceil`). O `subprocess.run` também possui um timeout próprio (`timeout + 2s`).
- Em Windows, o parâmetro `-w` do `ping` recebe **milissegundos**.
- Firewalls e políticas de rede podem **bloquear ICMP**, fazendo hosts parecerem offline.
- `--quiet` e `--json` são **mutuamente exclusivos** (uso simultâneo retorna erro amigável).

### Aviso legal (Disclaimer)

Esta ferramenta é destinada a uso educacional e **reconhecimento autorizado**. Varredura não autorizada de redes/sistemas pode ser ilegal e antiética. Use apenas onde você tenha permissão explícita.

---

## English

### Overview

**MOURA-TOOLS Ping Scanner** is a Python utility that performs an **ICMP ping sweep** over a CIDR subnet to identify **reachable (online) hosts**.  
It uses **concurrency** (`ThreadPoolExecutor`), **streaming** host scanning (bounded futures window — no full host list in memory), an **enhanced progress bar**, and can output results as JSON or write them to a file.

> Designed for **lab environments** and **authorized** network inventory/reconnaissance.

### Features

- **MOURA-TOOLS** branding with red color theme
- **CIDR** support (e.g. `192.168.1.0/24`)
- **Multi-threaded** scanning via `concurrent.futures.ThreadPoolExecutor`
- **Streaming scan** — bounded futures window, no full host-list allocation
- Configurable per-host **timeout** (correctly rounded up on Unix via `math.ceil`)
- Configurable **concurrency**
- **Windows / Linux / macOS** support
- **ANSI colored output** (disable with `--no-color`)
- Optional **emoji** support (disable with `--no-emoji` for limited terminals)
- Enhanced **progress bar** with percentage, speed (hosts/s), and estimated ETA
- Progress updates **throttled to 50 ms** to prevent flickering
- `--quiet` mode: prints only online IPs — perfect for pipes/scripts
- `--json` mode: structured JSON output for automation
- `--version`: prints tool version
- Optional **file export** of online hosts (`--output`)

### Repository layout

- `ping_scan.py` — main CLI script
- `README.md` — documentation

### Requirements

- **Python 3.8+**
- System **`ping`** command available (automatically checked at startup)

### Installation

No external dependencies (standard library only).

#### Windows (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python ping_scan.py -h
```

#### Linux/macOS (bash/zsh)

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 ping_scan.py -h
```

### Usage

#### Help

```bash
python ping_scan.py -h
```

#### Version

```bash
python ping_scan.py --version
```

#### Basic scan

```bash
python ping_scan.py --subnet 192.168.1.0/24
```

#### Custom timeout and concurrency

```bash
python ping_scan.py --subnet 10.0.0.0/24 --timeout 0.5 --concurrency 20
```

#### Quiet mode (online IPs only — good for pipes)

```bash
python ping_scan.py --subnet 10.0.0.0/24 --quiet
# redirect to file:
python ping_scan.py --subnet 10.0.0.0/24 --quiet > online_hosts.txt
```

#### JSON output

```bash
python ping_scan.py --subnet 10.0.0.0/24 --json
```

Example output:

```json
{
  "subnet": "10.0.0.0/24",
  "total_hosts": 254,
  "online": 3,
  "offline": 251,
  "duration_seconds": 2.541,
  "hosts": [
    "10.0.0.1",
    "10.0.0.5",
    "10.0.0.10"
  ]
}
```

#### Save results to a file

```bash
python ping_scan.py --subnet 10.0.0.0/24 --output
python ping_scan.py --subnet 10.0.0.0/24 --output --output-file found_hosts.txt
```

#### Disable colors and/or emojis

```bash
python ping_scan.py --subnet 192.168.1.0/24 --no-color
python ping_scan.py --subnet 192.168.1.0/24 --no-emoji
python ping_scan.py --subnet 192.168.1.0/24 --no-color --no-emoji
```

### CLI arguments

| Flag | Default | Description |
|------|---------|-------------|
| `--subnet` | *(required)* | Target subnet in CIDR (e.g. `192.168.1.0/24`) |
| `--timeout` | `1.0` | Per-host timeout in seconds. Rounded up on Unix. |
| `--concurrency` | `8` | Number of parallel ping workers |
| `--output` | disabled | Save online hosts to a file |
| `--output-file` | `results.txt` | Output file path |
| `--no-color` | disabled | Disable ANSI colors |
| `--no-emoji` | disabled | Disable emojis (for terminals with limited Unicode support) |
| `--quiet` | disabled | Print only online IPs, no decoration (good for pipes) |
| `--json` | disabled | JSON output. Mutually exclusive with `--quiet`. |
| `--version` | — | Print version and exit |

### Notes & limitations

- Sends **1 ping per host**.
- On Unix-like systems, `ping -W` takes **integer seconds**; fractional timeout values are rounded up with `math.ceil`. `subprocess.run` also has its own safety timeout (`timeout + 2s`).
- On Windows, `ping -w` takes **milliseconds**.
- Firewalls may **block ICMP**, causing hosts to appear offline.
- `--quiet` and `--json` are **mutually exclusive** (using both prints a friendly error).

### Disclaimer

This tool is for educational and **authorized** network reconnaissance only. Unauthorized scanning may be illegal and unethical. Use only on networks you have explicit permission to test.

---

## License

The MIT License (MIT)

Copyright (c) 2011-2025 The Bootstrap Authors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
