frappe.provide("frappe.dashboards.chart_sources");

frappe.dashboards.chart_sources["Export LC Status Distribution"] = {
	method: "export_lc.export_lc.dashboard_chart_source.export_lc_status_distribution.export_lc_status_distribution.get",
	filters: [],
};
