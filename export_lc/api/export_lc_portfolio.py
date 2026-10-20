# Copyright (c) 2026, Invento Software Limited and contributors
# For license information, please see license.txt

"""Data for the Export LC page dashboard (/app/export-lc-dashboard).

Portfolio totals mix LC currencies, so every amount here is in the company's
currency (the base_* fields). "Period" figures follow the selected window;
balances, expiry and the worklist are as of today.
"""

import frappe
from frappe import _
from frappe.core.doctype.user_permission.user_permission import get_user_permissions
from frappe.utils import cint, date_diff, flt, getdate, today

from export_lc.api import period as periods
from export_lc.api.export_lc_dashboard import _clamp, _paid_fraction, _pct

LIVE = ("Active", "Partially Utilized")
RUNWAY = [("≤15 d", 0, 15), ("16–30 d", 16, 30), ("31–60 d", 31, 60), ("61–90 d", 61, 90), ("90+ d", 91, None)]
MAX_PAGE = 100


@frappe.whitelist()
def get_dashboard_data(company=None, period="1y", from_date=None, to_date=None, start=0, page_length=20):
	frappe.has_permission("Export LC", "read", throw=True)
	company = _validate_company(company)
	start, page_length = max(cint(start), 0), min(max(cint(page_length), 1), MAX_PAGE)
	return Portfolio(company, period, from_date, to_date).build(start, page_length)


def _validate_company(company):
	allowed = _allowed_companies()
	company = company or frappe.defaults.get_user_default("Company") or (allowed[0] if allowed else None)
	if not company or company not in allowed:
		frappe.throw(_("You do not have access to company {0}").format(company or ""), frappe.PermissionError)
	return company


def _allowed_companies():
	"""Companies the user is not restricted from by User Permissions."""
	names = frappe.get_all("Company", pluck="name", order_by="name asc")
	restricted = get_user_permissions().get("Company")
	if restricted:
		allowed = {p.get("doc") for p in restricted}
		names = [n for n in names if n in allowed]
	return names


class Portfolio:
	def __init__(self, company, period, from_date, to_date):
		self.company, self.period = company, period
		self.today = getdate(today())
		self.currency = frappe.get_cached_value("Company", company, "default_currency")
		self.start, self.end, self.label = periods.resolve(period, from_date, to_date, self.today)
		self.lcs = self._lcs()
		self.invoices = self._linked("Sales Invoice", ["is_return", "outstanding_amount", "rounded_total",
			"base_rounded_total", "grand_total", "party_account_currency"])
		self.deliveries = self._linked("Delivery Note", [])
		self._attach_drawn()

	def build(self, start, page_length):
		currency = self.currency
		symbol, on_right = frappe.get_cached_value("Currency", currency, ["symbol", "symbol_on_right"]) or ("", 0)
		live = [lc for lc in self.lcs if lc.is_live]
		cohort = [lc for lc in self.lcs if self._in_period(lc.date_of_issue)]
		return {
			"company": self.company,
			"companies": _allowed_companies(),
			"currency": currency,
			"currency_symbol": symbol or currency,
			"currency_symbol_on_right": cint(on_right),
			"today": self.today,
			"period": self.period,
			"period_start": self.start,
			"period_end": self.end,
			"period_label": self.label,
			"opened": self._opened(cohort),
			"drawn": self._drawn(),
			"undrawn": {"amount": sum(lc.undrawn for lc in live), "count": len(live),
				"drawn": sum(min(lc.drawn, lc.value) for lc in live), "value": sum(lc.value for lc in live)},
			"expiring": self._expiring(live),
			"cohort": self._cohort(cohort),
			"chart": self._chart(),
			"status_mix": self._status_mix(cohort),
			"top_applicants": self._top_applicants(cohort),
			"worklist": self._worklist(start, page_length),
			"can_read": {dt: frappe.has_permission(dt, "read") for dt in ("Sales Invoice", "Delivery Note")},
		}

	def _lcs(self):
		fields = ["name", "lc_no", "applicant", "issuing_bank", "status", "currency", "grand_total",
			"base_grand_total", "date_of_issue", "date_and_place_of_expiry", "latest_date_of_shipment"]
		return frappe.get_list("Export LC", filters={"company": self.company, "docstatus": 1},
			fields=fields, limit_page_length=0, order_by="date_of_issue asc")

	def _linked(self, doctype, extra):
		if not frappe.has_permission(doctype, "read"):
			return []
		fields = ["name", "export_lc", "posting_date", "docstatus", "base_grand_total", "base_rounded_total"]
		rows = frappe.get_list(doctype, filters={"company": self.company, "docstatus": 1, "export_lc": ["is", "set"]},
			fields=list(dict.fromkeys(fields + extra)), limit_page_length=0)
		for row in rows:
			row.paid_fraction = _paid_fraction(row, self.currency) if doctype == "Sales Invoice" else 0
		return rows

	def _attach_drawn(self):
		drawn, delivered = {}, {}
		for si in self.invoices:
			drawn[si.export_lc] = drawn.get(si.export_lc, 0) + flt(si.base_grand_total)
		for dn in self.deliveries:
			delivered[dn.export_lc] = delivered.get(dn.export_lc, 0) + flt(dn.base_grand_total)
		for lc in self.lcs:
			lc.value = flt(lc.base_grand_total)
			lc.drawn = drawn.get(lc.name, 0)
			lc.delivered = delivered.get(lc.name, 0)
			lc.undrawn = max(lc.value - lc.drawn, 0)
			lc.days_to_expiry = date_diff(lc.date_and_place_of_expiry, self.today) if lc.date_and_place_of_expiry else None
			lc.is_live = lc.status in LIVE and (lc.days_to_expiry is None or lc.days_to_expiry >= 0)
			lc.is_lapsed = lc.days_to_expiry is not None and lc.days_to_expiry < 0 and lc.undrawn > 0 \
				and lc.status not in ("Closed", "Fully Utilized")

	def _in_period(self, date, start=None, end=None):
		return bool(date) and (start or self.start) <= getdate(date) <= (end or self.end)

	def _opened(self, cohort):
		prior_start, prior_end = periods.previous(self.start, self.end)
		prior = sum(lc.value for lc in self.lcs if self._in_period(lc.date_of_issue, prior_start, prior_end))
		amount = sum(lc.value for lc in cohort)
		return {"amount": amount, "count": len(cohort), "prior_amount": prior,
			"change_pct": (amount - prior) / prior * 100 if prior else None,
			"trend": self._series(self.lcs, "date_of_issue", "value")}

	def _drawn(self):
		rows = [si for si in self.invoices if self._in_period(si.posting_date)]
		amount = sum(flt(si.base_grand_total) for si in rows)
		realized = sum(flt(si.base_grand_total) * si.paid_fraction for si in rows if not si.is_return)
		return {"amount": amount, "count": len(rows), "realized": realized, "realized_pct": _pct(realized, amount),
			"outstanding": sum(flt(si.base_grand_total) * (1 - si.paid_fraction) for si in rows if not si.is_return)}

	def _expiring(self, live):
		runway = []
		for label, lo, hi in RUNWAY:
			hit = [lc for lc in live if lc.days_to_expiry is not None and lc.days_to_expiry >= lo and (hi is None or lc.days_to_expiry <= hi)]
			runway.append({"label": label, "from_days": lo, "to_days": hi, "amount": sum(lc.undrawn for lc in hit), "count": len(hit)})
		soon = [lc for lc in live if lc.days_to_expiry is not None and lc.days_to_expiry <= 30]
		lapsed = [lc for lc in self.lcs if lc.is_lapsed]
		return {"amount": sum(lc.undrawn for lc in soon), "count": len(soon), "runway": runway,
			"lapsed_amount": sum(lc.undrawn for lc in lapsed), "lapsed_count": len(lapsed)}

	def _cohort(self, cohort):
		names = {lc.name for lc in cohort}
		opened = sum(lc.value for lc in cohort)
		invoiced = sum(lc.drawn for lc in cohort)
		realized = sum(flt(si.base_grand_total) * si.paid_fraction for si in self.invoices if si.export_lc in names and not si.is_return)
		delivered = sum(lc.delivered for lc in cohort)
		return {"opened": opened, "count": len(cohort), "delivered": delivered, "delivered_pct": _pct(delivered, opened),
			"invoiced": invoiced, "invoiced_pct": _pct(invoiced, opened), "realized": realized,
			"realized_pct": _pct(realized, invoiced), "outstanding": max(invoiced - realized, 0), "names": sorted(names)}

	def _chart(self):
		marks = periods.buckets(self.start, self.end)
		return {"labels": [m[2] for m in marks], "opened": self._series(self.lcs, "date_of_issue", "value"),
			"drawn": self._series(self.invoices, "posting_date", "base_grand_total")}

	def _series(self, rows, date_field, value_field):
		marks = periods.buckets(self.start, self.end)
		return [sum(flt(r.get(value_field)) for r in rows if self._in_period(r.get(date_field), lo, hi)) for lo, hi, __ in marks]

	def _status_mix(self, cohort):
		mix = {}
		for lc in cohort:
			row = mix.setdefault(lc.status, {"status": lc.status, "count": 0, "amount": 0})
			row["count"] += 1
			row["amount"] += lc.value
		return sorted(mix.values(), key=lambda r: -r["amount"])

	def _top_applicants(self, cohort):
		top = {}
		for lc in cohort:
			row = top.setdefault(lc.applicant, {"applicant": lc.applicant, "count": 0, "amount": 0})
			row["count"] += 1
			row["amount"] += lc.value
		rows = sorted(top.values(), key=lambda r: -r["amount"])[:5]
		total = sum(lc.value for lc in cohort)
		for r in rows:
			r["pct"] = _pct(r["amount"], total)
		return rows

	def _worklist(self, start, page_length):
		open_lcs = sorted((lc for lc in self.lcs if lc.is_live or lc.is_lapsed),
			key=lambda lc: (lc.days_to_expiry is None, lc.days_to_expiry or 0))
		rows = [{
			"name": lc.name, "lc_no": lc.lc_no, "applicant": lc.applicant, "status": lc.status,
			"expiry_date": lc.date_and_place_of_expiry, "days_to_expiry": lc.days_to_expiry,
			"currency": lc.currency, "lc_value": flt(lc.grand_total), "drawn_pct": _clamp(_pct(lc.drawn, lc.value), 0, 999),
			"undrawn": lc.undrawn, "lapsed": lc.is_lapsed,
		} for lc in open_lcs[start:start + page_length]]
		return {"rows": rows, "total": len(open_lcs), "start": start, "page_length": page_length,
			"amount": sum(lc.undrawn for lc in open_lcs)}
