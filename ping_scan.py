#!/usr/bin/env python3
"""MOURA-TOOLS Ping Scanner — ICMP ping sweep for local lab networks."""

from __future__ import annotations

import argparse
import ipaddress
import json
import math
import os
import shutil
import subprocess
import sys
import time
from concurrent.futures import Future, ThreadPoolExecutor, as_completed

__version__ = "2.0.0"

_TOOL = "MOURA-TOOLS"
_UTIL = "Ping Scanner"


class Theme:
    """ANSI color theme for CLI output (red-primary)."""

    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    def __init__(self, use_color: bool = True):
        self.use_color = use_color
        self.colors = {
            "primary": "\033[38;5;196m",  # red
            "success": "\033[38;5;82m",   # green
            "warning": "\033[38;5;214m",  # orange
            "danger":  "\033[38;5;160m",  # dark red
            "muted":   "\033[38;5;245m",  # gray
            "accent":  "\033[38;5;203m",  # light red/salmon
        }

    def paint(self, text: str, tone: str = "primary", bold: bool = False, dim: bool = False) -> str:
        if not self.use_color:
            return text
        parts: list[str] = []
        if bold:
            parts.append(self.BOLD)
        if dim:
            parts.append(self.DIM)
        parts.append(self.colors.get(tone, ""))
        return "".join(parts) + text + self.RESET


def _icon(emoji: str, enabled: bool) -> str:
    """Return '*emoji* ' when emojis are enabled, otherwise ''."""
    return f"{emoji} " if enabled else ""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ping_scan.py",
        description=f"{_TOOL} {_UTIL} — ICMP ping sweep with stylish terminal output.",
    )
    parser.add_argument(
        "--version", action="version", version=f"{_TOOL} {_UTIL} v{__version__}",
    )
    parser.add_argument(
        "--subnet", required=True,
        help="Target subnet in CIDR notation (e.g. 192.168.1.0/24)",
    )
    parser.add_argument(
        "--timeout", type=float, default=1.0,
        help="Per-host timeout in seconds (default: 1.0). "
             "On Unix, fractional values are rounded up to the nearest integer for ping -W.",
    )
    parser.add_argument(
        "--concurrency", type=int, default=8,
        help="Number of parallel ping workers (default: 8)",
    )
    parser.add_argument(
        "--output", action="store_true",
        help="Save online hosts to a file",
    )
    parser.add_argument(
        "--output-file", default="results.txt",
        help="Output file path (default: results.txt)",
    )
    parser.add_argument(
        "--no-color", action="store_true",
        help="Disable ANSI color output",
    )
    parser.add_argument(
        "--no-emoji", action="store_true",
        help="Disable emoji characters (for terminals with limited Unicode support)",
    )
    parser.add_argument(
        "--quiet", action="store_true",
        help="Print only online IPs, one per line — no banner/progress/styling (good for pipes)",
    )
    parser.add_argument(
        "--json", action="store_true", dest="json_out",
        help="Output results as JSON. Mutually exclusive with --quiet.",
    )
    return parser


def validate_args(args: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    if args.timeout <= 0:
        parser.error("--timeout must be greater than 0")
    if args.concurrency <= 0:
        parser.error("--concurrency must be greater than 0")
    if args.quiet and args.json_out:
        parser.error("--quiet and --json are mutually exclusive; use one or the other.")


def ping_host(ip: str, timeout: float) -> bool:
    """Send one ICMP echo request; return True if the host replies."""
    try:
        if os.name == "nt":
            cmd = ["ping", "-n", "1", "-w", str(int(timeout * 1000)), ip]
        else:
            cmd = ["ping", "-c", "1", "-W", str(max(1, math.ceil(timeout))), ip]
        result = subprocess.run(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=timeout + 2,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, OSError):
        return False


def _host_count(net: ipaddress.IPv4Network | ipaddress.IPv6Network) -> int:
    """Return usable host count without iterating the full address space."""
    if net.prefixlen >= net.max_prefixlen - 1:  # /31-/32 (IPv4) or /127-/128 (IPv6)
        return net.num_addresses
    return max(0, net.num_addresses - 2)


def render_banner(theme: Theme) -> None:
    banner = (
        "\n"
        "╔══════════════════════════════════════════════╗\n"
        "║          MOURA-TOOLS · Ping Scanner          ║\n"
        "║       ICMP Sweep · Concurrent · Stylish      ║\n"
        "╚══════════════════════════════════════════════╝"
    )
    print(theme.paint(banner, tone="primary", bold=True))


def format_duration(seconds: float) -> str:
    if seconds < 1:
        return f"{seconds * 1000:.0f} ms"
    return f"{seconds:.2f} s"


def _render_progress(
    theme: Theme, completed: int, total: int, start_time: float, width: int = 28
) -> None:
    progress = completed / total if total > 0 else 1.0
    done = int(progress * width)
    bar = "█" * done + "░" * (width - done)
    elapsed = time.perf_counter() - start_time
    speed = completed / elapsed if elapsed > 0 else 0.0
    eta = (total - completed) / speed if speed > 0 else 0.0
    status = f"[{bar}] {completed:>4}/{total:<4} ({progress * 100:>5.1f}%)"
    if speed > 0:
        status += f"  {speed:.0f} h/s"
    if eta > 1:
        status += f"  ETA {eta:.0f}s"
    print("\r" + theme.paint(status, "muted"), end="", flush=True)


def scan_hosts(
    net: ipaddress.IPv4Network | ipaddress.IPv6Network,
    timeout: float,
    concurrency: int,
    suppress_progress: bool,
    theme: Theme,
) -> tuple[list[str], int]:
    """Scan all hosts using a bounded streaming futures window.

    Submits at most ``concurrency * 4`` futures at a time, so the full host
    list is never materialised in memory.  Returns ``(reachable, total_hosts)``.
    """
    total = _host_count(net)
    if total == 0:
        return [], 0

    host_iter = (str(ip) for ip in net.hosts())
    reachable: list[str] = []
    completed = 0
    window_size = concurrency * 4
    start_time = time.perf_counter()
    last_render = 0.0
    render_interval = 0.05  # 50 ms throttle

    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        pending: dict[Future[bool], str] = {}

        def _refill() -> None:
            while len(pending) < window_size:
                ip = next(host_iter, None)
                if ip is None:
                    break
                fut = executor.submit(ping_host, ip, timeout)
                pending[fut] = ip

        _refill()

        while pending:
            for fut in as_completed(list(pending)):
                ip = pending.pop(fut)
                if fut.result():
                    reachable.append(ip)
                completed += 1
                _refill()

                if not suppress_progress:
                    now = time.perf_counter()
                    if now - last_render >= render_interval or completed == total:
                        _render_progress(theme, completed, total, start_time)
                        last_render = now
                break  # take a fresh snapshot of pending so newly submitted futures are included

    return reachable, total


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    validate_args(args, parser)

    if shutil.which("ping") is None:
        print(
            "Error: 'ping' command not found. Please install it and try again.",
            file=sys.stderr,
        )
        return 1

    use_color = not args.no_color and sys.stdout.isatty()
    use_emoji = not args.no_emoji and sys.stdout.isatty()
    theme = Theme(use_color=use_color)
    silent = args.quiet or args.json_out

    try:
        net = ipaddress.ip_network(args.subnet, strict=False)
    except ValueError as exc:
        print(theme.paint(f"Invalid subnet: {exc}", "danger", bold=True), file=sys.stderr)
        return 2

    total_hosts = _host_count(net)

    if not silent:
        render_banner(theme)
        print(theme.paint(f"{_icon('⚙️', use_emoji)}Scan configuration", "primary", bold=True))
        print(f"  • Subnet:      {theme.paint(str(net), 'accent')}")
        print(f"  • Hosts:       {theme.paint(str(total_hosts), 'accent')}")
        print(f"  • Timeout:     {theme.paint(f'{args.timeout:.2f}s', 'accent')}")
        print(f"  • Concurrency: {theme.paint(str(args.concurrency), 'accent')}")

    if total_hosts == 0:
        if not silent:
            print(theme.paint("No hosts available in this subnet.", "warning", bold=True))
        return 0

    if not silent:
        print(theme.paint(f"\n{_icon('🚀', use_emoji)}Starting scan...", "primary", bold=True))

    start_time = time.perf_counter()
    reachable, _ = scan_hosts(net, args.timeout, args.concurrency, silent, theme)
    elapsed = time.perf_counter() - start_time

    sorted_reachable = sorted(reachable, key=ipaddress.ip_address)

    # --- JSON output ---
    if args.json_out:
        print(json.dumps({
            "subnet": str(net),
            "total_hosts": total_hosts,
            "online": len(sorted_reachable),
            "offline": total_hosts - len(sorted_reachable),
            "duration_seconds": round(elapsed, 3),
            "hosts": sorted_reachable,
        }, indent=2))
        return 0

    # --- Quiet output ---
    if args.quiet:
        for ip in sorted_reachable:
            print(ip)
        return 0

    # --- Interactive output ---
    print()  # newline after progress bar
    print(theme.paint(f"\n{_icon('📡', use_emoji)}Results", "primary", bold=True))
    if sorted_reachable:
        print(theme.paint(f"{len(sorted_reachable)} host(s) online:", "success", bold=True))
        for ip in sorted_reachable:
            print(theme.paint(f"  {_icon('✅', use_emoji)}{ip}", "success"))
    else:
        print(theme.paint("No hosts responded to ping.", "warning", bold=True))

    offline = total_hosts - len(sorted_reachable)
    print(theme.paint(f"\n{_icon('📊', use_emoji)}Summary", "primary", bold=True))
    print(f"  • Online:   {theme.paint(str(len(sorted_reachable)), 'success', bold=True)}")
    print(f"  • Offline:  {theme.paint(str(offline), 'danger', bold=True)}")
    print(f"  • Duration: {theme.paint(format_duration(elapsed), 'accent', bold=True)}")

    if args.output:
        try:
            with open(args.output_file, "w", encoding="utf-8") as fh:
                for ip in sorted_reachable:
                    fh.write(ip + "\n")
            print(theme.paint(
                f"\n{_icon('📝', use_emoji)}Saved to: {args.output_file}",
                "primary", bold=True,
            ))
        except OSError as exc:
            print(theme.paint(f"Error saving file: {exc}", "danger", bold=True), file=sys.stderr)
            return 1

    print(theme.paint(f"\n{_icon('✨', use_emoji)}Scan complete.", "accent", bold=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
