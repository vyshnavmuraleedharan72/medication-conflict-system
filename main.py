from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from pymongo import MongoClient
from datetime import datetime
import uuid

app = FastAPI()

# -----------------------
# MongoDB Connection
# -----------------------

client = MongoClient(
    "mongodb+srv://vyshnavmuraleedharan72_db_user:ia3KYuvWJhjHUeKK@cluster0.tykhwul.mongodb.net/med_db?retryWrites=true&w=majority"
)

db = client["med_db"]

med_collection = db["medication_snapshots"]
conflict_collection = db["conflicts"]

# -----------------------
# Drug Class Rules
# -----------------------

drug_classes = {
    "lisinopril": "ace_inhibitor",
    "losartan": "arb",
    "warfarin": "anticoagulant",
    "apixaban": "anticoagulant"
}

class_conflicts = {
    ("ace_inhibitor", "arb"),
    ("anticoagulant", "anticoagulant")
}

# -----------------------
# Data Models
# -----------------------

class Medication(BaseModel):
    name: str
    dose: str | None = None
    status: str = "active"


class IngestRequest(BaseModel):
    patient_id: str
    clinic_id: str
    source: str
    medications: List[Medication]


# ⭐ NEW: Resolution model (REQUIRED)
class ResolveRequest(BaseModel):
    resolution_reason: str
    resolved_by: str | None = "system"

# -----------------------
# Helper Functions
# -----------------------

def normalize_medication(med: Medication) -> dict:

    name = med.name.lower().strip()

    dose = None
    unit = None

    if med.dose:
        parts = med.dose.lower().split()
        if len(parts) == 2:
            try:
                dose = round(float(parts[0]), 1)
                unit = parts[1]
            except ValueError:
                pass

    return {
        "name": name,
        "dose": dose,
        "unit": unit,
        "status": med.status.lower()
    }


def detect_conflicts(existing_meds, new_meds, source):

    conflicts = []

    med_map = {}
    for med in existing_meds:
        med_map.setdefault(med["name"], []).append(med)

    # -------- Dose & Status Conflicts --------
    for med in new_meds:
        name = med["name"]

        if name in med_map:
            for old in med_map[name]:

                if (
                    med["dose"] is not None
                    and old["dose"] is not None
                    and med["dose"] != old["dose"]
                ):
                    conflicts.append({
                        "type": "dose_mismatch",
                        "drug": name,
                        "old_dose": old["dose"],
                        "new_dose": med["dose"],
                        "sources_involved": [source]
                    })

                if med["status"] != old.get("status", "active"):
                    conflicts.append({
                        "type": "status_conflict",
                        "drug": name,
                        "old_status": old.get("status", "active"),
                        "new_status": med["status"],
                        "sources_involved": [source]
                    })

    # -------- Drug Class Conflicts --------
    all_meds = existing_meds + new_meds

    for i in range(len(all_meds)):
        for j in range(i + 1, len(all_meds)):
            m1 = all_meds[i]["name"]
            m2 = all_meds[j]["name"]

            c1 = drug_classes.get(m1)
            c2 = drug_classes.get(m2)

            if c1 and c2:
                if (c1, c2) in class_conflicts or (c2, c1) in class_conflicts:
                    conflicts.append({
                        "type": "drug_class_conflict",
                        "drug_1": m1,
                        "drug_2": m2,
                        "class_1": c1,
                        "class_2": c2,
                        "sources_involved": [source]
                    })

    return conflicts

# -----------------------
# Routes
# -----------------------

@app.get("/")
def health_check():
    return {"message": "API is working"}

# -----------------------
# INGEST → CREATE SNAPSHOT
# -----------------------

@app.post("/ingest")
def ingest_data(data: IngestRequest):

    try:
        snapshot_id = str(uuid.uuid4())

        existing_docs = list(
            med_collection.find({"patient_id": data.patient_id})
        )

        version = len(existing_docs) + 1

        normalized_meds = [
            normalize_medication(med)
            for med in data.medications
        ]

        existing_meds = []
        for doc in existing_docs:
            existing_meds.extend(doc.get("normalized_medications", []))

        conflicts = detect_conflicts(
            existing_meds,
            normalized_meds,
            data.source
        )

        # -------- Save Snapshot --------
        snapshot_doc = {
            "snapshot_id": snapshot_id,
            "patient_id": data.patient_id,
            "clinic_id": data.clinic_id,
            "source": data.source,
            "version": version,
            "normalized_medications": normalized_meds,
            "created_at": datetime.utcnow()
        }

        med_collection.insert_one(snapshot_doc)

        # -------- Save Conflicts --------
        for c in conflicts:
            conflict_collection.insert_one({
                "conflict_id": str(uuid.uuid4()),
                "snapshot_id": snapshot_id,
                "patient_id": data.patient_id,
                "clinic_id": data.clinic_id,
                "source": data.source,
                "type": c["type"],
                "details": c,
                "sources_involved": c.get("sources_involved", []),
                "status": "unresolved",
                "detected_at": datetime.utcnow()
            })

        return {
            "message": "Snapshot created successfully",
            "snapshot_id": snapshot_id,
            "version": version,
            "conflicts_detected": len(conflicts)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# -----------------------
# PATIENT HISTORY
# -----------------------

@app.get("/patient/{patient_id}/history")
def get_patient_history(patient_id: str):

    try:
        results = []
        for doc in med_collection.find({"patient_id": patient_id}).sort("version"):
            doc["_id"] = str(doc["_id"])
            results.append(doc)
        return results

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# -----------------------
# REPORT → Unresolved conflicts
# -----------------------

@app.get("/report/{clinic_id}")
def get_unresolved(clinic_id: str):

    try:
        results = conflict_collection.find({
            "clinic_id": clinic_id,
            "status": "unresolved"
        })

        patients = list({r["patient_id"] for r in results})

        return {
            "clinic_id": clinic_id,
            "patients_with_unresolved_conflicts": patients
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# -----------------------
# ⭐ RESOLVE CONFLICTS (AUDITABLE)
# -----------------------

@app.post("/resolve/{patient_id}")
def resolve_conflicts(patient_id: str, data: ResolveRequest):

    try:
        result = conflict_collection.update_many(
            {
                "patient_id": patient_id,
                "status": "unresolved"
            },
            {
                "$set": {
                    "status": "resolved",
                    "resolution_reason": data.resolution_reason,
                    "resolved_by": data.resolved_by,
                    "resolved_at": datetime.utcnow()
                }
            }
        )

        return {
            "message": "Conflicts resolved successfully",
            "updated_count": result.modified_count
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# -----------------------
# DEBUG
# -----------------------

@app.get("/debug")
def debug():
    return {"message": "debug working"}