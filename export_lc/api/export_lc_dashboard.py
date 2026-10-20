# Copyright (c) 2026, Invento Software Limited and contributors
# For license information, please see license.txt

"""Data for the Dashboard tab on the Export LC form.

Every amount is returned in the LC's own currency (F32B), the currency the
credit is drawn in. Linked documents raised in another currency are converted
through company currency at the LC's exchange rate.
"""

import re

import frappe
from frappe import _
from frappe.utils import cint, date_diff, flt, getdate, today

ITEM_FIELDS = ["parent", "item_code", "qty", "uom", "stock_qty"]


@frappe.whitelist()
def get_dashboard_data(name: str) -> dict:
	frappe.has_permission("Export LC", "read", name, throw=True)
	lc = frappe.get_doc("Export LC", name)
	return LCDashboard(lc).build()


class LCDashboard:
	def __init__(self, lc):
		self.lc = lc
		self.rate = flt(lc.conversion_rate) or 1
		self.company_currency = frappe.get_cached_value("Company", lc.company, "default_currency")
		self.invoices = self._linked("Sales Invoice", ["is_return", "outstanding_amount", "due_date",
			"rounded_total", "base_rounded_total", "party_account_currency"])
		self.deliveries = self._linked("Delivery Note", ["is_return", "per_billed"])

	def build(self):
		submitted_si = [d for d in self.invoices if d.docstatus == 1]
		submitted_dn = [d for d in self.deliveries if d.docstatus == 1]
		lc_value = flt(self.lc.grand_total)
		invoiced = sum(d.lc_value for d in submitted_si)
		delivered = sum(d.lc_value for d in submitted_dn)
		realized = sum(d.lc_value * d.paid_fraction for d in submitted_si if not d.is_return)
		outstanding = sum(d.lc_value * (1 - d.paid_fraction) for d in submitted_si if not d.is_return)
		tolerance = _tolerance_pct(self.lc.percentage_credit_amount_tolerance)
		return {
			**self._identity(),
			**self._currency(),
			**self._dates(),
			"lc_value": lc_value,
			"base_lc_value": flt(self.lc.base_grand_total),
			"tolerance_pct": tolerance,
			"max_drawable": lc_value * (1 + tolerance / 100),
			"invoiced_amount": invoiced,
			"invoiced_count": len(submitted_si),
			"invoiced_pct": _pct(invoiced, lc_value),
			"invoiced_trend": _cumulative(self.lc.date_of_issue, submitted_si),
			"delivered_amount": delivered,
			"delivered_count": len(submitted_dn),
			"delivered_pct": _pct(delivered, lc_value),
			"available_amount": max(lc_value - invoiced, 0),
			"over_drawn_amount": max(invoiced - lc_value, 0),
			"realized_amount": realized,
			"realized_pct": _pct(realized, invoiced),
			"outstanding_amount": outstanding,
			"overdue_amount": self._overdue(submitted_si),
			"items": self._items(submitted_si, submitted_dn),
			"documents": self._documents(),
			"can_read": {
				"Sales Invoice": frappe.has_permission("Sales Invoice", "read"),
				"Delivery Note": frappe.has_permission("Delivery Note", "read"),
			},
		}

	def _identity(self):
		lc = self.lc
		fields = ["name", "lc_no", "status", "docstatus", "company", "applicant", "issuing_bank",
			"beneficiary_bank", "form_of_documentary_credit", "applicable_rules", "drafts_at",
			"incoterm", "partial_shipments", "transshipment", "confirmation_instructions",
			"period_for_presentation", "port_of_loading", "port_of_discharge", "final_destination",
			"mode_of_transport", "proforma_invoice", "sales_order"]
		return {f: lc.get(f) for f in fields}

	def _currency(self):
		symbol, on_right = frappe.get_cached_value("Currency", self.lc.currency, ["symbol", "symbol_on_right"]) or ("", 0)
		return {
			"currency": self.lc.currency,
			"currency_symbol": symbol or self.lc.currency,
			"currency_symbol_on_right": cint(on_right),
			"company_currency": self.company_currency,
			"conversion_rate": self.rate,
		}

	def _dates(self):
		lc, now = self.lc, today()
		issue, expiry, shipment = lc.date_of_issue, lc.date_and_place_of_expiry, lc.latest_date_of_shipment
		span = date_diff(expiry, issue) if issue and expiry else None
		return {
			"today": now,
			"date_of_issue": issue,
			"expiry_date": expiry,
			"latest_date_of_shipment": shipment,
			"days_to_expiry": date_diff(expiry, now) if expiry else None,
			"days_to_shipment": date_diff(shipment, now) if shipment else None,
			"validity_days": span,
			"validity_elapsed_pct": _clamp(_pct(date_diff(now, issue), span)) if span else None,
			"shipment_mark_pct": _clamp(_pct(date_diff(shipment, issue), span)) if span and shipment else None,
		}

	def _linked(self, doctype, extra_fields):
		"""Non-cancelled documents raised against this LC that the user may read."""
		if not frappe.has_permission(doctype, "read"):
			return []
		fields = ["name", "docstatus", "status", "posting_date", "currency", "grand_total",
			"base_grand_total", *extra_fields]
		rows = frappe.get_list(doctype, filters={"export_lc": self.lc.name, "docstatus": ["<", 2]},
			fields=fields, order_by="posting_date asc, creation asc")
		for row in rows:
			row.doctype = doctype
			row.lc_value = self._to_lc(row)
			row.paid_fraction = _paid_fraction(row, self.company_currency) if doctype == "Sales Invoice" else 0
		return rows

	def _to_lc(self, row):
		if row.currency == self.lc.currency:
			return flt(row.grand_total)
		return flt(row.base_grand_total) / self.rate

	def _overdue(self, invoices):
		now = getdate(today())
		return sum(d.lc_value * (1 - d.paid_fraction) for d in invoices
			if not d.is_return and d.due_date and getdate(d.due_date) < now)

	def _items(self, invoices, deliveries):
		invoiced = _child_qty("Sales Invoice Item", [d.name for d in invoices])
		delivered = _child_qty("Delivery Note Item", [d.name for d in deliveries])
		rows = []
		for item in self.lc.items:
			lc_qty = flt(item.qty)
			inv_qty = _qty_in_uom(invoiced.get(item.item_code, []), item.item_code, item.uom)
			rows.append({
				"item_code": item.item_code,
				"item_name": item.item_name or item.item_code,
				"uom": item.uom,
				"lc_qty": lc_qty,
				"lc_amount": flt(item.total),
				"invoiced_qty": inv_qty,
				"delivered_qty": _qty_in_uom(delivered.get(item.item_code, []), item.item_code, item.uom),
				"invoiced_pct": _pct(inv_qty, lc_qty),
			})
		return rows

	def _documents(self):
		docs = []
		for d in self.invoices + self.deliveries:
			is_si = d.doctype == "Sales Invoice"
			docs.append({
				"doctype": d.doctype,
				"name": d.name,
				"status": d.status or ("Draft" if d.docstatus == 0 else ""),
				"posting_date": d.posting_date,
				"value": d.lc_value,
				"progress_pct": None if d.docstatus == 0 else (d.paid_fraction * 100 if is_si else flt(d.per_billed)),
				"progress_label": _("realised") if is_si else _("billed"),
			})
		return sorted(docs, key=lambda d: str(d["posting_date"] or ""), reverse=True)


def _paid_fraction(si, company_currency):
	"""Share of the invoice already settled; outstanding is held in the party account currency."""
	if si.docstatus != 1 or si.is_return:
		return 0
	in_company_ccy = (si.party_account_currency or company_currency) == company_currency
	total = (si.base_rounded_total or si.base_grand_total) if in_company_ccy else (si.rounded_total or si.grand_total)
	if not flt(total):
		return 0
	return _clamp(1 - flt(si.outstanding_amount) / flt(total), 0, 1)


def _child_qty(child_doctype, parents):
	if not parents:
		return {}
	grouped = {}
	for row in frappe.get_all(child_doctype, filters={"parent": ["in", parents]}, fields=ITEM_FIELDS):
		grouped.setdefault(row.item_code, []).append(row)
	return grouped


def _qty_in_uom(rows, item_code, uom):
	"""Sum quantities in the LC row's UOM, converting through stock UOM when they differ."""
	total = 0
	for row in rows:
		if row.uom == uom:
			total += flt(row.qty)
			continue
		factor = _uom_factor(item_code, uom)
		if factor:
			total += flt(row.stock_qty) / factor
	return total


def _uom_factor(item_code, uom):
	if frappe.get_cached_value("Item", item_code, "stock_uom") == uom:
		return 1
	return flt(frappe.db.get_value("UOM Conversion Detail", {"parent": item_code, "uom": uom}, "conversion_factor"))


def _cumulative(start_date, docs):
	"""Running drawn total, one point per submitted invoice, starting from zero at issue."""
	points, running = [{"date": start_date, "value": 0}], 0
	for d in docs:
		running += d.lc_value
		points.append({"date": d.posting_date, "value": running})
	return points


def _tolerance_pct(raw):
	"""F39A is free text such as "5", "5%" or "5/5"; the first number is the upper tolerance."""
	match = re.search(r"\d+(?:\.\d+)?", str(raw or ""))
	return flt(match.group()) if match else 0


def _pct(part, whole):
	return flt(part) / flt(whole) * 100 if flt(whole) else 0


def _clamp(value, low=0, high=100):
	return max(low, min(high, value))
