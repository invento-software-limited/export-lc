app_name = "export_lc"
app_title = "Export LC"
app_publisher = "Invento Software Limited"
app_description = "An Export LC Management app developed by Invento Software Limited"
app_email = "help@invento.com.bd"
app_license = "mit"

app_logo_url = "/assets/export_lc/images/export_lc_logo.svg"
app_home = "/app/export-lc-workspace"

fixtures = [
	{"dt": "Role", "filters": [["name", "in", ["Export LC User", "Export LC Manager"]]]},
	{"dt": "Custom DocPerm", "filters": [["role", "in", ["Export LC User", "Export LC Manager"]]]},
	{"dt": "Role Profile", "filters": [["name", "in", ["Export LC Manager"]]]},
]

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
add_to_apps_screen = [
	{
		"name": "export_lc",
		"logo": "/assets/export_lc/images/export_lc_logo.svg",
		"title": "Export LC",
		"route": "/app/export-lc-workspace",
	}
]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/export_lc/css/export_lc.css"
# app_include_js = "/assets/export_lc/js/export_lc.js"

# include js, css files in header of web template
# web_include_css = "/assets/export_lc/css/export_lc.css"
# web_include_js = "/assets/export_lc/js/export_lc.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "export_lc/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

doctype_js = {"Sales Order": "public/js/sales_order.js", "Sales Invoice": "public/js/sales_invoice.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "export_lc/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# automatically load and sync documents of this doctype from downstream apps
# importable_doctypes = [doctype_1]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "export_lc.utils.jinja_methods",
# 	"filters": "export_lc.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "export_lc.install.before_install"
# after_install = "export_lc.install.after_install"
after_migrate = "export_lc.setup_permissions.run"

# Uninstallation
# ------------

# before_uninstall = "export_lc.uninstall.before_uninstall"
# after_uninstall = "export_lc.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "export_lc.utils.before_app_install"
# after_app_install = "export_lc.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "export_lc.utils.before_app_uninstall"
# after_app_uninstall = "export_lc.utils.after_app_uninstall"

# Build
# ------------------
# To hook into the build process

# after_build = "export_lc.build.after_build"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "export_lc.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"Sales Invoice": {
		"on_submit": "export_lc.export_lc.doctype.export_lc.export_lc.update_lc_status_on_invoice_event",
		"on_cancel": "export_lc.export_lc.doctype.export_lc.export_lc.update_lc_status_on_invoice_event",
	}
}

# Scheduled Tasks
# ---------------

scheduler_events = {"daily": ["export_lc.export_lc.doctype.export_lc.export_lc.update_expired_lcs"]}

# Testing
# -------

# before_tests = "export_lc.install.before_tests"

# Extend DocType Class
# ------------------------------
#
# Specify custom mixins to extend the standard doctype controller.
# extend_doctype_class = {
# 	"Task": "export_lc.custom.task.CustomTaskMixin"
# }

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "export_lc.event.get_events"
# }
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
override_doctype_dashboards = {"Sales Invoice": "export_lc.custom_dashboard.get_sales_invoice_dashboard_data"}
# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["export_lc.utils.before_request"]
# after_request = ["export_lc.utils.after_request"]

# Job Events
# ----------
# before_job = ["export_lc.utils.before_job"]
# after_job = ["export_lc.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"export_lc.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []
