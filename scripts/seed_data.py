from pymongo import MongoClient
from datetime import datetime
import uuid
import random

client = MongoClient("mongodb://localhost:27017/")
db = client["med_db"]

med_collection = db["medication_snapshots"]
conflict_collection = db["conflicts"]

patients = [f"P{str(i).zfill(3)}" for i in range(1, 16)]
clinics = ["C001", "C002"]

medications = ["lisinopril", "losartan", "warfarin", "apixaban"]

for p in patients:
    for v in range(1, 3):
        snapshot_id = str(uuid.uuid4())

        meds = [
            {
                "name": random.choice(medications),
                "dose": random.choice([5, 10, 20]),
                "unit": "mg",
                "status": random.choice(["active", "stopped"])
            }
            for _ in range(2)
        ]

        med_collection.insert_one({
            "snapshot_id": snapshot_id,
            "patient_id": p,
            "clinic_id": random.choice(clinics),
            "source": "synthetic",
            "version": v,
            "normalized_medications": meds,
            "created_at": datetime.utcnow()
        })

print("Seed data inserted successfully.")
