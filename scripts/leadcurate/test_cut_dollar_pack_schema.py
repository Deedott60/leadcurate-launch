#!/usr/bin/env python3
from cut_dollar_pack import STANDARD_DELIVERY_FIELDS, canonical_delivery


def test_canonical_delivery() -> None:
    fields = ["lc_owner_name", "lc_property_address", "lc_parcel_id", "extra"]
    rows = [{
        "lc_owner_name": "Owner Name",
        "lc_property_address": "100 Main St",
        "lc_parcel_id": "ABC-1",
        "extra": "kept",
    }]
    lane = {
        "lane_display": "Absentee owners",
        "market_display": "Example County",
        "source_name": "Official assessor",
        "pull_cycle": "July 2026",
    }
    output_fields, output_rows = canonical_delivery(fields, rows, lane)
    assert tuple(output_fields[:len(STANDARD_DELIVERY_FIELDS)]) == STANDARD_DELIVERY_FIELDS
    assert output_fields[-1] == "extra"
    assert output_rows[0]["owner_name"] == "Owner Name"
    assert output_rows[0]["parcel_id"] == "ABC-1"
    assert output_rows[0]["extra"] == "kept"


if __name__ == "__main__":
    test_canonical_delivery()
