# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2026-06-22

### Added
- Standard status field: Added a read-only Select field `status` on `Export LC` schema to track documentary credit lifecycle.
- 3 new number cards: Added Partially Utilized LCs, Fully Utilized LCs, and Closed LCs number cards.
- Standalone Dashboard: Programmed standard `Export LC Dashboard` record linking all number cards and charts.
- Event-driven automation: Hooked Sales Invoice events to update Export LC status automatically on submit or cancel.
- Scheduled task: Configured a daily background job to transition expired active LCs to "Expired".
- Custom Chart JS companion: Added companion JS for the custom chart source `Export LC Status Distribution` to register the Python query path with the frontend.

### Changed
- Workspace layout: Re-arranged the Export LC Workspace grid layout to display the 6 cards in a 2x3 block at the top.
- Refactored `export_lc_status_distribution.py` query logic to read directly from the new status field.

## [1.0.1] - 2026-06-22

### Added
- Link/connection dashboard updates: Integrated `Export LC` and `Export Proforma Invoice` references directly into the standard `Sales Invoice` dashboard connection panel.
- Added auto-assignment of series for Commercial Invoice.
- Added default `naming_series` logic dynamically for Commercial Invoices.

### Fixed
- **Accounting & Mapping**:
  - Fixed default `income_account` (along with standard accounting defaults and taxes) failing to fetch on Sales Invoices mapped from `Export LC` or `Export Proforma Invoice`.
  - Fixed an `AttributeError` on `country_of_origin` when creating a Delivery Note from `Export LC` items.
  - Updated field mapping, rate fetching, and document refresh on `Export LC Item`.
  - Fixed beneficiary field type mapping and default value logic.
  - Made `country_of_final_destination` empty by default.
  - Fixed auto-assignment of Export Proforma Invoice links.
- **UI & Formatting**:
  - Fixed Sales Invoice design break issue.
  - Fixed Sales Order UI formatting constraints.

## [1.0.0] - 2026-06-18

First stable release of the `export_lc` management application.

### Added
- Standardized Export LC workflow integrating:
  - `Sales Order`
  - `Export Proforma Invoice`
  - `Export LC`
  - `Sales Invoice` (Commercial Invoice)
  - `Delivery Note`
- Custom permissions and role profiles (`Export LC User`, `Export LC Manager`).
- Dedicated Export LC Workspace and workspace shortcuts.

### Changed
- Refactored `Export LC` dashboard to only display relevant Sales Invoice and Delivery Note transactions.
- Updated database sync logic in `setup_permissions.py` for clean installations.

### Removed
- Removed finance/expense and margin features to simplify workflow:
  - Removed `LC Margin` percent field from the `Export LC` DocType.
  - Removed `LC Margin`, `Difference Expense Booking`, and `Landed Cost Voucher` document creation flows and custom buttons.
  - Deleted custom fields `export_lc` and `export_lc_amount` from `Journal Entry`.
  - Deleted custom field `export_lc` from `Landed Cost Voucher`.
  - Deleted custom field `export_lc` from `LC Shipment`.
  - Deleted customization JSON files: `journal_entry.json`, `journal_entry_account.json`, `landed_cost_voucher.json`, and `lc_shipment.json`.

### Fixed
- Fixed `AttributeError: 'ExportProformaInvoice' object has no attribute 'invoice_date'` during Commercial Invoice generation by removing invalid field mappings.
