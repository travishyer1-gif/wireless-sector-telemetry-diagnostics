from pathlib import Path
import contextlib
import io
import tempfile
import unittest

from src.analyze_sector import analyze, load_samples, main, render_markdown


ROOT = Path(__file__).resolve().parents[1]
SAMPLE_CSV = ROOT / "sample_data" / "sector_snapshot.csv"


class AnalyzeSectorTests(unittest.TestCase):
    def test_detects_before_and_after_sector_health(self) -> None:
        summaries = analyze(load_samples(SAMPLE_CSV))
        by_snapshot = {summary["snapshot_id"]: summary for summary in summaries}

        self.assertEqual(by_snapshot["SNAP_001"]["sector_assessment"], "sector_level_ap_receive_asymmetry")
        self.assertEqual(by_snapshot["SNAP_001"]["asymmetry_link_count"], 5)
        self.assertGreaterEqual(by_snapshot["SNAP_001"]["median_ap_rx_gap_db"], 10)

        self.assertEqual(by_snapshot["SNAP_002"]["sector_assessment"], "healthy_baseline")
        self.assertEqual(by_snapshot["SNAP_002"]["asymmetry_link_count"], 0)
        self.assertLess(by_snapshot["SNAP_002"]["median_ap_rx_gap_db"], 5)

    def test_report_renders_without_private_identifiers(self) -> None:
        report = render_markdown(analyze(load_samples(SAMPLE_CSV)))
        self.assertIn("sector_level_ap_receive_asymmetry", report)
        self.assertIn("SNAP_002", report)
        self.assertNotIn("Advan" + "tage", report)

    def test_cli_writes_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "report.md"
            with contextlib.redirect_stdout(io.StringIO()):
                exit_code = main(["--input", str(SAMPLE_CSV), "--output", str(output)])
            self.assertEqual(exit_code, 0)
            self.assertIn("Sector Health Report", output.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
