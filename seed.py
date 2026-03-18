from pymongo import MongoClient
from datetime import datetime
import uuid
import random

client = MongoClient(
    "mongodb+srv://vyshnavmuraleedharan72_db_user:ia3KYuvWJhjHUeKK@cluster0.tykhwul.mongodb.net/med_db?retryWrites=true&w=majority"
)

db = client["med_db"]

med_collection = db["medication_snapshots"]
conflict_collection = db["conflicts"]

med_collection.delete_many({})
conflict_collection.delete_many({})

print("Old data cleared")

drug_pool = [
    ("lisinopril", "mg"),
    ("losartan", "mg"),
    ("warfarin", "mg"),
    ("apixaban", "mg")
]

clinics = ["C001", "C002", "C003"]

for i in range(1, 16):  # 15 patients

    patient_id = f"P{i:03d}"
    clinic_id = random.choice(clinics)

    prev_meds = []

    for version in range(1, 3):  # 2 snapshots each

        snapshot_id = str(uuid.uuid4())

        meds = []

        for drug, unit in random.sample(drug_pool, 2):

            dose = random.choice([5, 10, 20])
            status = random.choice(["active", "stopped"])

            med = {
                "name": drug,
                "dose": dose,
                "unit": unit,
                "status": status
            }

            meds.append(med)

        snapshot_doc = {
            "snapshot_id": snapshot_id,
            "patient_id": patient_id,
            "clinic_id": clinic_id,
            "source": "synthetic_source",
            "version": version,
            "normalized_medications": meds,
            "created_at": datetime.utcnow()
        }

        med_collection.insert_one(snapshot_doc)

        # Create conflicts if version > 1
        if version > 1:
            for new_med, old_med in zip(meds, prev_meds):

                if new_med["dose"] != old_med["dose"]:
                    conflict_collection.insert_one({
                        "conflict_id": str(uuid.uuid4()),
                        "snapshot_id": snapshot_id,
                        "patient_id": patient_id,
                        "clinic_id": clinic_id,
                        "type": "dose_mismatch",
                        "status": "unresolved",
                        "detected_at": datetime.utcnow()
                    })

        prev_meds = meds

print("Synthetic dataset inserted successfully")