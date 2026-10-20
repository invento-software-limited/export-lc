// Dashboard tab on the Export LC form: renders the skeleton into a shadow root,
// fetches one payload from export_lc.api.export_lc_dashboard and binds it.
frappe.provide("export_lc.dashboard");

(() => {
	const ns = export_lc.dashboard;
	const fmt = ns.format;
	const charts = ns.charts;
	const METHOD = "export_lc.api.export_lc_dashboard.get_dashboard_data";
	const STATUS_COLORS = {
		Overdue: "#7e2a30", Unpaid: "#3b4757", "Partly Paid": "#7a4f12", Paid: "#0a5a3c",
		"To Bill": "#8a4527", Completed: "#0a5a3c", Draft: "#3b4757", Return: "#7e2a30",
		"Credit Note Issued": "#7e2a30", "Return Issued": "#7e2a30", Closed: "#3b4757",
	};

	frappe.ui.form.on("Export LC", {
		refresh(frm) {
			if (frm.is_new() || !frm.get_field("dashboard_html")) return;
			ns.render(frm);
		},
	});

	ns.render = (frm) => {
		const wrapper = frm.get_field("dashboard_html").$wrapper[0];
		if (!wrapper) return;
		const root = mount(wrapper);
		frm.__elc_dashboard_for = frm.doc.name;
		const seq = (frm.__elc_dashboard_seq = (frm.__elc_dashboard_seq || 0) + 1);
		frappe
			.call({ method: METHOD, args: { name: frm.doc.name } })
			.then((r) => seq === frm.__elc_dashboard_seq && r.message && bind(root, r.message))
			.catch(() => {
				root.querySelector(".cd").innerHTML = `<div class="err">${__("Could not load the LC dashboard.")}</div>`;
			});
	};

	function mount(wrapper) {
		wrapper.innerHTML = "";
		const host = document.createElement("div");
		host.className = "export-lc-dashboard";
		wrapper.appendChild(host);
		const root = host.attachShadow({ mode: "open" });
		root.innerHTML = `<style>${ns.CSS}</style>${ns.HTML}`;
		return root;
	}


	function bind(root, d) {
		fmt.use_currency(d.currency, d.currency_symbol, d.currency_symbol_on_right);
		const $ = (field) => root.querySelector(`[data-field="${field}"]`);
		const text = (field, value) => $(field) && ($(field).textContent = value);
		const slot = (name, html) => (root.querySelector(`[data-slot="${name}"]`).innerHTML = html);
		bind_header(d, $, text);
		bind_metrics(d, $, text, slot);
		bind_stages(d, $, text);
		bind_window(d, text, slot);
		bind_goods(d, text, slot);
		bind_documents(d, text, slot);
		bind_drills(root, d);
	}

	function bind_header(d, $, text) {
		text("asof", __("Position as of {0}", [fmt.date(d.today)]));
		const base = d.company_currency !== d.currency ? ` · ${__("rate {0} {1}", [d.conversion_rate, d.company_currency])}` : "";
		text("ccy_note", __("Amounts in {0}", [d.currency]) + base);
		text("lc_no", d.lc_no || d.name);
		const meta = [d.lc_no ? d.name : null, d.applicant, d.drafts_at].filter(Boolean).map(fmt.esc);
		meta.push(`<b>${fmt.esc(__(d.status || ""))}</b>`);
		$("meta").innerHTML = meta.join(" &nbsp;·&nbsp; ");
		text("lc_value", fmt.compact(d.lc_value));
		const expired = d.days_to_expiry != null && d.days_to_expiry < 0;
		text("expiry_label", expired ? __("Expired") : __("Expires"));
		text("expiry_value", fmt.date(d.expiry_date));
	}

	function bind_metrics(d, $, text, slot) {
		fmt.set_compact($("invoiced_amount"), d.invoiced_amount);
		pill($("invoiced_pct"), fmt.pct(d.invoiced_pct, 0),
			d.invoiced_pct > 100 ? "#8a4527" : d.invoiced_pct >= 100 ? "#0a5a3c" : d.invoiced_pct > 0 ? "#17505d" : "#3b4757");
		text("invoiced_caption", __("{0} invoice(s)", [d.invoiced_count]));
		slot("invoiced_trend", charts.step_sparkline(d.invoiced_trend, d.today, "#097C52"));

		fmt.set_compact($("available_amount"), d.over_drawn_amount > 0 ? -d.over_drawn_amount : d.available_amount);
		text("available_caption", d.over_drawn_amount > 0
			? __("over-drawn beyond LC value")
			: __("max {0} at ±{1}%", [fmt.compact(d.max_drawable), d.tolerance_pct]));
		slot("available_split", charts.segmented([
			{ label: __("Drawn"), value: Math.min(d.invoiced_amount, d.max_drawable), color: "#097C52" },
			{ label: __("Available"), value: d.available_amount, color: "#2f5a86" },
			{ label: __("Tolerance"), value: d.max_drawable - Math.max(d.lc_value, d.invoiced_amount), color: "#c5ccd4" },
		]));

		fmt.set_compact($("realized_amount"), d.realized_amount);
		pill($("realized_pct"), fmt.pct(d.realized_pct, 0), d.realized_pct >= 100 ? "#0a5a3c" : d.realized_pct > 0 ? "#7a4f12" : "#3b4757");
		slot("realized_gauge", charts.gauge(d.realized_pct, "#8a5a16",
			[__("{0} open", [fmt.compact(d.outstanding_amount)]), __("{0} late", [fmt.compact(d.overdue_amount)])],
			null, __("Realised {0} of {1} drawn", [fmt.compact(d.realized_amount), fmt.compact(d.invoiced_amount)])));

		bind_validity(d, $, text, slot);
	}

	function bind_validity(d, $, text, slot) {
		const el = $("validity_value");
		if (d.days_to_expiry == null) {
			el.textContent = "—";
			return;
		}
		const left = d.days_to_expiry;
		el.textContent = String(Math.abs(left));
		el.insertAdjacentHTML("beforeend", `<span>${fmt.esc(Math.abs(left) === 1 ? __("day") : __("days"))}</span>`);
		const [label, color] = left < 0 ? [__("expired"), "#7e2a30"] : left <= 15 ? [__("expiring"), "#7a4f12"] : [__("open"), "#17505d"];
		pill($("validity_pill"), label, color);
		text("validity_caption", d.latest_date_of_shipment ? __("ship by {0}", [fmt.date(d.latest_date_of_shipment, false)]) : "");
		slot("validity_gauge", charts.gauge(d.validity_elapsed_pct, left < 0 ? "#a3302f" : "#17626e",
			[fmt.date(d.date_of_issue, false), fmt.date(d.expiry_date, false)], d.shipment_mark_pct,
			__("Marker: latest date of shipment {0}", [fmt.date(d.latest_date_of_shipment)])));
	}

	function bind_stages(d, $, text) {
		text("stage_opened", fmt.compact(d.lc_value));
		text("stage_opened_s", __("{0} · {1} line(s)", [fmt.date(d.date_of_issue), d.items.length]));
		text("stage_delivered", fmt.compact(d.delivered_amount));
		text("stage_delivered_s", __("{0} of LC · {1} note(s)", [fmt.pct(d.delivered_pct, 0), d.delivered_count]));
		text("stage_invoiced", fmt.compact(d.invoiced_amount));
		text("stage_invoiced_s", __("{0} of LC · {1} invoice(s)", [fmt.pct(d.invoiced_pct, 0), d.invoiced_count]));
		text("stage_realized", fmt.compact(d.realized_amount));
		text("stage_realized_s", __("{0} outstanding", [fmt.compact(d.outstanding_amount)]));
	}

	function bind_window(d, text, slot) {
		text("window_caption", d.validity_days != null ? __("{0}-day credit · issue to expiry", [d.validity_days]) : "");
		slot("timeline", charts.timeline(d));
		text("terms_caption", d.applicable_rules || "");
		const route = [d.port_of_loading, d.port_of_discharge || d.final_destination].filter(Boolean).join(" → ");
		const rows = [
			[__("Form of credit"), d.form_of_documentary_credit],
			[__("Drafts at"), d.drafts_at],
			[__("Amount tolerance"), d.tolerance_pct ? `±${d.tolerance_pct}%` : null],
			[__("Partial shipments"), d.partial_shipments],
			[__("Transshipment"), d.transshipment],
			[__("Confirmation"), d.confirmation_instructions],
			[__("Incoterm"), d.incoterm],
			[__("Issuing bank"), d.issuing_bank],
			[__("Beneficiary bank"), d.beneficiary_bank],
			[__("Route"), route ? `${route}${d.mode_of_transport ? ` · ${d.mode_of_transport}` : ""}` : null],
		].filter(([, v]) => v);
		slot("terms", rows.map(([k, v]) => `<tr><td>${fmt.esc(k)}</td><td class="n">${fmt.esc(v)}</td></tr>`).join(""));
	}

	function bind_goods(d, text, slot) {
		text("goods_caption", __("Invoiced quantity against LC quantity, per line"));
		if (!d.items.length) return slot("goods", `<div class="empty">${__("No goods lines on this LC.")}</div>`);
		slot("goods", d.items.map((it) => {
			const color = it.invoiced_pct > 100 ? "#a3552f" : it.invoiced_pct >= 100 ? "#097C52" : it.invoiced_pct > 0 ? "#17626e" : "#98a1ac";
			const tip = __("Delivered {0} · Invoiced {1} · LC {2} {3}", [fmt.qty(it.delivered_qty), fmt.qty(it.invoiced_qty), fmt.qty(it.lc_qty), it.uom || ""]);
			return `<div title="${fmt.esc(tip)}">
				<div class="rk-r"><span class="rk-d" style="background:${color}"></span>
				<span class="rk-n">${fmt.esc(it.item_name)}</span>
				<span class="rk-v">${fmt.qty(it.invoiced_qty)} / ${fmt.qty(it.lc_qty)} ${fmt.esc(it.uom || "")}<em> · ${fmt.esc(fmt.compact(it.lc_amount))}</em></span></div>
				<div class="rk-t"><div class="rk-f" style="width:${Math.max(Math.min(it.invoiced_pct, 100), it.invoiced_pct > 0 ? 2 : 0)}%;background:${color}"></div></div>
			</div>`;
		}).join(""));
	}

	function bind_documents(d, text, slot) {
		const hidden = Object.keys(d.can_read).filter((dt) => !d.can_read[dt]);
		const note = hidden.length ? ` · ${__("no access to {0}", [hidden.join(", ")])}` : "";
		text("docs_caption", __("{0} document(s) · {1} outstanding", [d.documents.length, fmt.compact(d.outstanding_amount)]) + note);
		if (!d.documents.length) {
			return slot("documents", `<tr><td colspan="6" class="empty">${__("No invoices or delivery notes raised against this LC yet.")}</td></tr>`);
		}
		slot("documents", d.documents.map((doc) => `<tr>
			<td class="doc"><a class="lk" data-doctype="${fmt.esc(doc.doctype)}" data-name="${fmt.esc(doc.name)}">${fmt.esc(doc.name)}</a></td>
			<td>${fmt.esc(__(doc.doctype))}</td>
			<td>${fmt.esc(fmt.date(doc.posting_date))}</td>
			<td><span class="pill" style="background:${STATUS_COLORS[doc.status] || "#3b4757"}">${fmt.esc(__(doc.status))}</span></td>
			<td class="n">${fmt.esc(fmt.full(doc.value))}</td>
			<td class="n">${doc.progress_pct == null ? "—" : fmt.esc(`${fmt.pct(doc.progress_pct, 0)} ${doc.progress_label}`)}</td>
		</tr>`).join(""));
	}

	function bind_drills(root, d) {
		const lists = {
			invoiced: ["Sales Invoice", { export_lc: d.name, docstatus: 1 }],
			delivered: ["Delivery Note", { export_lc: d.name, docstatus: 1 }],
			outstanding: ["Sales Invoice", { export_lc: d.name, docstatus: 1, outstanding_amount: [">", 0] }],
		};
		root.querySelectorAll("[data-drill]").forEach((el) => {
			const [doctype, filters] = lists[el.dataset.drill];
			if (!d.can_read[doctype]) return el.classList.remove("lk");
			el.title = __("Open {0} list", [__(doctype)]);
			el.onclick = () => frappe.set_route("List", doctype, filters);
		});
		root.querySelectorAll("a[data-doctype]").forEach((a) => {
			a.onclick = () => frappe.set_route("Form", a.dataset.doctype, a.dataset.name);
		});
	}

	function pill(el, label, color) {
		if (!el) return;
		el.textContent = label;
		el.style.background = color;
	}
})();
