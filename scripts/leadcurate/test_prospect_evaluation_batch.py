#!/usr/bin/env python3
"""Regression tests for prospect evaluation cuts."""
from __future__ import annotations

import unittest

from build_prospect_evaluation_batch import (
    DESHAWN_MASSACHUSETTS_800,
    clean_customer_property_zip,
    is_eligible,
    owner_actionability,
)


def base_row(category: str) -> dict[str, str]:
    return {
        "owner_name": "TEST OWNER LLC",
        "property_address": "10 MAIN ST BOSTON MA 02110",
        "parcel_id": "1|TEST",
        "mailing_address": "PO BOX 100",
        "mailing_city": "BOSTON",
        "mailing_state": "MA",
        "mailing_zip": "02110",
        "primary_category_key": category,
        "FY": "2026",
        "USE_DESC": "Three-Family Residential",
        "total_value": "500000",
        "building_value": "350000",
        "acreage": "0.25",
        "case_number": "26 SM 000001",
        "filed_date": "06/01/2026",
        "years_owned": "15",
        "is_absentee_owner": "yes",
        "is_out_of_state_owner": "no",
        "information_not_available": "",
    }


class ProspectEvaluationBatchTests(unittest.TestCase):
    def test_deshawn_profile_is_exactly_800(self) -> None:
        self.assertEqual(sum(DESHAWN_MASSACHUSETTS_800.values()), 800)
        self.assertEqual(DESHAWN_MASSACHUSETTS_800["tax-title"], 4)

    def test_false_zero_zip_is_removed_and_disclosed(self) -> None:
        row = base_row("pre-foreclosure")
        row["property_zip"] = "00000"
        row["property_address"] = "10 MAIN ST BOSTON MA 00000"
        clean_customer_property_zip(row)
        self.assertEqual(row["property_zip"], "")
        self.assertEqual(row["property_address"], "10 MAIN ST BOSTON MA")
        self.assertIn("Property ZIP", row["information_not_available"])

    def test_utility_right_of_way_is_not_eligible(self) -> None:
        row = base_row("industrial")
        row["USE_DESC"] = "Electric Transmission Right-of-Way"
        eligible, reason = is_eligible(row, "industrial", 2025)
        self.assertFalse(eligible)
        self.assertEqual(reason, "non_acquisition_use")

    def test_utility_owner_is_not_eligible(self) -> None:
        row = base_row("industrial")
        row["owner_name"] = "COMMONWEALTH GAS COMPANY"
        row["USE_DESC"] = "Industrial Warehouse"
        eligible, reason = is_eligible(row, "industrial", 2025)
        self.assertFalse(eligible)
        self.assertEqual(reason, "non_acquisition_owner")

    def test_pre_foreclosure_requires_current_court_evidence(self) -> None:
        row = base_row("pre-foreclosure")
        row["case_number"] = ""
        eligible, reason = is_eligible(row, "pre-foreclosure", 2025)
        self.assertFalse(eligible)
        self.assertEqual(reason, "missing_current_court_evidence")

    def test_out_of_state_requires_non_massachusetts_mail_state(self) -> None:
        row = base_row("out-of-state-owners")
        eligible, reason = is_eligible(row, "out-of-state-owners", 2025)
        self.assertFalse(eligible)
        self.assertEqual(reason, "missing_out_of_state_evidence")

    def test_individual_and_property_entities_rank_ahead_of_generic_corporations(self) -> None:
        individual = base_row("industrial")
        individual["owner_name"] = "JANE SMITH"
        property_llc = base_row("industrial")
        property_llc["owner_name"] = "MAIN STREET PROPERTIES LLC"
        corporation = base_row("industrial")
        corporation["owner_name"] = "MANUFACTURING CORPORATION"
        self.assertGreater(owner_actionability(individual), owner_actionability(property_llc))
        self.assertGreater(owner_actionability(property_llc), owner_actionability(corporation))


if __name__ == "__main__":
    unittest.main()
