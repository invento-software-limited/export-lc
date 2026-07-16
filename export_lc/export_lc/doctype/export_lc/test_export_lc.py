# Copyright (c) 2026, Invento Software Limited and Contributors
# See license.txt

import unittest
from unittest.mock import MagicMock, patch

import frappe
from frappe.tests import IntegrationTestCase

from export_lc.export_lc.doctype.export_lc.export_lc import make_delivery_note, make_sales_invoice


class IntegrationTestExportLC(unittest.TestCase):
	@patch("export_lc.export_lc.doctype.export_lc.export_lc.get_mapped_doc")
	@patch("export_lc.export_lc.doctype.export_lc.export_lc.frappe.get_doc")
	def test_make_sales_invoice_status(self, mock_get_doc, mock_get_mapped_doc):
		# Setup dummy source and target documents
		source_doc = MagicMock()
		source_doc.name = "EXP-LC-0001"
		source_doc.status = "Fully Utilized"
		source_doc.proforma_invoice = "PI-0001"

		target_doc = MagicMock()
		target_doc.status = "Fully Utilized"  # Simulated mapped value
		target_doc.items = []

		# Mock get_mapped_doc to execute set_missing_values callback and return target_doc
		def side_effect(doctype, source_name, mapping, target_doc, set_missing_values):
			set_missing_values(source_doc, target_doc)
			return target_doc

		mock_get_mapped_doc.side_effect = side_effect

		# Call make_sales_invoice
		res = make_sales_invoice("EXP-LC-0001", target_doc=target_doc)

		# Assert status was reset to Draft
		self.assertEqual(res.status, "Draft")

	@patch("export_lc.export_lc.doctype.export_lc.export_lc.get_mapped_doc")
	@patch("export_lc.export_lc.doctype.export_lc.export_lc.frappe.get_doc")
	def test_make_delivery_note_status(self, mock_get_doc, mock_get_mapped_doc):
		source_doc = MagicMock()
		source_doc.name = "EXP-LC-0001"
		source_doc.status = "Fully Utilized"

		target_doc = MagicMock()
		target_doc.status = "Fully Utilized"
		target_doc.items = []

		def side_effect(doctype, source_name, mapping, target_doc, set_missing_values):
			set_missing_values(source_doc, target_doc)
			return target_doc

		mock_get_mapped_doc.side_effect = side_effect

		res = make_delivery_note("EXP-LC-0001", target_doc=target_doc)

		self.assertEqual(res.status, "Draft")
