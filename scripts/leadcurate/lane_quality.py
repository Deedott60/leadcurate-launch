#!/usr/bin/env python3
"""Shared lane-quality primitives used by builders, repairs, and QA gates."""
from __future__ import annotations

import re


INSTITUTIONAL_OWNER = re.compile(
    r"\b(DEPT|DEPARTMENT|CITY OF|COUNTY OF|STATE OF|UNITED STATES|U\s*S\s*A"
    r"|SCHOOL|CHURCH|DIOCESE|BISHOP|MINISTR|BAPTIST|METHODIST|PRESBYTER"
    r"|SYNAGOGUE|MOSQUE|UNIVERSITY|COLLEGE|HOSPITAL|HEALTHCARE|AUTHORITY"
    r"|COMMISSION|TRANSPORTATION|HOUSING AUTHORITY|MUNICIPAL|TOWN OF"
    r"|VILLAGE OF|CEMETERY|FOUNDATION|PARK DISTRICT|SANITAR|WATER DIST"
    r"|FIRE DIST|LIBRARY|BANK|CREDIT UNION|RAILROAD|RAILWAY|RAPID TRANSIT"
    r"|HOMEOWNER|ASSOCIATION|ASSN|HOA)\b",
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


def is_po_box(value: str) -> bool:
    return bool(re.search(r"\bP\s*\.?\s*O\.?\s*BOX\b|\bPOBOX\b", value or "", re.I))


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
