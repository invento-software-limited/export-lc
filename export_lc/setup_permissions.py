import frappe


def run():
	try:
		from frappe.model.document import unlock_document

		unlock_document("Role Profile", "Export LC Manager")
	except Exception:
		pass

	# 1. Add Custom DocPerm for Payment Entry to Export LC User (if not exists)
	doctypes_to_grant = [
		"Sales Order",
		"Sales Invoice",
		"Export Proforma Invoice",
		"Export LC",
		"Journal Entry",
		"Delivery Note",
		"Payment Entry",
	]

	for dt in doctypes_to_grant:
		# Ensure Export LC User has full permission
		if not frappe.db.exists("Custom DocPerm", {"parent": dt, "role": "Export LC User"}):
			doc = frappe.new_doc("Custom DocPerm")
			doc.parent = dt
			doc.parenttype = "DocType"
			doc.parentfield = "permissions"
			doc.role = "Export LC User"
			doc.permlevel = 0
			doc.read = 1
			doc.write = 1
			doc.create = 1
			doc.delete = 1
			doc.submit = 1
			doc.cancel = 1
			doc.amend = 1
			doc.insert()
			print(f"Added Export LC User perm for {dt}")
		else:
			# update to make sure they have all permissions
			doc = frappe.get_doc("Custom DocPerm", {"parent": dt, "role": "Export LC User"})
			doc.read = doc.write = doc.create = doc.delete = doc.submit = doc.cancel = doc.amend = 1
			doc.save()
			print(f"Updated Export LC User perm for {dt}")

		# Ensure Export LC Manager has full permission
		if not frappe.db.exists("Custom DocPerm", {"parent": dt, "role": "Export LC Manager"}):
			doc = frappe.new_doc("Custom DocPerm")
			doc.parent = dt
			doc.parenttype = "DocType"
			doc.parentfield = "permissions"
			doc.role = "Export LC Manager"
			doc.permlevel = 0
			doc.read = 1
			doc.write = 1
			doc.create = 1
			doc.delete = 1
			doc.submit = 1
			doc.cancel = 1
			doc.amend = 1
			doc.insert()
			print(f"Added Export LC Manager perm for {dt}")
		else:
			doc = frappe.get_doc("Custom DocPerm", {"parent": dt, "role": "Export LC Manager"})
			doc.read = doc.write = doc.create = doc.delete = doc.submit = doc.cancel = doc.amend = 1
			doc.save()
			print(f"Updated Export LC Manager perm for {dt}")

	# 2. Ensure Role Profile "Export LC Manager" exists and has roles
	role_profile_name = "Export LC Manager"
	roles_to_assign = [
		"Export LC Manager",
		"Export LC User",
		"Sales Manager",
		"Accounts Manager",
		"Stock Manager",
		"Desk User",
	]

	if not frappe.db.exists("Role Profile", role_profile_name):
		rp = frappe.new_doc("Role Profile")
		rp.role_profile = role_profile_name
		for role in roles_to_assign:
			rp.append("roles", {"role": role})
		rp.insert()
		print(f"Created Role Profile {role_profile_name}")
	else:
		rp = frappe.get_doc("Role Profile", role_profile_name)
		existing_roles = [r.role for r in rp.roles]
		modified_rp = False
		for role in roles_to_assign:
			if role not in existing_roles:
				rp.append("roles", {"role": role})
				modified_rp = True
		if modified_rp:
			rp.save()
			print(f"Updated Role Profile {role_profile_name}")

	# 3. Ensure "Export LC Workspace" has the correct roles, charts, and content assigned
	workspace_name = "Export LC Workspace"
	if frappe.db.exists("Workspace", workspace_name):
		import json
		import os

		doc = frappe.get_doc("Workspace", workspace_name)

		# Sync charts and content from JSON
		workspace_path = os.path.join(
			frappe.get_app_path("export_lc"),
			"export_lc",
			"workspace",
			"export_lc_workspace",
			"export_lc_workspace.json",
		)
		if os.path.exists(workspace_path):
			with open(workspace_path) as f:
				ws_data = json.load(f)
			doc.charts = []
			for c in ws_data.get("charts", []):
				doc.append("charts", {"chart_name": c["chart_name"], "label": c["label"]})
			doc.content = ws_data.get("content")

			# Sync number cards
			doc.number_cards = []
			for nc in ws_data.get("number_cards", []):
				doc.append("number_cards", {"number_card_name": nc["number_card_name"], "label": nc["label"]})

			# Sync shortcuts
			doc.shortcuts = []
			for s in ws_data.get("shortcuts", []):
				doc.append(
					"shortcuts",
					{
						"type": s.get("type"),
						"link_to": s.get("link_to"),
						"doc_view": s.get("doc_view"),
						"label": s.get("label"),
						"stats_filter": s.get("stats_filter"),
						"color": s.get("color"),
					},
				)

			# Sync links
			doc.links = []
			for l in ws_data.get("links", []):
				doc.append(
					"links",
					{
						"type": l.get("type"),
						"label": l.get("label"),
						"link_to": l.get("link_to"),
						"link_type": l.get("link_type"),
						"hidden": l.get("hidden"),
						"is_query_report": l.get("is_query_report"),
						"onboard": l.get("onboard"),
						"link_count": l.get("link_count"),
					},
				)

		roles_needed = ["Export LC User", "Export LC Manager", "System Manager"]
		existing_roles = [r.role for r in doc.roles]
		for role in roles_needed:
			if role not in existing_roles:
				doc.append("roles", {"role": role})
		doc.save(ignore_permissions=True)
		print(f"Updated roles, charts, and content for {workspace_name}")

	# 3.2. Ensure "Export LC Dashboard" exists and is standard
	dashboard_name = "Export LC Dashboard"
	if not frappe.db.exists("Dashboard", dashboard_name):
		dash = frappe.new_doc("Dashboard")
		dash.dashboard_name = dashboard_name
		dash.module = "Export LC"
		dash.is_standard = 1
		dash.is_default = 1
		dash.append("cards", {"card": "Total LC Exposure"})
		dash.append("cards", {"card": "Active LCs"})
		dash.append("cards", {"card": "Partially Utilized LCs"})
		dash.append("cards", {"card": "Fully Utilized LCs"})
		dash.append("cards", {"card": "Expired LCs"})
		dash.append("cards", {"card": "Closed LCs"})
		dash.append("charts", {"chart": "Export LC Status Distribution", "width": "Half"})
		dash.append("charts", {"chart": "Bank Risk Concentration", "width": "Half"})
		dash.append("charts", {"chart": "Export LC Chart", "width": "Full"})
		dash.insert(ignore_permissions=True)
		print(f"Created Dashboard {dashboard_name}")
	else:
		dash = frappe.get_doc("Dashboard", dashboard_name)
		dash.module = "Export LC"
		dash.is_standard = 1
		dash.is_default = 1
		dash.cards = []
		dash.append("cards", {"card": "Total LC Exposure"})
		dash.append("cards", {"card": "Active LCs"})
		dash.append("cards", {"card": "Partially Utilized LCs"})
		dash.append("cards", {"card": "Fully Utilized LCs"})
		dash.append("cards", {"card": "Expired LCs"})
		dash.append("cards", {"card": "Closed LCs"})
		dash.charts = []
		dash.append("charts", {"chart": "Export LC Status Distribution", "width": "Half"})
		dash.append("charts", {"chart": "Bank Risk Concentration", "width": "Half"})
		dash.append("charts", {"chart": "Export LC Chart", "width": "Full"})
		dash.save(ignore_permissions=True)
		print(f"Updated Dashboard {dashboard_name}")

	# 3.5. Ensure "Export LC" Workspace Sidebar is synced from JSON
	sidebar_name = "Export LC"
	if frappe.db.exists("Workspace Sidebar", sidebar_name):
		import json
		import os

		doc = frappe.get_doc("Workspace Sidebar", sidebar_name)
		sidebar_path = os.path.join(frappe.get_app_path("export_lc"), "workspace_sidebar", "export_lc.json")
		if os.path.exists(sidebar_path):
			with open(sidebar_path) as f:
				sidebar_data = json.load(f)
			doc.items = []
			for item in sidebar_data.get("items", []):
				doc.append(
					"items",
					{
						"child": item.get("child"),
						"collapsible": item.get("collapsible"),
						"filters": item.get("filters"),
						"icon": item.get("icon"),
						"indent": item.get("indent"),
						"keep_closed": item.get("keep_closed"),
						"label": item.get("label"),
						"link_to": item.get("link_to"),
						"link_type": item.get("link_type"),
						"show_arrow": item.get("show_arrow"),
						"type": item.get("type"),
					},
				)
			doc.save(ignore_permissions=True)
			print(f"Updated Workspace Sidebar for {sidebar_name}")

	# 4. Copy custom fields from Sales Order to Sales Invoice and Delivery Note
	import json
	import os

	from frappe.modules.utils import export_customizations

	# Cleanup old supplier-related custom fields to prevent database clutter
	old_supplier_fields = [
		"supplier_information",
		"supplier",
		"supplier_name",
		"supplier_contact",
		"supplier_phone_no",
		"supplier_email_",
		"supplier_address",
		"supplier_full_address",
		"column_break_y09zf",
	]
	for dt in ["Sales Order", "Sales Invoice", "Delivery Note"]:
		for fieldname in old_supplier_fields:
			frappe.db.delete("Custom Field", {"dt": dt, "fieldname": fieldname})
			frappe.db.delete("Property Setter", {"doc_type": dt, "field_name": fieldname})

	# Tag Sales Order custom fields and property setters with Export LC module
	frappe.db.sql("""
		UPDATE `tabCustom Field`
		SET module = 'Export LC'
		WHERE dt = 'Sales Order'
	""")
	frappe.db.sql("""
		UPDATE `tabProperty Setter`
		SET module = 'Export LC'
		WHERE doc_type = 'Sales Order'
	""")

	sales_order_custom_path = os.path.join(
		frappe.get_app_path("export_lc"), "export_lc", "custom", "sales_order.json"
	)
	if os.path.exists(sales_order_custom_path):
		with open(sales_order_custom_path) as f:
			so_data = json.loads(f.read())

		custom_fields = so_data.get("custom_fields", [])
		extra_fields = [
			{
				"fieldname": "export_proforma_invoice",
				"fieldtype": "Link",
				"label": "Export Proforma Invoice",
				"options": "Export Proforma Invoice",
				"insert_after": "export_lc",
				"no_copy": 1,
			},
			{
				"fieldname": "pi_number",
				"fieldtype": "Data",
				"label": "PI Number",
				"insert_after": "export_proforma_invoice",
				"read_only": 1,
			},
			{
				"fieldname": "pi_date",
				"fieldtype": "Date",
				"label": "PI Date",
				"insert_after": "pi_number",
				"read_only": 1,
			},
		]
		target_doctypes = ["Sales Invoice", "Delivery Note"]

		for target_dt in target_doctypes:
			all_fields = list(custom_fields) + extra_fields
			for cf in all_fields:
				fieldname = cf.get("fieldname")
				existing = frappe.db.exists("Custom Field", {"dt": target_dt, "fieldname": fieldname})

				new_cf = cf.copy()
				new_cf.pop("name", None)
				new_cf.pop("creation", None)
				new_cf.pop("modified", None)
				new_cf.pop("owner", None)
				new_cf.pop("modified_by", None)

				new_cf["dt"] = target_dt
				new_cf["module"] = "Export LC"

				# Adjust depends_on/mandatory_depends_on
				if new_cf.get("depends_on"):
					new_cf["depends_on"] = (
						new_cf["depends_on"]
						.replace('doc.order_type == "Sales"', "true")
						.replace("doc.order_type == 'Sales'", "true")
						.replace('doc.order_type == \\"Sales\\"', "true")
					)
				if new_cf.get("mandatory_depends_on"):
					new_cf["mandatory_depends_on"] = (
						new_cf["mandatory_depends_on"]
						.replace('doc.order_type == "Sales"', "true")
						.replace("doc.order_type == 'Sales'", "true")
						.replace('doc.order_type == \\"Sales\\"', "true")
					)

				# Adjust insert_after
				if new_cf["insert_after"] == "order_type":
					new_cf["insert_after"] = "naming_series"

				if existing:
					doc = frappe.get_doc("Custom Field", existing)
					doc.update(new_cf)
					doc.save(ignore_permissions=True)
				else:
					doc = frappe.new_doc("Custom Field")
					doc.update(new_cf)
					doc.insert(ignore_permissions=True)

			# Ensure property setters of Export LC fields and field_order are tagged with module='Export LC'
			frappe.db.sql("""
				UPDATE `tabProperty Setter`
				SET module = 'Export LC'
				WHERE doc_type = %s AND (
					field_name IN (
						SELECT fieldname FROM `tabCustom Field` WHERE dt = %s AND module = 'Export LC'
					) OR property = 'field_order'
				)
			""", (target_dt, target_dt))

			# Export customizations to JSON files in the app, filtering by module
			export_customizations(
				module="Export LC", doctype=target_dt, sync_on_migrate=True, with_permissions=True, apply_module_export_filter=True
			)
			print(f"Synced and exported custom fields for {target_dt}")

		# Also export Sales Order customizations with filter
		export_customizations(
			module="Export LC", doctype="Sales Order", sync_on_migrate=True, with_permissions=True, apply_module_export_filter=True
		)
		print("Synced and exported custom fields for Sales Order")

	# Programmatically delete removed custom fields from the database
	for dt, fieldname in [
		("Journal Entry", "export_lc"),
		("Journal Entry", "export_lc_amount"),
	]:
		if frappe.db.exists("Custom Field", {"dt": dt, "fieldname": fieldname}):
			frappe.db.delete("Custom Field", {"dt": dt, "fieldname": fieldname})
			frappe.db.delete("Property Setter", {"doc_type": dt, "field_name": fieldname})
			print(f"Deleted custom field {fieldname} from {dt}")

	frappe.db.commit()
