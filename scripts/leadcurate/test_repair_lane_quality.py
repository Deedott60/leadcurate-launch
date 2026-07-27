#!/usr/bin/env python3
import argparse
import csv
import tempfile
from pathlib import Path

from repair_lane_quality import repair


def test_repair() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        source = root / "input.csv"
        fields = [
            "lc_parcel_id", "lc_owner_name", "lc_property_address",
            "lc_mailing_address", "lc_total_value",
        ]
        rows = [
            {
                "lc_parcel_id": "1",
                "lc_owner_name": "Owner One",
                "lc_property_address": "15901 HENRY LN HUNTERSVILLE NC",
                "lc_mailing_address": "15901 HENRY LANE HUNTERSVILLE NC 28078",
                "lc_total_value": "100000",
            },
            {
                "lc_parcel_id": "2",
                "lc_owner_name": "Owner Two",
                "lc_property_address": "100 MAIN ST",
                "lc_mailing_address": "PO BOX 2",
                "lc_total_value": "90000",
            },
            {
                "lc_parcel_id": "3",
                "lc_owner_name": "County Of Example",
                "lc_property_address": "200 MAIN ST",
                "lc_mailing_address": "300 OAK ST",
                "lc_total_value": "80000",
            },
        ]
        with source.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)

        output = root / "output.csv"
        report = root / "report.json"
        result = repair(argparse.Namespace(
            market="example", lane="absentee-owners", source=source,
            output=output, report=report, require_absentee=True,
            exclude_institutional=True, trim_top_percent=None,
            sort_wholesale=True,
        ))
        assert result["output_rows"] == 1
        with output.open(newline="", encoding="utf-8") as handle:
            repaired = list(csv.DictReader(handle))
        assert repaired[0]["lc_parcel_id"] == "2"


if __name__ == "__main__":
    test_repair()
