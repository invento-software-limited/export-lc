from frappe import _


def get_data():
	return {
		"fieldname": "export_lc",
		"non_standard_fieldnames": {
			"Sales Invoice": "export_lc",
			"Delivery Note": "export_lc",
			"LC Shipment": "export_lc",
		},
		"transactions": [
			{
				"label": "",
				"items": [
					"Sales Invoice",
				],
			},
			{"label": "", "items": ["Delivery Note"]},
		],
	}
