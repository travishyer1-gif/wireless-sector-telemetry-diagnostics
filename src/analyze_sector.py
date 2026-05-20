from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path
from statistics import mean, median
from typing import Iterable


AP_RX_GAP_WARN_DB = 10.0
AP_RX_GAP_CRITICAL_DB = 14.0
LOW_AP_CCQ_PCT = 70.0
HIGH_RETRY_PCT = 15.0
HIGH_LATENCY_P95_MS = 60.0


@dataclass(frozen=True)
class LinkSample:
    snapshot_id: str
    sector_id: str
    site_id: str
    cpe_id: str
    radio_class: str
    firmware_bucket: str
    frequency_bucket: str
    channel_width_mhz: int
    link_uptime_bucket: str
    ap_rx_signal_dbm: float
    cpe_rx_signal_dbm: float
    ap_tx_ccq_pct: float
    cpe_tx_ccq_pct: float
    noise_floor_bucket_dbm: str
    retry_rate_pct: float
    latency_p95_ms: float
    throughput_down_mbps: float
    throughput_up_mbps: float
    notes: str

    @property
    def ap_rx_gap_db(self) -> float:
        """Positive values mean the customer radio hears the AP better than the AP hears the customer."""
        return self.cpe_rx_signal_dbm - self.ap_rx_signal_dbm

    @property
    def has_ap_rx_asymmetry(self) -> bool:
        return self.ap_rx_gap_db >= AP_RX_GAP_WARN_DB

    @property
    def health_flags(self) -> list[str]:
        flags: list[str] = []
        if self.ap_rx_gap_db >= AP_RX_GAP_CRITICAL_DB:
            flags.append("critical_ap_rx_asymmetry")
        elif self.has_ap_rx_asymmetry:
            flags.append("ap_rx_asymmetry")
        if self.ap_tx_ccq_pct < LOW_AP_CCQ_PCT:
            flags.append("low_ap_tx_ccq")
        if self.retry_rate_pct >= HIGH_RETRY_PCT:
            flags.append("high_retry_rate")
        if self.latency_p95_ms >= HIGH_LATENCY_P95_MS:
            flags.append("high_latency_p95")
        return flags


def _float(row: dict[str, str], field: str) -> float:
    try:
        return float(row[field])
    except KeyError as exc:
        raise ValueError(f"missing required field: {field}") from exc
    except ValueError as exc:
        raise ValueError(f"invalid numeric value for {field}: {row.get(field)!r}") from exc


def _int(row: dict[str, str], field: str) -> int:
    return int(_float(row, field))


def load_samples(path: Path) -> list[LinkSample]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)

    samples: list[LinkSample] = []
    for row in rows:
        samples.append(
            LinkSample(
                snapshot_id=row["snapshot_id"],
                sector_id=row["sector_id"],
                site_id=row["site_id"],
                cpe_id=row["cpe_id"],
                radio_class=row["radio_class"],
                firmware_bucket=row["firmware_bucket"],
                frequency_bucket=row["frequency_bucket"],
                channel_width_mhz=_int(row, "channel_width_mhz"),
                link_uptime_bucket=row["link_uptime_bucket"],
                ap_rx_signal_dbm=_float(row, "ap_rx_signal_dbm"),
                cpe_rx_signal_dbm=_float(row, "cpe_rx_signal_dbm"),
                ap_tx_ccq_pct=_float(row, "ap_tx_ccq_pct"),
                cpe_tx_ccq_pct=_float(row, "cpe_tx_ccq_pct"),
                noise_floor_bucket_dbm=row["noise_floor_bucket_dbm"],
                retry_rate_pct=_float(row, "retry_rate_pct"),
                latency_p95_ms=_float(row, "latency_p95_ms"),
                throughput_down_mbps=_float(row, "throughput_down_mbps"),
                throughput_up_mbps=_float(row, "throughput_up_mbps"),
                notes=row.get("notes", ""),
            )
        )
    return samples


def summarize_snapshot(samples: Iterable[LinkSample]) -> dict[str, object]:
    sample_list = list(samples)
    if not sample_list:
        raise ValueError("cannot summarize an empty snapshot")

    asymmetry_samples = [sample for sample in sample_list if sample.has_ap_rx_asymmetry]
    flagged_samples = [sample for sample in sample_list if sample.health_flags]
    ap_rx_gaps = [sample.ap_rx_gap_db for sample in sample_list]
    retries = [sample.retry_rate_pct for sample in sample_list]
    latencies = [sample.latency_p95_ms for sample in sample_list]
    down = [sample.throughput_down_mbps for sample in sample_list]
    up = [sample.throughput_up_mbps for sample in sample_list]

    asymmetry_rate = len(asymmetry_samples) / len(sample_list)
    median_ap_gap = median(ap_rx_gaps)
    mean_retry = mean(retries)
    median_latency = median(latencies)

    if asymmetry_rate >= 0.35 and median_ap_gap >= AP_RX_GAP_WARN_DB:
        sector_assessment = "sector_level_ap_receive_asymmetry"
    elif flagged_samples:
        sector_assessment = "mixed_link_degradation"
    else:
        sector_assessment = "healthy_baseline"

    return {
        "snapshot_id": sample_list[0].snapshot_id,
        "sector_id": sample_list[0].sector_id,
        "site_id": sample_list[0].site_id,
        "sample_count": len(sample_list),
        "sector_assessment": sector_assessment,
        "asymmetry_link_count": len(asymmetry_samples),
        "asymmetry_rate_pct": round(asymmetry_rate * 100, 1),
        "median_ap_rx_gap_db": round(median_ap_gap, 1),
        "max_ap_rx_gap_db": round(max(ap_rx_gaps), 1),
        "mean_retry_rate_pct": round(mean_retry, 1),
        "median_latency_p95_ms": round(median_latency, 1),
        "median_down_mbps": round(median(down), 1),
        "median_up_mbps": round(median(up), 1),
        "flagged_links": [
            {
                "cpe_id": sample.cpe_id,
                "ap_rx_gap_db": round(sample.ap_rx_gap_db, 1),
                "ap_tx_ccq_pct": sample.ap_tx_ccq_pct,
                "retry_rate_pct": sample.retry_rate_pct,
                "latency_p95_ms": sample.latency_p95_ms,
                "flags": sample.health_flags,
            }
            for sample in flagged_samples
        ],
    }


def analyze(samples: list[LinkSample]) -> list[dict[str, object]]:
    by_snapshot: dict[str, list[LinkSample]] = {}
    for sample in samples:
        by_snapshot.setdefault(sample.snapshot_id, []).append(sample)
    return [summarize_snapshot(by_snapshot[key]) for key in sorted(by_snapshot)]


def render_markdown(summaries: list[dict[str, object]]) -> str:
    lines = [
        "# Sector Health Report",
        "",
        "This report is generated from sanitized sample telemetry. Identifiers are neutral and values are bucketed or synthetic.",
        "",
        "| Snapshot | Assessment | Links | AP RX asymmetry | Median AP RX gap | Mean retries | Median latency | Median down/up |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for summary in summaries:
        lines.append(
            "| {snapshot_id} | {sector_assessment} | {sample_count} | {asymmetry_rate_pct}% | "
            "{median_ap_rx_gap_db} dB | {mean_retry_rate_pct}% | {median_latency_p95_ms} ms | "
            "{median_down_mbps}/{median_up_mbps} Mbps |".format(**summary)
        )

    lines.extend(["", "## Flagged Links", ""])
    for summary in summaries:
        lines.append(f"### {summary['snapshot_id']}")
        flagged_links = summary["flagged_links"]
        if not flagged_links:
            lines.append("")
            lines.append("No links crossed the configured warning thresholds.")
            lines.append("")
            continue
        lines.extend(
            [
                "",
                "| CPE | AP RX gap | AP TX CCQ | Retry rate | P95 latency | Flags |",
                "| --- | ---: | ---: | ---: | ---: | --- |",
            ]
        )
        for link in flagged_links:
            lines.append(
                f"| {link['cpe_id']} | {link['ap_rx_gap_db']} dB | {link['ap_tx_ccq_pct']}% | "
                f"{link['retry_rate_pct']}% | {link['latency_p95_ms']} ms | {', '.join(link['flags'])} |"
            )
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def default_paths() -> tuple[Path, Path]:
    root = Path(__file__).resolve().parents[1]
    return root / "sample_data" / "sector_snapshot.csv", root / "reports" / "sector_health_report.md"


def main(argv: list[str] | None = None) -> int:
    default_input, default_output = default_paths()
    parser = argparse.ArgumentParser(description="Analyze sanitized wireless sector telemetry.")
    parser.add_argument("--input", type=Path, default=default_input, help="CSV telemetry snapshot to analyze.")
    parser.add_argument("--output", type=Path, default=default_output, help="Markdown report path to write.")
    parser.add_argument("--json", action="store_true", help="Print JSON summary instead of a compact text summary.")
    args = parser.parse_args(argv)

    samples = load_samples(args.input)
    summaries = analyze(samples)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_markdown(summaries), encoding="utf-8")

    if args.json:
        print(json.dumps(summaries, indent=2))
    else:
        for summary in summaries:
            print(
                "{snapshot_id}: {sector_assessment} "
                "({asymmetry_rate_pct}% AP-side RX asymmetry, median gap {median_ap_rx_gap_db} dB)".format(
                    **summary
                )
            )
        display_output = args.output
        try:
            display_output = args.output.resolve().relative_to(Path.cwd().resolve())
        except ValueError:
            pass
        print(f"report: {display_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
