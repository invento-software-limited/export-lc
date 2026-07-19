# Product Overview

**Export LC** is a specialized Letter of Credit (LC) management application designed specifically for **Frappe** and **ERPNext (version-16)**, developed by **Invento Software Limited**.

The application streamlines the tracking of export contracts, associated bank requirements, and Export Letters of Credit, ensuring full compliance and eliminating manual tracking overhead. It integrates directly with standard ERPNext sales processes.

---

## SWIFT MT700 Alignment

The custom doctypes are designed to map directly to standard SWIFT MT700 (Letter of Credit) message fields:
* **F40A (Form of Documentary Credit)**: Irrevocable, Revocable, Transferable, etc.
* **F31C (Date of Issue)**: Date the LC was issued by the buyer's bank.
* **F31D (Date and Place of Expiry)**: Expiry timeline and country of presentation.
* **F50 (Applicant)**: The buyer/customer opening the credit line.
* **F59 (Beneficiary)**: The seller/exporter receiving the credit.
* **F45A (Description of Goods/Services)**: Item specifications and terms.
* **F46A (Documents Required)**: Required documents for negotiation (e.g., Bills of Lading, Certificate of Origin, Packing Lists).
* **F47A (Additional Conditions)**: Custom terms or restrictions set by the issuing bank.
* **F78 (Instructions to Bank)**: Special instructions to the paying/negotiating bank.

---

## Core DocTypes & Schema

### 1. Export Proforma Invoice (PI)
The primary document starting the export cycle, serving as the commercial contract.
* **DocType Name**: `Export Proforma Invoice`
* **Naming Series**: `EXP-PRO-INV-.####`
* **Key Fields**:
  - `pi_number` (Unique reference ID)
  - `sales_order` (Link to ERPNext `Sales Order`)
  - `bank`, `swift_code`, `account_number_iban`, `bank_address` (Seller's receiving bank credentials)
  - `buyer`, `buyer_name`, `buyer_address` (Customer information)
  - `incoterm`, `payment_terms`, `tolerance_percent` (Commercial agreements)
  - `port_of_loading`, `port_of_discharge`, `country_of_final_destination` (Logistics)

### 2. Export LC (Letter of Credit)
Records the official LC details received from the advising/issuing bank.
* **DocType Name**: `Export LC`
* **Naming Series**: `EXP-LC-.####`
* **Key Fields**:
  - `lc_no` (Letter of Credit number)
  - `proforma_invoice` (Link to `Export Proforma Invoice`)
  - `issuing_bank` & `beneficiary_bank` (Banks involved)
  - `latest_date_of_shipment`, `transshipment`, `partial_shipments` (Logistics parameters)
  - `percentage_credit_amount_tolerance` (Value tolerance)

---

## System Workflows & Automations

### 1. Validation Rules
- **One-to-One Validation**: The system enforces that only one active or submitted `Export LC` can exist per `Export Proforma Invoice` to prevent duplicate tracking or billing anomalies.

### 2. Automated Calculations
- **Currency & Conversion Rates**: The document totals are automatically converted to base (company) currency using the document-level `conversion_rate`.

### 3. Dynamic LC Status Tracking
The system dynamically updates the `status` of an `Export LC` record based on document life cycle and linked transactions:
* `Draft`: Document is still in draft state.
* `Active`: Document is submitted and open.
* `Expired`: Today's date has passed the defined `date_and_place_of_expiry`.
* `Partially Utilized`: Some linked commercial invoices have been billed but do not meet the grand total.
* `Fully Utilized`: The sum of linked submitted `Sales Invoice` (Commercial Invoice) totals meets or exceeds the LC value.
* `Cancelled`: The document has been cancelled.
