#!/usr/bin/env python3
from lane_quality import (
    RoleMappingError,
    canonical_address_key,
    derive_occupancy_signals,
    is_institutional_owner,
    is_po_box,
    validate_role_mapping,
)


def test_mecklenburg_duplicated_locality_fixture() -> None:
    property_address = "15901 HENRY LN HUNTERSVILLE NC HUNTERSVILLE NC"
    mailing_address = "15901 HENRY LANE HUNTERSVILLE NC 28078"
    assert canonical_address_key(property_address) == canonical_address_key(mailing_address)
    assert not derive_occupancy_signals(
        property_address,
        mailing_address,
        property_state="NC",
        mailing_state="NC",
    ).absentee


def test_nc_highway_fixture() -> None:
    assert canonical_address_key("14611 N C 73 HY") == canonical_address_key("14611 HIGHWAY 73")


def test_canonical_address_key() -> None:
    pairs = [
        ("320 N MAIN STREET APT 4", "320 NORTH MAIN ST"),
        ("77 WEST PARKWAY CHARLOTTE NC", "77 W PKWY CHARLOTTE NC 28202"),
    ]
    for property_address, mailing_address in pairs:
        assert canonical_address_key(property_address) == canonical_address_key(mailing_address)
    assert canonical_address_key("100 N MAIN ST") != canonical_address_key("100 S MAIN ST")
    assert is_po_box("P.O. Box 42")


def test_shared_occupancy_and_institutional_rules() -> None:
    assert derive_occupancy_signals(
        "100 MAIN ST",
        "PO BOX 42",
        property_state="NC",
        mailing_state="NC",
    ).absentee
    assert derive_occupancy_signals(
        "100 MAIN ST",
        "100 MAIN STREET",
        property_state="NC",
        mailing_state="VA",
    ).out_of_state
    assert is_institutional_owner("Charlotte Mecklenburg School Board")
    assert not is_institutional_owner("Jane Homeowner")


def test_explicit_role_mapping() -> None:
    validate_role_mapping(
        ("PARCEL_ID", "OWNER_NAME", "SITE_ADDRESS"),
        {
            "parcel": ("PARCEL_ID",),
            "owner": ("OWNER_NAME",),
            "property_street": ("SITE_ADDRESS",),
        },
        ("parcel", "owner", "property_street"),
    )
    try:
        validate_role_mapping(
            ("parcel_number", "owner", "address"),
            {
                "parcel": ("PARCEL_ID",),
                "owner": ("OWNER_NAME",),
                "property_street": ("SITE_ADDRESS",),
            },
            ("parcel", "owner", "property_street"),
        )
    except RoleMappingError:
        pass
    else:
        raise AssertionError("Fuzzy or guessed source roles must be rejected")


if __name__ == "__main__":
    test_mecklenburg_duplicated_locality_fixture()
    test_nc_highway_fixture()
    test_canonical_address_key()
    test_shared_occupancy_and_institutional_rules()
    test_explicit_role_mapping()
