import pydicom
import numpy as np
import uuid

def process_dicom_dataset(dataset: pydicom.Dataset) -> dict:
    """Anonymizes and runs POC Triage on a DICOM dataset."""
    
    
    dataset.PatientName = "ANONYMIZED^PATIENT"
    dataset.PatientID = f"ANON-{str(uuid.uuid4())[:8]}"
    if 'PatientBirthDate' in dataset:
        dataset.PatientBirthDate = ""
    
    
    flags = []
    priority_score = 0
    urgency_level = "ROUTINE"

    
    study_desc = dataset.get("StudyDescription", "").upper()
    if any(keyword in study_desc for keyword in ["TRAUMA", "STAT", "MVA", "STROKE"]):
        flags.append("METADATA_STAT")
        priority_score += 40

    
    if hasattr(dataset, 'pixel_array'):
        pixels = dataset.pixel_array
        
        max_val = np.max(pixels)
        if max_val > 0:
            high_intensity_ratio = np.sum(pixels > (max_val * 0.9)) / pixels.size
            if high_intensity_ratio > 0.05: 
                flags.append("PIXEL_ANOMALY")
                priority_score += 50

    if priority_score >= 80:
        urgency_level = "CRITICAL"
    elif priority_score >= 40:
        urgency_level = "URGENT"

    return {
        "urgency_level": urgency_level,
        "flags": flags,
        "priority_score": priority_score,
        "anonymized_ds": dataset
    }