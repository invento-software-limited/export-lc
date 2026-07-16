import frappe


def get_sales_invoice_dashboard_data(data):
	if not data:
		data = frappe._dict()

	if "internal_links" not in data:
		data["internal_links"] = {}

	# Map local fields on Sales Invoice to the respective parent doctypes
	data["internal_links"]["Export LC"] = "export_lc"
	data["internal_links"]["Export Proforma Invoice"] = "export_proforma_invoice"

	if "transactions" not in data:
		data["transactions"] = []

	# Find the existing "Reference" group and append our export documents
	found = False
	for group in data["transactions"]:
		if group.get("label") == "Reference":
			if "Export LC" not in group["items"]:
				group["items"].append("Export LC")
			if "Export Proforma Invoice" not in group["items"]:
				group["items"].append("Export Proforma Invoice")
			found = True
			break

	if not found:
		data["transactions"].append({"label": "Export", "items": ["Export LC", "Export Proforma Invoice"]})

	return data
