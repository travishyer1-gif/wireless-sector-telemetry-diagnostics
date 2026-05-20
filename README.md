# Wireless Sector Telemetry Diagnostics

This is a sanitized portfolio reconstruction of a field-ops diagnostic workflow for a wireless ISP sector. It shows how telemetry from an access point and connected customer radios can be turned into a practical maintenance recommendation without exposing customer, site, or internal company data.

## Why this exists

Wireless network issues often look like individual customer trouble tickets until the same signal shows up across several links on the same sector. The goal of this project is to demonstrate a lightweight way to gather sector telemetry, compare link-side symptoms, and separate customer-premise issues from an access-point-side health problem.

The original work supported a real field decision, but this repository uses synthetic identifiers and structurally faithful sample data only.

## Problem

There was an Asymmetry between AP side Signal Chain and CPE side Signal Chains across every customer on an AP as well as suspected self interference at a particular tower site.

That kind of receive asymmetry matters because it can point away from isolated customer installs and toward sector-side health, radio model/generation, firmware, channel plan, or interference conditions.

## Approach

The workflow is intentionally small:

1. Export a sector snapshot with one row per customer radio.
2. Compare access-point receive signal against customer-radio receive signal.
3. Flag links where the AP-side receive gap, retry rate, CCQ, or latency crosses a threshold.
4. Summarize whether the issue looks isolated, mixed, or sector-level.
5. Use the report to prioritize field changes instead of chasing one customer at a time.

## What the tool checks

- AP-side receive asymmetry: customer radio hears the access point much better than the access point hears the customer radio.
- Low AP transmit CCQ: useful as a second signal when asymmetric receive is present.
- High retry rate: catches links wasting airtime.
- High p95 latency: confirms whether radio health is showing up as customer-visible performance.
- Before/after comparison: the sample data includes a degraded snapshot and a post-change snapshot.

## Example result

Running the demo against sample_data/sector_snapshot.csv produces:

~~~text
SNAP_001: sector_level_ap_receive_asymmetry (62.5% AP-side RX asymmetry, median gap 14.0 dB)
SNAP_002: healthy_baseline (0.0% AP-side RX asymmetry, median gap 3.0 dB)
report: reports/sector_health_report.md
~~~

In the degraded snapshot, five of eight links cross the AP-side receive asymmetry threshold. In the post-change snapshot, the asymmetry clears and the remaining flags are link-watch items rather than a sector-wide receive problem.

## Operational outcome

The diagnostic pointed to a sector-level maintenance path rather than a single-customer repair path. The field response was to replace older customer radios connected to the access point, update firmware, and move the sector to a cleaner frequency range.

That combination largely resolved the reported problem. The useful part was not a complicated model; it was disciplined comparison of many small telemetry signals until the sector pattern was hard to ignore.

## Privacy/sanitization

This repository does not contain live telemetry, customer names, addresses, account numbers, MAC addresses, IP addresses, site names, tower names, exact coordinates, screenshots, private paths, or internal artifact names.

The sample CSV is synthetic and uses neutral identifiers such as SECTOR_A, SITE_ALPHA, and CPE_001. Numeric values are representative of the diagnostic shape but are not copied from production exports.

See PRIVACY.md for the redaction boundary and scripts/check_redaction.py for the local scan used before publishing.

## How to run

No third-party Python packages are required.

~~~bash
python3 -m src.analyze_sector
~~~

Write JSON instead of the compact console summary:

~~~bash
python3 -m src.analyze_sector --json
~~~

Run the smoke tests:

~~~bash
python3 -m unittest discover -s tests
~~~

Run the redaction check:

~~~bash
python3 scripts/check_redaction.py
~~~

## What this demonstrates about Travis/Froberto

This project demonstrates the kind of practical automation Travis and Froberto are building around real operations work:

- turning messy field telemetry into a clear diagnostic signal;
- protecting private customer and company data while still showing credible work;
- building tools that support technician decisions instead of producing abstract dashboards;
- closing the loop from diagnosis to field action to after-change validation.
