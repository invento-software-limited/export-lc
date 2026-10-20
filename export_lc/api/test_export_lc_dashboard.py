# Copyright (c) 2026, Invento Software Limited and Contributors
# See license.txt

import unittest
from unittest.mock import patch

import frappe

from export_lc.api import export_lc_dashboard as dash


def _si(**kw):
	base = {"docstatus": 1, "is_return": 0, "party_account_currency": "BDT", "outstanding_amount": 0,
		"grand_total": 100, "rounded_total": 100, "base_grand_total": 12000, "base_rounded_total": 12000}
	return frappe._dict({**base, **kw})


class TestExportLCDashboardHelpers(unittest.TestCase):
	def test_tolerance_reads_first_number_of_free_text(self):
		self.assertEqual(dash._tolerance_pct("5"), 5)
		self.assertEqual(dash._tolerance_pct("10/5"), 10)
		self.assertEqual(dash._tolerance_pct("2.5 %"), 2.5)
		self.assertEqual(dash._tolerance_pct(None), 0)

	def test_paid_fraction_uses_party_account_currency(self):
		self.assertEqual(dash._paid_fraction(_si(outstanding_amount=6000), "BDT"), 0.5)
		usd_party = _si(party_account_currency="USD", outstanding_amount=25)
		self.assertEqual(dash._paid_fraction(usd_party, "BDT"), 0.75)

	def test_paid_fraction_ignores_drafts_and_returns(self):
		self.assertEqual(dash._paid_fraction(_si(docstatus=0), "BDT"), 0)
		self.assertEqual(dash._paid_fraction(_si(is_return=1), "BDT"), 0)

	def test_qty_converts_other_uom_through_stock_qty(self):
		rows = [frappe._dict(uom="Nos", qty=5, stock_qty=5), frappe._dict(uom="Box", qty=2, stock_qty=24)]
		with patch.object(dash, "_uom_factor", return_value=1):
			self.assertEqual(dash._qty_in_uom(rows, "ITEM", "Nos"), 29)

	def test_cumulative_starts_at_zero_on_issue(self):
		docs = [frappe._dict(posting_date="2026-01-05", lc_value=40), frappe._dict(posting_date="2026-02-01", lc_value=60)]
		points = dash._cumulative("2026-01-01", docs)
		self.assertEqual([p["value"] for p in points], [0, 40, 100])
