import os
import time
from pydicom import dcmread
from pynetdicom import AE, StoragePresentationContexts

def send_dicom_directory(directory_path, target_ip="127.0.0.1", target_port=11112):
    ae = AE(ae_title=b'HOSP_MODALITY')
    ae.requested_contexts = StoragePresentationContexts

    if not os.path.exists(directory_path):
        print(f"Error: Directory '{directory_path}' not found.")
        return

    files = [f for f in os.listdir(directory_path) if f.endswith('.dcm')]
    if not files:
        print("No .dcm files found in sample_data folder!")
        return
        
    print(f"Starting transmission of {len(files)} files to {target_ip}:{target_port}...")

    for file_name in files:
        file_path = os.path.join(directory_path, file_name)
        success = False
        retries = 3
        
        while not success and retries > 0:
            print(f"Attempting to send {file_name}... ", end="", flush=True)
            
            assoc = ae.associate(target_ip, target_port)
            if assoc.is_established:
                dataset = dcmread(file_path)
                status = assoc.send_c_store(dataset)
                
                if status:
                    if status.Status == 0x0000:
                        print("SUCCESS")
                        success = True
                    elif status.Status == 0xC000:
                        print("FAILED (Chaos Simulator active). Retrying in 1s...")
                        retries -= 1
                        time.sleep(1)
                    else:
                        print(f"FAILED (DICOM Status: {status.Status:04X})")
                        break
                else:
                    print("Connection lost mid-transfer. Retrying...")
                    retries -= 1
                    time.sleep(1)
                    
                assoc.release()
            else:
                print("Association rejected. Backend might be down.")
                retries -= 1
                time.sleep(2)
                
        if not success:
            print(f"--> Giving up on {file_name} after multiple failures.")

if __name__ == "__main__":
    
    send_dicom_directory("sample_data")