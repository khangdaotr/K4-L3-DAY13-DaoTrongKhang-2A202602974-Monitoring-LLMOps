from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import mean

import yaml


ROOT = Path(__file__).resolve().parents[1]
LOG_PATH = ROOT / "data" / "logs.jsonl"
CONFIG_PATH = ROOT / "config" / "dashboard.yaml"
OUTPUT_PATH = ROOT / "submission" / "evidence" / "11-dashboard-overview.svg"


def percentile(values: list[float], percent: int) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    position = (len(ordered) - 1) * percent / 100
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] * (1 - fraction) + ordered[upper] * fraction


def sparkline(values: list[float], x: int, y: int, width: int, height: int) -> str:
    if not values:
        values = [0.0]
    low, high = min(values), max(values)
    span = high - low or 1.0
    step = width / max(1, len(values) - 1)
    points = " ".join(
        f"{x + index * step:.1f},{y + height - (value - low) / span * height:.1f}"
        for index, value in enumerate(values)
    )
    return f'<polyline points="{points}" fill="none" stroke="#60a5fa" stroke-width="3"/>'


def main() -> None:
    config = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))["dashboard"]
    now = datetime.now(timezone.utc)
    start = now - timedelta(minutes=config["time_range_minutes"])
    records = []
    for line in LOG_PATH.read_text(encoding="utf-8").splitlines():
        record = json.loads(line)
        timestamp = datetime.fromisoformat(record["ts"].replace("Z", "+00:00"))
        if timestamp >= start:
            records.append(record)

    requests = [row for row in records if row.get("event") == "request_received"]
    responses = [row for row in records if row.get("event") == "response_sent"]
    failures = [row for row in records if row.get("event") == "request_failed"]
    latency = [float(row["latency_ms"]) for row in responses]
    ttft = [float(row["ttft_ms"]) for row in responses]
    traffic = Counter(row["ts"][:16] for row in requests)
    cost_by_minute: dict[str, float] = defaultdict(float)
    for row in responses:
        cost_by_minute[row["ts"][:16]] += float(row["cost_usd"])
    tool_rows = [row for row in records if row.get("tool_success") is not None]
    retrieval_success = 100 * sum(bool(row["tool_success"]) for row in tool_rows) / max(1, len(tool_rows))
    error_rate = 100 * len(failures) / max(1, len(requests))
    tokens_in = [float(row["tokens_in"]) for row in responses]
    tokens_out = [float(row["tokens_out"]) for row in responses]
    quality = [float(row["quality_score"]) for row in responses]

    panels = [
        ("Latency", f"P50 {percentile(latency, 50):.0f} ms · P95 {percentile(latency, 95):.0f} ms · P99 {percentile(latency, 99):.0f} ms · TTFT P95 {percentile(ttft, 95):.0f} ms", latency, "threshold: P95 ≤ 3000 ms"),
        ("Traffic", f"{len(requests)} requests · {len(traffic)} active minutes", list(traffic.values()), "threshold: ≥ 1 request/min"),
        ("Errors", f"Error rate {error_rate:.1f}% · Retrieval success {retrieval_success:.1f}%", [error_rate, retrieval_success], "threshold: errors ≤ 2%"),
        ("Cost", f"Total ${sum(float(row['cost_usd']) for row in responses):.4f}", list(cost_by_minute.values()), "threshold: total ≤ $2.50"),
        ("Tokens", f"Input {sum(tokens_in):.0f} · Output {sum(tokens_out):.0f}", tokens_out, "threshold: total ≤ 50,000"),
        ("Quality", f"Average {mean(quality) if quality else 0:.2f}", quality, "threshold: average ≥ 0.75"),
    ]

    svg = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="920" viewBox="0 0 1400 920">',
        '<rect width="1400" height="920" fill="#07111f"/>',
        '<text x="60" y="60" fill="#f8fafc" font-family="Segoe UI" font-size="30" font-weight="700">K4-L3B Monitoring &amp; LLMOps</text>',
        f'<text x="60" y="91" fill="#94a3b8" font-family="Segoe UI" font-size="16">Last 60 minutes · refresh 30s · generated {now.isoformat(timespec="seconds")}</text>',
    ]
    for index, (title, summary, values, threshold) in enumerate(panels):
        column, row = index % 2, index // 2
        x, y = 60 + column * 670, 130 + row * 250
        svg.extend(
            [
                f'<rect x="{x}" y="{y}" width="620" height="210" rx="16" fill="#111c2e" stroke="#26364d"/>',
                f'<text x="{x + 25}" y="{y + 38}" fill="#f8fafc" font-family="Segoe UI" font-size="22" font-weight="600">{title}</text>',
                f'<text x="{x + 25}" y="{y + 70}" fill="#cbd5e1" font-family="Segoe UI" font-size="15">{summary}</text>',
                f'<line x1="{x + 25}" y1="{y + 145}" x2="{x + 595}" y2="{y + 145}" stroke="#f59e0b" stroke-width="2" stroke-dasharray="7 6"/>',
                sparkline(values, x + 25, y + 93, 570, 82),
                f'<text x="{x + 25}" y="{y + 196}" fill="#fbbf24" font-family="Segoe UI" font-size="13">{threshold}</text>',
            ]
        )
    svg.append("</svg>")
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text("\n".join(svg), encoding="utf-8")
    print(f"Dashboard written to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
