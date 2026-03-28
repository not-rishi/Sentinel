import os
import time
import random
import numpy as np
import pydicom
from pydicom.dataset import Dataset, FileDataset, FileMetaDataset
from pydicom.uid import generate_uid, ImplicitVRLittleEndian
from datetime import datetime
from pynetdicom import AE, StoragePresentationContexts

TARGET_IP = "127.0.0.1"
TARGET_PORT = 11112
SEND_INTERVAL_SECONDS = 10

FIRST_NAMES = ["John", "Jane", "Alex", "Sam", "Chris", "Pat", "Taylor", "Jordan"]
LAST_NAMES = ["Smith", "Doe", "Johnson", "Brown", "Davis", "Miller", "Wilson"]
STUDY_DESCS = [
    "CHEST XRAY ROUTINE", "CT HEAD STAT", "CT ABDOMEN W CONTRAST",
    "MRI BRAIN STROKE PROTOCOL", "XR EXTREMITY TRAUMA", "CT CHEST MVA",
    "US PELVIS ROUTINE", "CT NECK URGENT"
]

def generate_critical_metadata(study_desc):
    keywords = ["STAT", "URGENT", "TRAUMA", "MVA", "STROKE", "BLEED"]
    return {
        "priority": random.choice(["ROUTINE", "URGENT", "STAT", "CRITICAL"]),
        "suspected_condition": random.choice([
            "Normal", "Hemorrhage", "Fracture", "Tumor", "Stroke"
        ]),
        "alert_flag": random.choice([True, False]),
        "radiologist_note": random.choice([
            "No acute findings",
            "Follow-up required",
            "Immediate attention needed",
            "Possible abnormality detected"
        ]),
        "timestamp": datetime.now().isoformat(),
        "keyword_trigger": any(k in study_desc.upper() for k in keywords)
    }

def create_pixel_array(has_anomaly=False):
    img = np.random.randint(0, 50, (256, 256), dtype=np.uint8)
    if has_anomaly:
        x, y = random.randint(50, 200), random.randint(50, 200)
        img[x:x+20, y:y+20] = 255
    return img

def generate_random_dicom():
    """Generates a valid DICOM dataset entirely in memory."""

    patient_id = f"PT-{random.randint(1000, 9999)}"
    patient_name = f"{random.choice(LAST_NAMES)}^{random.choice(FIRST_NAMES)}"
    study_desc = random.choice(STUDY_DESCS)
    has_anomaly = random.choice([True, False, False]) 
    metadata = generate_critical_metadata(study_desc)

    file_meta = FileMetaDataset()
    file_meta.MediaStorageSOPClassUID = '1.2.840.10008.5.1.4.1.1.2'
    file_meta.MediaStorageSOPInstanceUID = generate_uid()
    file_meta.TransferSyntaxUID = ImplicitVRLittleEndian

    ds = FileDataset(None, {}, file_meta=file_meta, preamble=b"\0" * 128)
    
    ds.SOPClassUID = file_meta.MediaStorageSOPClassUID
    ds.SOPInstanceUID = file_meta.MediaStorageSOPInstanceUID
    ds.StudyInstanceUID = generate_uid() # Unique Study per scan
    ds.SeriesInstanceUID = generate_uid()
    
    ds.PatientID = patient_id
    ds.PatientName = patient_name
    ds.StudyDescription = study_desc
    ds.Modality = "CT"
    ds.ContentDate = datetime.now().strftime('%Y%m%d')
    ds.ContentTime = datetime.now().strftime('%H%M%S')

    pixel_array = create_pixel_array(has_anomaly)
    ds.Rows, ds.Columns = pixel_array.shape
    ds.PhotometricInterpretation = "MONOCHROME2"
    ds.SamplesPerPixel = 1
    ds.BitsStored = 8
    ds.BitsAllocated = 8
    ds.HighBit = 7
    ds.PixelRepresentation = 0
    ds.PixelData = pixel_array.tobytes()

    ds.add_new((0x0011, 0x1010), 'LO', metadata["priority"])
    ds.add_new((0x0011, 0x1011), 'LO', metadata["suspected_condition"])
    ds.add_new((0x0011, 0x1012), 'CS', str(metadata["alert_flag"]))
    ds.add_new((0x0011, 0x1013), 'LO', metadata["radiologist_note"])
    ds.add_new((0x0011, 0x1014), 'LO', metadata["timestamp"])
    ds.add_new((0x0011, 0x1015), 'CS', str(metadata["keyword_trigger"]))

    return ds, has_anomaly

def start_continuous_feed():
    ae = AE(ae_title=b'LIVE_SIMULATOR')
    ae.requested_contexts = StoragePresentationContexts

    print("🏥 Starting Sentinel Live Hospital Feed Simulator...")
    print(f"📡 Target: {TARGET_IP}:{TARGET_PORT}")
    print(f"⏱️  Interval: {SEND_INTERVAL_SECONDS} seconds")
    print("-" * 50)

    scan_count = 1

    try:
        while True:
            print(f"\n[Scan #{scan_count}] Generating scan...", end=" ")
            ds, has_anomaly = generate_random_dicom()
            print("Done.")
            
            print(f"   Patient: {ds.PatientID} | Desc: {ds.StudyDescription}")
            print(f"   Anomaly: {has_anomaly} | Connecting to PACS... ", end="")

            assoc = ae.associate(TARGET_IP, TARGET_PORT)
            
            if assoc.is_established:
                status = assoc.send_c_store(ds)
                if status and status.Status == 0x0000:
                    print("✅ DELIVERED")
                elif status and status.Status == 0xC000:
                    print("⚠️ DROPPED (Chaos Simulator)")
                else:
                    print(f"❌ FAILED (Status: {status.Status:04X if status else 'None'})")
                assoc.release()
            else:
                print("🚫 CONNECTION REJECTED (Is the server running?)")

            scan_count += 1
            time.sleep(SEND_INTERVAL_SECONDS)

    except KeyboardInterrupt:
        print("\n\n🛑 Live feed simulator stopped by user.")

if __name__ == "__main__":
    start_continuous_feed()