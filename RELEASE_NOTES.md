# Release Notes - version 1.0.0 (2026-07-16)

We are pleased to announce the release of **v1.0.0** of the `export_lc` app. This initial release introduces the core Export LC Management system for Frappe and ERPNext.

## Key Features in v1.0.0

### 📄 Export LC & Proforma Invoice Management
- **Export LC**: Standardized schema for tracking letters of credit (F50 Applicant, F59 Beneficiary, F20 LC Number, Bank Details, and Trade Information).
- **Export Proforma Invoice**: Cleaned schemas for tracking export proforma invoices mapped to Sales Orders.
- **Auto Mapping**: Fully automated document mapper workflows to generate Sales Orders, Sales Invoices, and Delivery Notes from Export LCs.

### 📈 Workspace & Dashboards
- **Export LC Workspace**: High-quality Workspace dashboard with KPI number cards (Total LC Exposure, Active LCs, Expired LCs, etc.).
- **Standalone Dashboard**: Interactive charts tracking LC status distribution and bank risk concentration.

### 🛡️ Permissions & Security
- **Role Profiles**: Predefined roles for `Export LC User` and `Export LC Manager`.
- **Permission Setup**: Automated script to grant full read/write/submit permissions to LC documents upon app installation.
