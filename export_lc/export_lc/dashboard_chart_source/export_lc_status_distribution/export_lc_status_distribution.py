# Copyright (c) 2026, Invento Software Limited and Contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import today


@frappe.whitelist()
def get(
	chart_name: str | None = None,
	chart: str | None = None,
	no_cache: int | None = None,
	filters: str | None = None,
	from_date: str | None = None,
	to_date: str | None = None,
	timespan: str | None = None,
	time_interval: str | None = None,
	heatmap_year: int | None = None,
):
	# Query all draft and active/utilized/expired/closed Export LCs
	lcs = frappe.get_all("Export LC", filters={"docstatus": ["<", 2]}, fields=["status"])

	status_counts = {
		_("Draft"): 0,
		_("Active"): 0,
		_("Partially Utilized"): 0,
		_("Fully Utilized"): 0,
		_("Expired"): 0,
		_("Closed"): 0,
	}

	for lc in lcs:
		status = lc.get("status") or "Draft"
		if status in status_counts:
			status_counts[status] += 1
		else:
			status_counts[_("Draft")] += 1

	labels = list(status_counts.keys())
	values = list(status_counts.values())

	return {
		"labels": labels,
		"datasets": [{"name": _("LC Count"), "values": values}],
	}
