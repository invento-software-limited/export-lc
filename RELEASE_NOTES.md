# Release Notes - version 1.1.0 (2026-06-22)

We are pleased to announce the release of **v1.1.0** of the `export_lc` app. This feature release introduces the standard lifecycle status field, automated event triggers, and a comprehensive analytics dashboard.

## What's New in v1.1.0

### 🔄 Lifecycle Status Field
- **Actual Status Field**: Added a read-only select field `status` directly to the `Export LC` schema.
- **Automated Event Hooks**: Registered document hooks in `hooks.py` to automatically update the `Export LC` status when associated Commercial Invoices (Sales Invoices) are submitted or cancelled.
- **Expiry Scheduler**: Configured a daily background scheduler task to identify and mark validity-expired LCs.

### 📈 Standalone Dashboard & KPI Cards
- **Standalone Dashboard**: Created the standard **Export LC Dashboard** document displaying 6 KPI Cards, 2 distribution/concentration charts (half-width), and a progress timeline chart (full-width).
- **6 KPI Number Cards**: Integrated 6 KPI number cards:
  - Total LC Exposure
  - Active LCs
  - Partially Utilized LCs
  - Fully Utilized LCs
  - Expired LCs
  - Closed LCs
- **Workspace Layout**: Refactored the **Export LC Workspace** to position the 6 KPI cards in two clean rows of 3 at the top.

### 🛠️ Custom Chart Fixes
- **JS Companion Config**: Added the frontend registration configuration file for the custom chart source `Export LC Status Distribution` to prevent desk rendering errors.
