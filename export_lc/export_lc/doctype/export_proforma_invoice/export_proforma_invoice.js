frappe.ui.form.on("Export Proforma Invoice", {
	refresh: function (frm) {
		if (frm.doc.company_address && !frm.doc.address_display) {
			frm.trigger("company_address");
		}

		// Apply queries based on current Company
		if (frm.doc.company) {
			frm.set_query("company_address", function () {
				return {
					query: "frappe.contacts.doctype.address.address.address_query",
					filters: { link_doctype: "Company", link_name: frm.doc.company },
				};
			});
		}

		// Buyer (Customer): auto-populate address display and apply query filters
		if (frm.doc.buyer_address && !frm.doc.buyer_address_display) {
			frm.trigger("buyer_address");
		}
		toggle_base_currency_fields(frm);

		if (frm.doc.buyer) {
			frm.set_query("buyer_address", function () {
				return {
					query: "frappe.contacts.doctype.address.address.address_query",
					filters: { link_doctype: "Customer", link_name: frm.doc.buyer },
				};
			});
		}

		if (frm.doc.docstatus === 1) {
			// Create Export LC button
			frm.add_custom_button(
				__("Export LC"),
				function () {
					frappe.model.open_mapped_doc({
						method: "export_lc.export_lc.doctype.export_proforma_invoice.export_proforma_invoice.make_export_lc",
						frm: frm,
					});
				},
				__("Create")
			);

			// Create Sales Invoice button
			frm.add_custom_button(
				__("Sales Invoice"),
				function () {
					frappe.model.open_mapped_doc({
						method: "export_lc.export_lc.doctype.export_proforma_invoice.export_proforma_invoice.make_sales_invoice",
						frm: frm,
					});
				},
				__("Create")
			);
		}
	},

	company: function (frm) {
		// Clear dependent fields when company changes
		frm.set_value("company_address", "");
		frm.set_value("address_display", "");

		if (!frm.doc.company) return;

		// Set filter on company_address
		frm.set_query("company_address", function () {
			return {
				query: "frappe.contacts.doctype.address.address.address_query",
				filters: {
					link_doctype: "Company",
					link_name: frm.doc.company,
				},
			};
		});

		// Auto-fetch address if exactly one exists for this company
		frappe.call({
			method: "frappe.client.get_list",
			args: {
				doctype: "Address",
				filters: [
					["Dynamic Link", "link_doctype", "=", "Company"],
					["Dynamic Link", "link_name", "=", frm.doc.company],
					["disabled", "=", 0],
				],
				fields: ["name"],
				limit: 2,
			},
			callback: function (r) {
				if (r.message && r.message.length === 1) {
					frm.set_value("company_address", r.message[0].name);
				}
			},
		});
	},

	company_address: function (frm) {
		if (frm.doc.company_address) {
			frappe.call({
				method: "frappe.contacts.doctype.address.address.get_address_display",
				args: { address_dict: frm.doc.company_address },
				callback: function (r) {
					if (r.message) {
						let address = r.message.replace(/<br\s*\/?>/gi, "\n");
						frm.set_value("address_display", address);
					}
				},
			});
		} else {
			frm.set_value("address_display", "");
		}
	},

	buyer: function (frm) {
		// Clear dependent fields when buyer changes
		frm.set_value("buyer_address", "");
		frm.set_value("buyer_address_display", "");

		if (!frm.doc.buyer) return;

		// Set filter on buyer_address
		frm.set_query("buyer_address", function () {
			return {
				query: "frappe.contacts.doctype.address.address.address_query",
				filters: { link_doctype: "Customer", link_name: frm.doc.buyer },
			};
		});

		// Fetch name directly from Customer
		frappe.call({
			method: "frappe.client.get_value",
			args: {
				doctype: "Customer",
				filters: { name: frm.doc.buyer },
				fieldname: ["customer_name"],
			},
			callback: function (r) {
				if (r.message) {
					frm.set_value("buyer_name", r.message.customer_name || "");
				}
			},
		});

		// Auto-fetch address if exactly one exists for this buyer
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
	},

	buyer_address: function (frm) {
		if (frm.doc.buyer_address) {
			frappe.call({
				method: "frappe.contacts.doctype.address.address.get_address_display",
				args: { address_dict: frm.doc.buyer_address },
				callback: function (r) {
					if (r.message) {
						let address = r.message.replace(/<br\s*\/?>/gi, "\n");
						frm.set_value("buyer_address_display", address);
					}
				},
			});
		} else {
			frm.set_value("buyer_address_display", "");
		}
	},

	tc_name: function (frm) {
		if (frm.doc.tc_name) {
			frappe.call({
				method: "frappe.client.get_value",
				args: {
					doctype: "Terms and Conditions",
					filters: { name: frm.doc.tc_name },
					fieldname: "terms",
				},
				callback: function (r) {
					if (r.message) {
						frm.set_value("terms", r.message.terms);
					}
				},
			});
		} else {
			frm.set_value("terms", "");
		}
	},

	freight_charges: function (frm) {
		calculate_totals(frm);
	},

	currency: function (frm) {
		if (frm.doc.currency && frm.doc.company) {
			frappe.db.get_value("Company", frm.doc.company, "default_currency", function (r) {
				if (r && r.default_currency) {
					if (frm.doc.currency === r.default_currency) {
						frm.set_value("conversion_rate", 1.0);
					} else {
						frappe.call({
							method: "erpnext.setup.utils.get_exchange_rate",
							args: {
								transaction_date: frm.doc.pi_date || frappe.datetime.get_today(),
								from_currency: frm.doc.currency,
								to_currency: r.default_currency,
							},
							callback: function (r2) {
								frm.set_value("conversion_rate", flt(r2.message));
							},
						});
					}
				}
			});
		}
		toggle_base_currency_fields(frm);
	},

	conversion_rate: function (frm) {
		if (frm.doc.items && frm.doc.items.length > 0) {
			frm.doc.items.forEach((item) => {
				var base_rate = flt(item.rate) * flt(frm.doc.conversion_rate || 1);
				var base_amount = flt(item.total) * flt(frm.doc.conversion_rate || 1);
				frappe.model.set_value(item.doctype, item.name, "base_rate", base_rate);
				frappe.model.set_value(item.doctype, item.name, "base_total", base_amount);
			});
		}
		calculate_totals(frm);
	},

	sales_order: function (frm) {
		if (frm.doc.sales_order) {
			frappe.call({
				method: "export_lc.export_lc.doctype.export_proforma_invoice.export_proforma_invoice.make_export_proforma_invoice",
				args: {
					source_name: frm.doc.sales_order,
				},
				callback: function (r) {
					if (r.message) {
						let doc = r.message;

						// Map main fields safely
						Object.keys(doc).forEach((key) => {
							if (
								key !== "name" &&
								key !== "doctype" &&
								key !== "items" &&
								!key.startsWith("_")
							) {
								if (doc[key]) {
									if (frm.fields_dict[key]) {
										frm.set_value(key, doc[key]);
									}
								}
							}
						});

						// Map items
						if (doc.items && doc.items.length > 0) {
							frm.clear_table("items");
							doc.items.forEach((item) => {
								let row = frm.add_child("items");
								Object.keys(item).forEach((key) => {
									if (
										key !== "name" &&
										key !== "doctype" &&
										key !== "parent" &&
										key !== "parentfield" &&
										key !== "parenttype" &&
										!key.startsWith("_")
									) {
										if (item[key] !== undefined && item[key] !== null) {
											row[key] = item[key];
										}
									}
								});
							});
							frm.refresh_field("items");
						}

						calculate_totals(frm);

						// Cascade data
						if (frm.doc.buyer) {
							frm.trigger("buyer");
						}
						if (frm.doc.company) {
							frm.trigger("company");
						}

						frappe.show_alert({
							message: __("Data fetched from Sales Order"),
							indicator: "green",
						});
					}
				},
			});
		}
	},
});

frappe.ui.form.on("Export Proforma Invoice Item", {
	qty: function (frm, cdt, cdn) {
		calculate_item_amount(frm, cdt, cdn);
	},
	rate: function (frm, cdt, cdn) {
		calculate_item_amount(frm, cdt, cdn);
	},
	items_remove: function (frm) {
		calculate_totals(frm);
	},
});

var calculate_item_amount = function (frm, cdt, cdn) {
	var row = locals[cdt][cdn];
	var total = flt(row.qty) * flt(row.rate);
	var base_rate = flt(row.rate) * flt(frm.doc.conversion_rate || 1);
	var base_total = total * flt(frm.doc.conversion_rate || 1);

	frappe.model.set_value(cdt, cdn, "total", total);
	frappe.model.set_value(cdt, cdn, "base_rate", base_rate);
	frappe.model.set_value(cdt, cdn, "base_total", base_total);

	// Assuming Total Amount (USD) is same as total for now
	frappe.model.set_value(cdt, cdn, "total_amount_usd", total);
	calculate_totals(frm);
};

var calculate_totals = function (frm) {
	var total = 0;
	var base_total = 0;

	(frm.doc.items || []).forEach(function (item) {
		total += flt(item.total);
		base_total += flt(item.base_total);
	});
	frm.set_value("total", total);
	frm.set_value("base_total", base_total);

	var conversion_rate = flt(frm.doc.conversion_rate) || 1;

	var grand_total = total;
	var base_grand_total = grand_total * conversion_rate;

	frm.set_value("grand_total", grand_total);
	frm.set_value("rounded_total", Math.round(grand_total));

	frm.set_value("base_grand_total", base_grand_total);
	frm.set_value("base_rounded_total", Math.round(base_grand_total));
};

var toggle_base_currency_fields = function (frm) {
	if (frm.doc.company && frm.doc.currency) {
		frappe.db.get_value("Company", frm.doc.company, "default_currency", function (r) {
			let hide_base = false;
			if (r && r.default_currency && frm.doc.currency === r.default_currency) {
				hide_base = true;
			}
			frm.toggle_display(
				[
					"conversion_rate",
					"base_total",
					"base_grand_total",
					"base_rounded_total",
					"base_in_words",
				],
				!hide_base
			);
			if (frm.fields_dict.items && frm.fields_dict.items.grid) {
				frm.fields_dict.items.grid.toggle_display("base_rate", !hide_base);
				frm.fields_dict.items.grid.toggle_display("base_total", !hide_base);
			}
		});
	}
};
