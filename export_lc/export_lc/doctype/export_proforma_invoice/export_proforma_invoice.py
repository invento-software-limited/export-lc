# Copyright (c) 2026, Invento Software Limited and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc
from frappe.utils import flt, money_in_words


class ExportProformaInvoice(Document):
	def validate(self):
		self.validate_one_to_one()
		self.calculate_totals()
		self.set_in_words()

	def validate_one_to_one(self):
		if self.sales_order:
			existing_pi = frappe.db.get_value(
				"Export Proforma Invoice",
				{"sales_order": self.sales_order, "name": ["!=", self.name], "docstatus": ["<", 2]},
				"name",
			)
			if existing_pi:
				from frappe.utils import get_link_to_form

				link = get_link_to_form("Export Proforma Invoice", existing_pi)
				so_link = get_link_to_form("Sales Order", self.sales_order)
				frappe.throw(
					f"Export Proforma Invoice <b>{link}</b> already exists for Sales Order <b>{so_link}</b>"
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
		company_currency = frappe.db.get_value("Company", self.company, "default_currency")
		if company_currency:
			self.base_in_words = money_in_words(self.base_grand_total, company_currency)


@frappe.whitelist()
def make_export_proforma_invoice(source_name: str, target_doc: str | None = None):
	"""Create Export Proforma Invoice from Sales Order."""

	def set_missing_values(source, target):
		target.sales_order = source.name
		target.buyer = source.customer  # Customer is the buyer in Export PI

		import re

		if target.address_display:
			target.address_display = re.sub(r"<br\s*/?>", "\n", target.address_display, flags=re.IGNORECASE)
		if target.buyer_address_display:
			target.buyer_address_display = re.sub(
				r"<br\s*/?>", "\n", target.buyer_address_display, flags=re.IGNORECASE
			)

	doclist = get_mapped_doc(
		"Sales Order",
		source_name,
		{
			"Sales Order": {
				"doctype": "Export Proforma Invoice",
				"field_map": {
					"name": "sales_order",
					"company": "company",
					"customer": "buyer",
					"customer_name": "buyer_name",
					"customer_address": "buyer_address",
					"address_display": "buyer_address_display",
					"contact_person": "buyer_contact",
					"contact_mobile": "buyer_phone_no",
					"contact_email": "buyer_email",
					"bank": "bank",
					"swift_code": "swift_code",
					"branch": "bank_branch",
					"account_number__iban": "account_number_iban",
					"bank_address": "bank_address",
					"company_address": "company_address",
					"company_address_display": "address_display",
					"company_contact_person": "company_contact",
					"currency": "currency",
					"conversion_rate": "conversion_rate",
					"payment_term": "payment_terms",
					"incoterm": "incoterm",
					"tolerance_": "tolerance_percent",
					"freight_charges": "freight_charges",
					"delivery_terms": "delivery_terms",
					"safta_clause": "safta_clause",
					"port_of_loading": "port_of_loading",
					"port_of_discharge": "port_of_discharge",
					"country_of_final_destination": "country_of_final_destination",
					"mode_of_transport": "mode_of_transport",
					"mode_of_shipment": "mode_of_shipment",
					"partial_shipment": "partial_shipment",
					"transshipment": "transshipment",
					"shipment_conditions": "shipment_conditions",
					"tc_name": "tc_name",
					"terms": "terms",
				},
			},
			"Sales Order Item": {
				"doctype": "Export Proforma Invoice Item",
				"field_map": {
					"item_code": "item_code",
					"item_name": "item_name",
					"description": "description",
					"brand": "brand",
					"qty": "qty",
					"uom": "uom",
					"rate": "rate",
					"base_rate": "base_rate",
					"amount": "total",
					"base_amount": "base_total",
					"total_qty": "total_qty",
					"total_amount_usd": "total_amount_usd",
				},
			},
		},
		target_doc,
		set_missing_values,
	)

	return doclist


@frappe.whitelist()
def make_export_lc(source_name: str, target_doc: str | None = None):
	"""Create Export LC from Export Proforma Invoice."""

	def set_missing_values(source, target):
		target.proforma_invoice = source.name
		target.currency = source.currency
		target.lc_amount = source.grand_total
		target.beneficiary = source.company

	doclist = get_mapped_doc(
		"Export Proforma Invoice",
		source_name,
		{
			"Export Proforma Invoice": {
				"doctype": "Export LC",
				"field_map": {
					"company": "company",
					"buyer": "applicant",
					"buyer_address": "applicant_address",
					"bank": "beneficiary_bank",
					"company_address": "beneficiary_address",
					"country_of_origin": "country_of_origin",
					"currency": "currency",
					"conversion_rate": "conversion_rate",
					"total": "total",
					"base_total": "base_total",
					"grand_total": "grand_total",
					"base_grand_total": "base_grand_total",
					"rounded_total": "rounded_total",
					"base_rounded_total": "base_rounded_total",
					"in_words": "in_words",
					"base_in_words": "base_in_words",
					"payment_terms": "drafts_at",
					"incoterm": "incoterm",
					"tolerance_percent": "percentage_credit_amount_tolerance",
					"freight_charges": "freight_charges",
					"delivery_terms": "delivery_terms",
					"safta_clause": "safta_clause",
					"port_of_loading": "port_of_loading",
					"port_of_discharge": "port_of_discharge",
					"country_of_final_destination": "final_destination",
					"mode_of_transport": "mode_of_transport",
					"mode_of_shipment": "mode_of_shipment",
					"transshipment": "transshipment",
					"partial_shipment": "partial_shipments",
					"shipment_conditions": "shipment_conditions",
					"sales_order": "sales_order",
				},
			},
			"Export Proforma Invoice Item": {
				"doctype": "Export LC Item",
				"field_map": {
					"item_code": "item_code",
					"item_name": "item_name",
					"description": "description",
					"brand": "brand",
					"hs_code": "hs_code",
					"qty": "qty",
					"uom": "uom",
					"rate": "rate",
					"base_rate": "base_rate",
					"total": "total",
					"base_total": "base_total",
					"packing_type": "packing_type",
					"packing_details": "packing_details",
					"total_qty": "total_qty",
					"total_volume_weight": "total_volume_weight",
					"rate_per_carton": "rate_per_carton",
					"total_amount_usd": "total_amount_usd",
				},
			},
		},
		target_doc,
		set_missing_values,
	)

	return doclist


@frappe.whitelist()
def make_sales_invoice(source_name: str, target_doc: str | None = None):
	"""Create Sales Invoice from Export Proforma Invoice."""

	def set_missing_values(source, target):
		target.sales_type = "Export"
		target.naming_series = "COM-INV-.YYYY.-"
		target.export_proforma_invoice = source.name

		# Run standard missing values logic to fetch default income accounts, taxes, etc.
		target.flags.ignore_permissions = True
		target.run_method("set_missing_values")
		target.run_method("calculate_taxes_and_totals")

	doclist = get_mapped_doc(
		"Export Proforma Invoice",
		source_name,
		{
			"Export Proforma Invoice": {
				"doctype": "Sales Invoice",
				"field_map": {
					"pi_number": "pi_number",
					"pi_date": "pi_date",
					"buyer": "customer",
					"buyer_name": "customer_name",
					"buyer_address": "customer_address",
					"buyer_contact": "contact_person",
					"buyer_phone_no": "contact_phone",
					"buyer_email": "contact_email",
					"company": "company",
					"bank": "bank",
					"swift_code": "swift_code",
					"bank_branch": "branch",
					"account_number_iban": "account_number__iban",
					"bank_address": "bank_address",
					"currency": "currency",
					"conversion_rate": "conversion_rate",
					"payment_terms": "payment_terms",
					"incoterm": "incoterm",
					"tolerance_percent": "tolerance_percent",
					"freight_charges": "freight_charges",
					"grand_total": "grand_total",
					"base_grand_total": "base_grand_total",
					"rounded_total": "rounded_total",
					"base_rounded_total": "base_rounded_total",
					"delivery_terms": "delivery_terms",
					"safta_clause": "safta_clause",
					"port_of_loading": "port_of_loading",
					"port_of_discharge": "port_of_discharge",
					"country_of_final_destination": "country_of_final_destination",
					"mode_of_transport": "mode_of_transport",
					"mode_of_shipment": "mode_of_shipment_container_details",
					"transshipment": "transshipment",
					"partial_shipment": "partial_shipment",
					"shipment_conditions": "shipment_conditions",
					"sales_order": "sales_order",
				},
			},
			"Export Proforma Invoice Item": {
				"doctype": "Sales Invoice Item",
				"field_map": {
					"item_code": "item_code",
					"item_name": "item_name",
					"description": "description",
					"brand": "brand",
					"hs_code": "hs_code",
					"qty": "qty",
					"uom": "uom",
					"rate": "rate",
					"base_rate": "base_rate",
					"amount": "amount",
					"base_amount": "base_amount",
					"packing_type": "packing_type",
					"total_qty": "total_qty",
					"total_volume_weight": "total_volume_weight",
					"rate_per_carton": "rate_per_carton",
					"total_amount_usd": "total_amount_usd",
				},
			},
		},
		target_doc,
		set_missing_values,
	)

	return doclist
