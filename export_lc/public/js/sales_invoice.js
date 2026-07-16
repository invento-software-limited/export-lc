frappe.ui.form.on("Sales Invoice", {
	refresh: function (frm) {
		frm.trigger("set_naming_series");
		frm.set_df_property("export_proforma_invoice", "read_only", 1);
	},
	export_lc: function (frm) {
		if (frm.doc.export_lc) {
			frappe.db.get_value("Export LC", frm.doc.export_lc, "proforma_invoice", function (r) {
				frm.set_value("export_proforma_invoice", r ? r.proforma_invoice : "");
			});
		} else {
			frm.set_value("export_proforma_invoice", "");
		}
	},
	export_proforma_invoice: function (frm) {
		if (frm.doc.export_proforma_invoice) {
			frappe.db.get_value(
				"Export Proforma Invoice",
				frm.doc.export_proforma_invoice,
				["pi_number", "pi_date"],
				function (r) {
					if (r) {
						frm.set_value("pi_number", r.pi_number || "");
						frm.set_value("pi_date", r.pi_date || "");
					}
				}
			);
		} else {
			frm.set_value("pi_number", "");
			frm.set_value("pi_date", "");
		}
	},
	sales_type: function (frm) {
		frm.trigger("refresh");
		frm.trigger("set_naming_series");
	},
	set_naming_series: function (frm) {
		let options = "ACC-SINV-.YYYY.-\nACC-SINV-RET-.YYYY.-";
		if (frm.doc.sales_type === "Export") {
			options += "\nCOM-INV-.YYYY.-";
			if (!frm.doc.naming_series || !frm.doc.naming_series.startsWith("COM-INV-")) {
				frm.set_value("naming_series", "COM-INV-.YYYY.-");
			}
		} else {
			if (frm.doc.naming_series && frm.doc.naming_series.startsWith("COM-INV-")) {
				frm.set_value("naming_series", "ACC-SINV-.YYYY.-");
			}
		}
		frm.set_df_property("naming_series", "options", options);
	},
});
