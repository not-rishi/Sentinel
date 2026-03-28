import os
import time
import argparse
from pydicom import dcmread
from pynetdicom import AE, StoragePresentationContexts

def send_dicom_directory(directory_path, target_ip, target_port, max_retries, iterations):
    
    ae = AE(ae_title=b'TEST_MODALITY')
    ae.requested_contexts = StoragePresentationContexts

    
    if not os.path.exists(directory_path):
        print(f"❌ Error: Directory '{directory_path}' not found.")
        return

    files = [f for f in os.listdir(directory_path) if f.endswith('.dcm')]
    if not files:
        print(f"❌ No .dcm files found in '{directory_path}'!")
        return
        
    print(f"🚀 Starting DICOM Test Suite")
    print(f"➔ Target: {target_ip}:{target_port}")
    print(f"➔ Files: {len(files)} unique files")
    print(f"➔ Iterations: {iterations} (Total pushes: {len(files) * iterations})")
    print("-" * 50)

    
    stats = {
        "success": 0,
        "failed": 0,
        "chaos_drops": 0,
        "rejected": 0
    }
    
    start_time = time.time()

    
    for i in range(iterations):
        if iterations > 1:
            print(f"\n--- Iteration {i + 1} of {iterations} ---")
            
        for file_name in files:
            file_path = os.path.join(directory_path, file_name)
            success = False
            attempts = 0
            
            while not success and attempts <= max_retries:
                attempts += 1
                print(f"[{file_name}] Attempt {attempts}/{max_retries + 1}... ", end="", flush=True)
                
                
                assoc = ae.associate(target_ip, target_port)
                
                if assoc.is_established:
                    try:
                        dataset = dcmread(file_path)
                        status = assoc.send_c_store(dataset)
                        
                        if status:
                            if status.Status == 0x0000:
                                print("✅ SUCCESS")
                                stats["success"] += 1
                                success = True
                            elif status.Status == 0xC000:
                                print("⚠️ CHAOS DROP (0xC000). Retrying...")
                                stats["chaos_drops"] += 1
                                time.sleep(1)
                            else:
                                print(f"❌ FAILED (Status: {status.Status:04X})")
                                break 
                        else:
                            print("🔌 Connection lost mid-transfer. Retrying...")
                            time.sleep(1)
                    except Exception as e:
                        print(f"❌ ERROR reading/sending file: {e}")
                    finally:
                        assoc.release()
                else:
                    print("🚫 Association rejected. Server might be down or busy.")
                    stats["rejected"] += 1
                    time.sleep(2)
                    
            if not success:
                print(f"--> 💀 Gave up on {file_name} after {attempts} attempts.")
                stats["failed"] += 1

    
    elapsed = time.time() - start_time
    total_attempts = stats["success"] + stats["failed"]
    
    print("\n" + "=" * 50)
    print("📊 TEST SUITE SUMMARY")
    print("=" * 50)
    print(f"Time Elapsed:     {elapsed:.2f} seconds")
    print(f"Successful Pushes:{stats['success']}")
    print(f"Failed Pushes:    {stats['failed']}")
    print(f"Chaos Drops Hit:  {stats['chaos_drops']}")
    print(f"Assoc Rejections: {stats['rejected']}")
    
    if total_attempts > 0:
        success_rate = (stats["success"] / (stats["success"] + stats["failed"])) * 100
        print(f"Deliverability:   {success_rate:.2f}%")
    print("=" * 50)


if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description="DICOM Server Stress Tester")
    parser.add_argument("-d", "--dir", type=str, default="sample_data", help="Directory containing .dcm files")
    parser.add_argument("-i", "--ip", type=str, default="127.0.0.1", help="Target Server IP")
    parser.add_argument("-p", "--port", type=int, default=11112, help="Target Server Port")
    parser.add_argument("-r", "--retries", type=int, default=3, help="Max retries per file")
    parser.add_argument("-n", "--iterations", type=int, default=1, help="Number of times to loop through the directory")
    
    args = parser.parse_args()
    
    send_dicom_directory(
        directory_path=args.dir, 
        target_ip=args.ip, 
        target_port=args.port, 
        max_retries=args.retries,
        iterations=args.iterations
    )