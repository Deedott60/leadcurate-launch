#!/usr/bin/env python3
"""Shared lane-quality primitives used by builders, repairs, and QA gates."""
from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass


INSTITUTIONAL_OWNER = re.compile(
    r"\b(DEPT|DEPARTMENT|CITY OF|COUNTY OF|STATE OF|UNITED STATES|U\s*S\s*A"
    r"|SCHOOL|CHURCH|DIOCESE|BISHOP|MINISTR|BAPTIST|METHODIST|PRESBYTER"
    r"|SYNAGOGUE|MOSQUE|UNIVERSITY|COLLEGE|HOSPITAL|HEALTHCARE|AUTHORITY"
    r"|COMMISSION|TRANSPORTATION|HOUSING AUTHORITY|MUNICIPAL|TOWN OF"
    r"|VILLAGE OF|CEMETERY|FOUNDATION|PARK DISTRICT|SANITAR|WATER DIST"
    r"|FIRE DIST|LIBRARY|BANK|CREDIT UNION|RAILROAD|RAILWAY|RAPID TRANSIT"
    r"|HOMEOWNERS ASSOCIATION|ASSOCIATION|ASSN|HOA)\b",
    re.I,
)

TOKEN_ALIASES = {
    "NORTH": "N",
    "SOUTH": "S",
    "EAST": "E",
    "WEST": "W",
    "STREET": "ST",
    "AVENUE": "AVE",
    "AV": "AVE",
    "ROAD": "RD",
    "BOULEVARD": "BLVD",
    "DRIVE": "DR",
    "LANE": "LN",
    "COURT": "CT",
    "PARKWAY": "PKWY",
    "HIGHWAY": "HWY",
    "HY": "HWY",
    "PLACE": "PL",
    "TERRACE": "TER",
    "CIRCLE": "CIR",
    "TRAIL": "TRL",
}

STREET_SUFFIXES = {
    "ST", "AVE", "RD", "BLVD", "DR", "LN", "CT", "PKWY", "HWY", "PL",
    "TER", "CIR", "WAY", "TRL", "LOOP", "RUN", "PT", "SQ",
}

UNIT_MARKERS = {"APT", "APARTMENT", "UNIT", "SUITE", "STE", "#"}
STATE_CODES = {
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", "HI",
    "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", "MA", "MI",
    "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", "NM", "NY", "NC",
    "ND", "OH", "OK", "OR", "PA", "RI", "SC", "SD", "TN", "TX", "UT",
    "VT", "VA", "WA", "WV", "WI", "WY", "DC",
}


class RoleMappingError(ValueError):
    """Raised when a source does not explicitly satisfy its declared field roles."""


@dataclass(frozen=True)
class OccupancySignals:
    property_key: str
    mailing_key: str
    out_of_state: bool
    address_mismatch: bool
    absentee: bool


def validate_role_mapping(
    source_fields: Iterable[str],
    role_map: Mapping[str, Iterable[str]],
    required_roles: Iterable[str],
) -> None:
    """Require exact source-column assignments for every required semantic role."""
    available = set(source_fields)
    errors: list[str] = []
    for role in required_roles:
        mapped = [column for column in role_map.get(role, ()) if column]
        if not mapped:
            errors.append(f"{role}: no source column declared")
            continue
        missing = [column for column in mapped if column not in available]
        if len(missing) == len(mapped):
            errors.append(f"{role}: declared columns absent ({', '.join(missing)})")
    if errors:
        raise RoleMappingError("; ".join(errors))


def is_po_box(value: str) -> bool:
    return bool(re.search(r"\bP\s*\.?\s*O\.?\s*BOX\b|\bPOBOX\b", value or "", re.I))


def is_institutional_owner(value: str) -> bool:
    return bool(INSTITUTIONAL_OWNER.search(value or ""))


def canonical_address_key(value: str) -> str:
    """Return a comparable house-number and street key.

    City, state, ZIP, duplicated locality suffixes, and unit designators do not
    affect the key. Highway aliases such as ``N C 73 HY`` and ``HIGHWAY 73``
    collapse to the same route identity.
    """
    text = str(value or "").upper()
    if is_po_box(text):
        box = re.search(r"(?:P\s*\.?\s*O\.?\s*BOX|POBOX)\s*([A-Z0-9-]+)", text)
        return f"POBOX|{box.group(1)}" if box else "POBOX"

    raw_tokens = re.findall(r"[A-Z0-9]+", text)
    number_index = next(
        (index for index, token in enumerate(raw_tokens) if re.fullmatch(r"\d+[A-Z]?", token)),
        None,
    )
    if number_index is None:
        return ""

    house_number = raw_tokens[number_index]
    tokens = [TOKEN_ALIASES.get(token, token) for token in raw_tokens[number_index + 1:]]
    if not tokens:
        return f"{house_number}|"

    if "HWY" in tokens:
        route_number = next((token for token in tokens if token.isdigit()), "")
        if route_number:
            return f"{house_number}|{route_number}|HWY"

    street: list[str] = []
    for token in tokens:
        if token in UNIT_MARKERS:
            break
        if re.fullmatch(r"\d{5}(?:\d{4})?", token) or token in STATE_CODES:
            break
        street.append(token)
        if token in STREET_SUFFIXES:
            break
        if len(street) >= 3:
            break

    return "|".join([house_number, *street])


def derive_occupancy_signals(
    property_address: str,
    mailing_address: str,
    *,
    property_state: str = "",
    mailing_state: str = "",
) -> OccupancySignals:
    """Derive absentee signals only from normalized addresses and state roles."""
    property_key = canonical_address_key(property_address)
    mailing_key = canonical_address_key(mailing_address)
    normalized_property_state = (property_state or "").strip().upper()
    normalized_mailing_state = (mailing_state or "").strip().upper()
    out_of_state = bool(
        normalized_property_state
        and normalized_mailing_state
        and normalized_property_state != normalized_mailing_state
    )
    address_mismatch = bool(
        is_po_box(mailing_address)
        or (property_key and mailing_key and property_key != mailing_key)
    )
    return OccupancySignals(
        property_key=property_key,
        mailing_key=mailing_key,
        out_of_state=out_of_state,
        address_mismatch=address_mismatch,
        absentee=out_of_state or address_mismatch,
    )
