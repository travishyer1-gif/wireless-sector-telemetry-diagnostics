# Publish Checklist

Do not publish or post until the final local checks pass and the repo contents have been reviewed.

## Local verification

From the repository root:

~~~bash
python3 -m src.analyze_sector
python3 -m unittest discover -s tests
python3 scripts/check_redaction.py
git status --short
~~~

## Repository publish

1. Review README.md, PRIVACY.md, sample_data/sector_snapshot.csv, and docs/x-post.md.
2. Confirm no private identifiers, screenshots, workbook exports, private paths, exact site names, IP addresses, MAC addresses, or customer data are present.
3. Create the public GitHub repository named wireless-sector-telemetry-diagnostics.
4. Add the remote:

~~~bash
git remote add origin https://github.com/travishyer1-gif/wireless-sector-telemetry-diagnostics.git
~~~

5. Confirm the local commit exists:

~~~bash
git log --oneline -1
~~~

6. If review edits are made, commit those changes locally before publishing:

~~~bash
git add .
git commit -m "Polish public wireless sector diagnostics repo"
~~~

7. Push:

~~~bash
git push -u origin main
~~~

## X post

After the GitHub repository is public, review docs/x-post.md and post it manually or through an approval-gated workflow.
