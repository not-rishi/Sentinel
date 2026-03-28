import os
import numpy as np
import pydicom
from pydicom.dataset import FileDataset, FileMetaDataset
from pydicom.uid import UID, generate_uid
import datetime

def create_dicom(filepath, patient_id, description, has_pixel_anomaly=False):
    """Generates a valid synthetic DICOM file from scratch."""
    
    
    file_meta = FileMetaDataset()
    file_meta.MediaStorageSOPClassUID = '1.2.840.10008.5.1.4.1.1.2' 
    file_meta.MediaStorageSOPInstanceUID = generate_uid()
    file_meta.TransferSyntaxUID = pydicom.uid.ExplicitVRLittleEndian
    file_meta.ImplementationClassUID = generate_uid()

    
    ds = FileDataset(filepath, {}, file_meta=file_meta, preamble=b"\0" * 128)
    
    
    dt = datetime.datetime.now()
    ds.PatientName = f"TEST^{patient_id}"
    ds.PatientID = patient_id
    ds.StudyInstanceUID = generate_uid()
    ds.SeriesInstanceUID = generate_uid()
    ds.SOPInstanceUID = file_meta.MediaStorageSOPInstanceUID
    ds.SOPClassUID = file_meta.MediaStorageSOPClassUID
    ds.StudyDescription = description
    ds.Modality = "CT"
    ds.StudyDate = dt.strftime('%Y%m%d')
    ds.StudyTime = dt.strftime('%H%M%S')

    
    
    pixels = np.full((256, 256), 100, dtype=np.uint16)
    
    
    noise = np.random.normal(0, 10, (256, 256)).astype(np.uint16)
    pixels = np.clip(pixels + noise, 0, 4095)

    if has_pixel_anomaly:
        
        y, x = np.ogrid[-128:128, -128:128]
        mask = x**2 + y**2 <= 30**2 
        pixels[mask] = 4000 

    
    ds.SamplesPerPixel = 1
    ds.PhotometricInterpretation = "MONOCHROME2"
    ds.PixelRepresentation = 0
    ds.HighBit = 11
    ds.BitsStored = 12
    ds.BitsAllocated = 16
    ds.Columns = 256
    ds.Rows = 256
    
    
    ds.PixelData = pixels.tobytes()

    
    ds.is_little_endian = True
    ds.is_implicit_VR = False
    ds.save_as(filepath)
    print(f"Generated: {filepath} | Desc: {description} | Anomaly: {has_pixel_anomaly}")

if __name__ == "__main__":
    
    os.makedirs("sample_data", exist_ok=True)
    print("Generating synthetic DICOM files...\n")

    
    create_dicom("sample_data/01_routine.dcm", "PT-001", "CHEST XRAY ROUTINE", has_pixel_anomaly=False)

    
    create_dicom("sample_data/02_urgent_meta.dcm", "PT-002", "CT HEAD STAT", has_pixel_anomaly=False)

    
    create_dicom("sample_data/03_urgent_pixel.dcm", "PT-003", "CT HEAD ROUTINE", has_pixel_anomaly=True)

    
    create_dicom("sample_data/04_critical.dcm", "PT-004", "CT HEAD TRAUMA MVA", has_pixel_anomaly=True)
    
    print("\nDone! 4 test files are ready in test_client/sample_data/")