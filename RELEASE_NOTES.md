# Release Notes - version 1.0.1 (2026-07-19)

This maintenance release (v1.0.1) implements automated CI workflow configurations for code quality tracking on branch pushes, defines bench package dependencies, and updates documentation features.

## Improvements in v1.0.1

### 🛠️ CI Workflow Configurations
- **Branch Triggers**: Configured the linters pipeline to trigger on direct pushes to the `develop` and `version-16` branches.
- **Workflow Skip Conditions**: Removed the strict pull request filter from the main linter job to allow status reporting for branch commits.

### 📦 Bench Compatibility & Dependencies
- **Frappe Dependencies**: Added the mandatory `[tool.bench.frappe-dependencies]` settings to declare compatibility with Frappe/ERPNext version-16.

### 📄 Documentation Updates
- **Key Features Alignments**: Rephrased the features section to highlight Sales Order and Commercial Invoice features.
- **Feature Cleanup**: Removed outdated references to in-words currency conversion.

---

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
