frappe.ui.form.on("Sales Order", {
	refresh: function (frm) {
		if (frm.doc.docstatus === 1 && frm.doc.sales_type === "Export") {
			frm.add_custom_button(
				__("Export Proforma Invoice"),
				function () {
					frappe.model.open_mapped_doc({
						method: "export_lc.export_lc.doctype.export_proforma_invoice.export_proforma_invoice.make_export_proforma_invoice",
						frm: frm,
					});
				},
				__("Create")
			);
		}

		if (frm.doc.sales_type === "Export") {
			if (!frm.doc.buyer && frm.doc.customer) {
				frm.set_value("buyer", frm.doc.customer);
			}
		}

		if (frm.doc.buyer) {
			frm.set_query("buyer_address", function () {
				return {
					query: "frappe.contacts.doctype.address.address.address_query",
					filters: { link_doctype: "Customer", link_name: frm.doc.buyer },
				};
			});

			frm.set_query("buyer_contact", function () {
				return {
					query: "frappe.contacts.doctype.contact.contact.contact_query",
					filters: { link_doctype: "Customer", link_name: frm.doc.buyer },
				};
			});
		}
	},

	sales_type: function (frm) {
		if (frm.doc.sales_type === "Export") {
			if (!frm.doc.buyer && frm.doc.customer) {
				frm.set_value("buyer", frm.doc.customer);
			}
		}
	},

	customer: function (frm) {
		if (frm.doc.sales_type === "Export") {
			frm.set_value("buyer", frm.doc.customer);
		}
	},

	buyer: function (frm) {
		if (!frm.doc.buyer) {
			frm.set_value("buyer_name", "");
			frm.set_value("buyer_address", "");
			frm.set_value("buyer_contact", "");
			frm.set_value("buyer_phone_no", "");
			frm.set_value("buyer_email", "");
			frm.set_value("buyer_full_address", "");
			return;
		}

		frappe.db.get_value("Customer", frm.doc.buyer, "customer_name", function (r) {
			if (r && r.customer_name) {
				frm.set_value("buyer_name", r.customer_name);
			}
		});

		// Set filters
		frm.set_query("buyer_address", function () {
			return {
				query: "frappe.contacts.doctype.address.address.address_query",
				filters: { link_doctype: "Customer", link_name: frm.doc.buyer },
			};
		});

		frm.set_query("buyer_contact", function () {
			return {
				query: "frappe.contacts.doctype.contact.contact.contact_query",
				filters: { link_doctype: "Customer", link_name: frm.doc.buyer },
			};
		});

		// Auto-fetch address
		frappe.call({
			method: "frappe.client.get_list",
			args: {
				doctype: "Address",
				filters: [
					["Dynamic Link", "link_doctype", "=", "Customer"],
					["Dynamic Link", "link_name", "=", frm.doc.buyer],
					["disabled", "=", 0],
				],
				fields: ["name"],
				limit: 2,
			},
			callback: function (r) {
				if (r.message && r.message.length === 1) {
					frm.set_value("buyer_address", r.message[0].name);
				}
			},
		});

		// Auto-fetch contact
		frappe.call({
			method: "frappe.client.get_list",
			args: {
				doctype: "Contact",
				filters: [
					["Dynamic Link", "link_doctype", "=", "Customer"],
					["Dynamic Link", "link_name", "=", frm.doc.buyer],
				],
				fields: ["name"],
				limit: 2,
			},
			callback: function (r) {
				if (r.message && r.message.length === 1) {
					frm.set_value("buyer_contact", r.message[0].name);
				}
			},
		});
	},

	buyer_address: function (frm) {
		if (frm.doc.buyer_address) {
			frappe.call({
				method: "frappe.contacts.doctype.address.address.get_address_display",
				args: { address_dict: frm.doc.buyer_address },
				callback: function (r) {
					if (r.message) {
						frm.set_value("buyer_full_address", r.message);
					}
				},
			});
		} else {
			frm.set_value("buyer_full_address", "");
		}
	},

	buyer_contact: function (frm) {
		if (frm.doc.buyer_contact) {
			frappe.db.get_value(
				"Contact",
				frm.doc.buyer_contact,
				["phone", "email_id"],
				function (r) {
					if (r) {
						frm.set_value("buyer_phone_no", r.phone || "");
						frm.set_value("buyer_email", r.email_id || "");
					}
				}
			);
		} else {
			frm.set_value("buyer_phone_no", "");
			frm.set_value("buyer_email", "");
		}
	},
});
