#!/usr/bin/env python3
from lane_quality import canonical_address_key, is_po_box


def test_canonical_address_key() -> None:
    pairs = [
        (
            "15901 HENRY LN HUNTERSVILLE NC HUNTERSVILLE NC",
            "15901 HENRY LANE HUNTERSVILLE NC 28078",
        ),
        ("14611 N C 73 HY", "14611 HIGHWAY 73"),
        ("320 N MAIN STREET APT 4", "320 NORTH MAIN ST"),
        ("77 WEST PARKWAY CHARLOTTE NC", "77 W PKWY CHARLOTTE NC 28202"),
    ]
    for property_address, mailing_address in pairs:
        assert canonical_address_key(property_address) == canonical_address_key(mailing_address)

    assert canonical_address_key("100 N MAIN ST") != canonical_address_key("100 S MAIN ST")
    assert is_po_box("P.O. Box 42")


if __name__ == "__main__":
    test_canonical_address_key()
