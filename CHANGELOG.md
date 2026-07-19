# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.1] - 2026-07-19

### Changed
- Configured the `Linters` workflow triggers to run on direct pushes to the `develop` and `version-16` branches.
- Updated key features lists across the README and product documentation to add Sales Order and Commercial Invoice features and remove the obsolete in-words conversion reference.
- Cleaned up python permissions source code formatting using Ruff.

## [1.0.0] - 2026-07-16

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
