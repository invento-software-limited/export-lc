from frappe import _


def get_data():
	return {
		"fieldname": "proforma_invoice",
		"non_standard_fieldnames": {"Sales Invoice": "export_proforma_invoice"},
		"transactions": [{"label": _("Sales"), "items": ["Export LC", "Sales Invoice"]}],
	}
