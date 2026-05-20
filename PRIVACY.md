# Privacy And Redaction Boundary

This repository is public-ready because it is a reconstruction, not a dump.

## Included

- Synthetic sample telemetry with neutral identifiers.
- Bucketed or representative values that preserve the shape of the diagnostic.
- A small Python analyzer that demonstrates the method.
- Generated text reports created from the synthetic sample data.

## Excluded

- Real customer names, addresses, phone numbers, emails, account IDs, or service notes.
- MAC addresses, IP addresses, exact coordinates, tower names, access point names, or site names.
- Raw screenshots, workbook exports, private file paths, internal domains, messaging IDs, or email IDs.
- Live wireless ISP telemetry and exact workbook data.

## Public narrative rule

The case study describes the operational pattern at a high level: a wireless ISP sector had a group of customer radios showing AP-side receive asymmetry, and field changes largely resolved the issue.

The public version intentionally uses generic language such as wireless ISP, sector, access point, and customer radios.

## Pre-publish check

Run:

~~~bash
python3 scripts/check_redaction.py
~~~

The script is not a complete privacy guarantee, but it catches obvious mistakes before publishing: private path fragments, internal names, emails, phone numbers, IP addresses, MAC addresses, and coordinate-like strings.

