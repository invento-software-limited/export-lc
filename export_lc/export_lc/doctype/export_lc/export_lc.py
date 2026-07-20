# Copyright (c) 2026, Invento Software Limited and contributors
# For license information, please see license.txt

import erpnext
import frappe
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc
from frappe.utils import flt, money_in_words, today


class ExportLC(Document):
	def validate(self):
		self.validate_one_to_one()
		self.calculate_totals()
		self.set_in_words()
		self.set_status()

	def on_submit(self):
		self.set_status(update=True)  # nosemgrep: frappe-modifying-but-not-committing-other-method

	def on_cancel(self):
		self.set_status(update=True)  # nosemgrep: frappe-modifying-but-not-committing-other-method

	def set_status(self, update=False):
		if self.docstatus == 0:
			self.status = "Draft"
		elif self.docstatus == 2:
			self.status = "Cancelled"
		else:
			# docstatus == 1 (Submitted)
			# Find linked submitted Sales Invoices
			billed_amount = (
				frappe.db.sql(
					"select sum(grand_total) from `tabSales Invoice` where export_lc=%s and docstatus=1",
					self.name,
				)[0][0]
				or 0.0
			)

			if billed_amount >= self.grand_total:
				self.status = "Fully Utilized"
			elif billed_amount > 0:
				self.status = "Partially Utilized"
			elif self.date_and_place_of_expiry and str(self.date_and_place_of_expiry) < today():
				self.status = "Expired"
			else:
				self.status = "Active"

		if update and self.name:
			self.db_set("status", self.status)

	def validate_one_to_one(self):
		if self.proforma_invoice:
			existing_lc = frappe.db.get_value(
				"Export LC",
				{"proforma_invoice": self.proforma_invoice, "name": ["!=", self.name], "docstatus": ["<", 2]},
				"name",
			)
			if existing_lc:
				from frappe.utils import get_link_to_form

				link = get_link_to_form("Export LC", existing_lc)
				pi_link = get_link_to_form("Export Proforma Invoice", self.proforma_invoice)
				frappe.throw(
					f"Export LC <b>{link}</b> already exists for Export Proforma Invoice <b>{pi_link}</b>"
				)

	def calculate_totals(self):
		self.total = 0
		self.base_total = 0
		self.total_qty = 0

		for item in self.items:
			item.total = flt(item.qty) * flt(item.rate)
			item.base_rate = flt(item.rate) * flt(self.conversion_rate or 1)
			item.base_total = flt(item.total) * flt(self.conversion_rate or 1)

			self.total += item.total
			self.base_total += item.base_total
			self.total_qty += flt(item.qty)

		self.grand_total = flt(self.total)
		self.base_grand_total = self.grand_total * flt(self.conversion_rate or 1)

		self.rounded_total = round(self.grand_total)
		self.base_rounded_total = round(self.base_grand_total)

	def set_in_words(self):
		self.in_words = money_in_words(self.grand_total, self.currency)
		company_currency = frappe.get_cached_value("Company", self.company, "default_currency")
		if company_currency:
			self.base_in_words = money_in_words(self.base_grand_total, company_currency)


@frappe.whitelist()
def make_sales_invoice(source_name, target_doc=None):
	"""Create Sales Invoice from Export LC and its linked Export Proforma Invoice."""

	def set_missing_values(source, target):
		target.sales_type = "Export"
		target.naming_series = "COM-INV-.YYYY.-"
		target.export_lc = source.name
		target.status = "Draft"

		if source.proforma_invoice:
			pi = frappe.get_doc("Export Proforma Invoice", source.proforma_invoice)
			target.export_proforma_invoice = pi.name
			target.pi_number = pi.pi_number
			target.pi_date = pi.pi_date

			# Bank Information
			target.bank = pi.bank
			target.swift_code = pi.swift_code
			if pi.get("bank_branch"):
				target.branch = pi.bank_branch
			target.account_number__iban = pi.account_number_iban
			target.bank_address = pi.bank_address

			# Buyer / Customer Information
			target.buyer = pi.buyer
			target.buyer_name = pi.buyer_name
			if pi.get("buyer_contact"):
				target.buyer_contact = pi.buyer_contact
			if pi.get("buyer_phone_no"):
				target.buyer_phone_no = pi.buyer_phone_no
			if pi.get("buyer_email"):
				target.buyer_email = pi.buyer_email
			target.buyer_address = pi.buyer_address
			target.buyer_full_address = pi.buyer_address_display

			# Trade Details
			target.freight_charges = pi.freight_charges
			if pi.get("delivery_terms"):
				target.delivery_terms = pi.delivery_terms
			if pi.get("safta_clause"):
				target.safta_clause = pi.safta_clause

			# Shipment Details
			target.mode_of_transport = pi.mode_of_transport
			if pi.get("mode_of_shipment"):
				target.mode_of_shipment = pi.mode_of_shipment
			if pi.get("shipment_conditions"):
				target.shipment_conditions = pi.shipment_conditions

			# Map items from PI if LC items are generic or missing logistics
			pi_items_map = {item.item_code: item for item in pi.items}
			for item in target.items:
				if item.item_code in pi_items_map:
					pi_item = pi_items_map[item.item_code]
					item.brand = pi_item.brand
					item.packing_type = pi_item.packing_type
					item.total_qty = pi_item.total_qty
					item.total_volume_weight = pi_item.total_volume_weight
					item.rate_per_carton = pi_item.rate_per_carton
					item.total_amount_usd = pi_item.total_amount_usd

		# Run standard missing values logic to fetch default income accounts, taxes, etc.
		target.flags.ignore_permissions = True
		target.run_method("set_missing_values")
		target.run_method("calculate_taxes_and_totals")

	doclist = get_mapped_doc(
		"Export LC",
		source_name,
		{
			"Export LC": {
				"doctype": "Sales Invoice",
				"field_map": {
					"lc_no": "lc_number",
					"applicant": "customer",
					"currency": "currency",
					"incoterm": "incoterm",
					"percentage_credit_amount_tolerance": "tolerance_",
					"port_of_loading": "port_of_loading",
					"final_destination": "country_of_final_destination",
					"transshipment": "transshipment",
					"partial_shipments": "partial_shipment",
					"conversion_rate": "conversion_rate",
				},
			},
			"Export LC Item": {
				"doctype": "Sales Invoice Item",
				"field_map": {
					"item_code": "item_code",
					"item_name": "item_name",
					"description": "description",
					"hs_code": "hs_code",
					"qty": "qty",
					"uom": "uom",
					"rate": "rate",
					"base_rate": "base_rate",
					"total": "amount",
					"base_total": "base_amount",
				},
			},
		},
		target_doc,
		set_missing_values,
	)

	return doclist


@frappe.whitelist()
def make_delivery_note(source_name, target_doc=None):
	"""Create Delivery Note from Export LC and its linked Sales Invoice."""

	def set_missing_values(source, target):
		target.sales_type = "Export"
		target.export_lc = source.name
		target.status = "Draft"

		# Find linked Sales Invoice
		pi_name = frappe.db.get_value(
			"Sales Invoice", {"export_lc": source.name, "docstatus": ["<", 2]}, "name"
		)
		if pi_name:
			pi = frappe.get_doc("Sales Invoice", pi_name)
			target.sales_invoice = pi.name

			# Map fields from PI if they exist
			fields_to_map = [
				"pi_number",
				"pi_date",
				"bank",
				"swift_code",
				"branch",
				"account_number__iban",
				"bank_address",
				"buyer",
				"buyer_name",
				"buyer_contact",
				"buyer_phone_no",
				"buyer_email",
				"buyer_address",
				"buyer_full_address",
				"freight_charges",
				"delivery_terms",
				"safta_clause",
				"mode_of_transport",
				"mode_of_shipment",
				"shipment_conditions",
			]
			for field in fields_to_map:
				if hasattr(pi, field) and getattr(pi, field):
					setattr(target, field, getattr(pi, field))

			# Map items from PI to get logistics data
			pi_items_map = {item.item_code: item for item in pi.items}
			for item in target.items:
				if item.item_code in pi_items_map:
					pi_item = pi_items_map[item.item_code]
					item.hs_code = pi_item.get("hs_code")
					item.country_of_origin = pi_item.get("country_of_origin")
					item.packing_type = pi_item.get("packing_type")
					item.total_qty = pi_item.get("total_qty")
					item.total_amount_usd = pi_item.get("total_amount_usd")

	doclist = get_mapped_doc(
		"Export LC",
		source_name,
		{
			"Export LC": {
				"doctype": "Delivery Note",
				"field_map": {
					"lc_no": "lc_number",
					"applicant": "customer",
					"currency": "currency",
					"incoterm": "incoterm",
					"percentage_credit_amount_tolerance": "tolerance_",
					"port_of_loading": "port_of_loading",
					"final_destination": "country_of_final_destination",
					"transshipment": "transshipment",
					"partial_shipments": "partial_shipment",
					"conversion_rate": "conversion_rate",
				},
			},
			"Export LC Item": {
				"doctype": "Delivery Note Item",
				"field_map": {
					"item_code": "item_code",
					"item_name": "item_name",
					"description": "description",
					"qty": "qty",
					"uom": "uom",
					"rate": "rate",
				},
			},
		},
		target_doc,
		set_missing_values,
	)

	return doclist


def update_lc_status_on_invoice_event(doc, method):
	if doc.export_lc:
		lc = frappe.get_doc("Export LC", doc.export_lc)
		lc.set_status()
		lc.db_set("status", lc.status)


def update_expired_lcs():
	"""Daily job to mark submitted, un-utilized, expired LCs as Expired."""
	current_date = today()

	# Find all submitted LCs that are Active and have expired
	expired_lcs = frappe.db.get_all(
		"Export LC",
		filters={"docstatus": 1, "status": "Active", "date_and_place_of_expiry": ["<", current_date]},
		pluck="name",
	)

	for name in expired_lcs:
		lc = frappe.get_doc("Export LC", name)
		lc.set_status()
		lc.db_set("status", lc.status)
