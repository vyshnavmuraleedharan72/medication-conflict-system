# Medication Reconciliation System — FastAPI + MongoDB

## Overview

This project implements a simplified medication reconciliation backend similar to those used in healthcare systems. The system ingests medication lists from multiple sources, detects conflicts, maintains longitudinal history through versioned snapshots, and allows conflicts to be resolved with audit information.

The design preserves all historical data instead of overwriting previous records, reflecting real-world clinical systems where traceability is critical.

---

## Key Features

- Longitudinal medication snapshots per patient
- Versioned history of medication lists over time
- Support for multiple ingestion sources
- Conflict detection across snapshots
- Drug class conflict rules
- Tracking of active vs stopped medications
- Auditable conflict records
- Conflict resolution workflow
- Reporting of unresolved conflicts by clinic

---

## Technology Stack

- FastAPI for backend API
- MongoDB for data storage
- Pydantic for request validation
- Python 3.10+

---

## Data Model Overview

### Medication Snapshot Collection

Each ingestion creates a new snapshot document.

Fields include:

- `snapshot_id`: unique identifier for the snapshot  
- `patient_id`: patient identifier  
- `clinic_id`: clinic identifier  
- `source`: origin of the medication list (e.g., clinic EMR, hospital discharge)  
- `version`: sequential version number per patient  
- `normalized_medications`: cleaned medication list  
- `created_at`: timestamp of ingestion  

This structure enables longitudinal tracking without modifying prior records.

---

### Conflict Collection

Conflicts are stored separately for auditability.

Each conflict record contains:

- `conflict_id`: unique identifier  
- `snapshot_id`: snapshot where conflict was detected  
- `patient_id` and `clinic_id`  
- `source` that triggered detection  
- `type` of conflict  
- `details` describing the issue  
- `sources_involved`  
- `status`: unresolved or resolved  
- `detected_at` timestamp  
- `resolution_reason` (when resolved)  
- `resolved_by` (optional)  
- `resolved_at` timestamp  

---

## Conflict Detection Rules

The system currently detects:

1. Same drug with different doses across snapshots  
2. Active versus stopped status mismatch  
3. Drug class conflicts using predefined rules  

Example class conflicts:

- ACE inhibitor with ARB  
- Concurrent anticoagulants  

Drug class mappings and conflict rules are defined in code for simplicity.

---

## Conflict Resolution

Conflicts are not removed. Instead, they are marked as resolved with full audit metadata:

- Resolution reason  
- Resolver identity (optional)  
- Resolution timestamp  

This approach preserves history and supports traceability.

---

## API Endpoints

### Health Check

**GET /**

Returns a simple status message.

---

### Ingest Medication Data

**POST /ingest**

Creates a new medication snapshot and detects conflicts.

Request body includes:

- patient_id  
- clinic_id  
- source  
- medications list (name, dose, status)

Response includes snapshot ID, version number, and number of conflicts detected.

---

### Get Patient History

**GET /patient/{patient_id}/history**

Returns all snapshots for a patient ordered by version.

---

### Report Patients with Unresolved Conflicts

**GET /report/{clinic_id}**

Returns a list of patients in a clinic who currently have unresolved conflicts.

---

### Resolve Conflicts for a Patient

**POST /resolve/{patient_id}**

Marks all unresolved conflicts for the patient as resolved.

Request body:

- `resolution_reason` (required)  
- `resolved_by` (optional)  

---

## Running the Application Locally

### 1. Clone the repository

```bash
git clone <repository-url>
cd <repository-folder>
