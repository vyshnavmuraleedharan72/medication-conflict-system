# MongoDB Schema Design

## Overview

The system uses two main collections:

1. medication_snapshots
2. conflicts

Snapshots store longitudinal medication data per patient.
Conflicts are stored separately for auditability and lifecycle tracking.

---

## Collection: medication_snapshots

Each document represents one ingestion event (snapshot).

### Fields

- snapshot_id: Unique identifier for the snapshot (UUID)
- patient_id: Identifier of the patient
- clinic_id: Identifier of the clinic
- source: Origin of the medication list
- version: Sequential version number per patient
- normalized_medications: List of normalized medication objects
- created_at: Timestamp of snapshot creation

### Example Document

{
  "snapshot_id": "uuid",
  "patient_id": "P001",
  "clinic_id": "C001",
  "source": "clinic_emr",
  "version": 3,
  "normalized_medications": [
    {
      "name": "lisinopril",
      "dose": 10,
      "unit": "mg",
      "status": "active"
    }
  ],
  "created_at": "timestamp"
}

---

## Collection: conflicts

Each document represents one detected conflict.

### Fields

- conflict_id: Unique identifier (UUID)
- snapshot_id: Snapshot where conflict was detected
- patient_id: Patient identifier
- clinic_id: Clinic identifier
- source: Source triggering the conflict
- type: Conflict type (dose_mismatch, status_conflict, drug_class_conflict)
- details: Conflict details object
- sources_involved: List of sources contributing to conflict
- status: unresolved or resolved
- detected_at: Timestamp of detection
- resolution_reason: Reason for resolution (if resolved)
- resolved_by: Person/system resolving conflict (optional)
- resolved_at: Resolution timestamp (if resolved)

---

## Design Decisions

- Snapshots are stored as separate documents to support versioning.
- Historical data is never overwritten.
- Conflicts are stored independently to allow lifecycle tracking.
- Denormalization is used for simpler queries.

---

## Indexing Rationale

Suggested indexes:

- patient_id on medication_snapshots for history queries
- clinic_id and status on conflicts for reporting
- snapshot_id on conflicts for traceability

These indexes optimize common operations such as retrieving patient history and generating clinic-level reports.
