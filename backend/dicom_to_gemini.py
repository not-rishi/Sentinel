import pydicom
import numpy as np
from PIL import Image
import google.generativeai as genai
import io
import re

GEMINI_API_KEY = ""
MODEL_NAME = "gemini-2.5-flash" 

def dicom_to_png_bytes(dicom_path):
    try:
        ds = pydicom.dcmread(dicom_path)
        
        
        
        if ds.file_meta.TransferSyntaxUID.is_compressed:
            ds.decompress() 
        
        pixel_array = ds.pixel_array.astype(float)

        
        
        max_val = pixel_array.max()
        if max_val == 0:
            scaled = np.uint8(pixel_array)
        else:
            scaled = (np.maximum(pixel_array, 0) / max_val) * 255.0
            scaled = np.uint8(scaled)

        image = Image.fromarray(scaled)
        image = image.convert("RGB") 

        buf = io.BytesIO()
        image.save(buf, format="PNG")
        return buf.getvalue()
    except Exception as e:
        print(f"CRITICAL DICOM ERROR: {e}")
        raise



def analyze_image_with_gemini(image_bytes):
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(MODEL_NAME)

    prompt = """
You are acting as an AI assistant in a simulated medical image triage system.
Analyze this radiological scan. Briefly describe:
1. The anatomical region visible.
2. Any obvious visual anomalies or high-contrast areas.
3. A preliminary triage recommendation (Routine, Urgent, or Critical).
4. Try to do tumor or foreign object detection.

Keep the response concise (under 4 sentences).
Start with "AI FINDINGS: ".
End the response with priority number 0 for Routine 1 for Urgent and 2 for Critical
"""

    response = model.generate_content(
        [
            prompt,
            {
                "mime_type": "image/png",
                "data": image_bytes,
            },
        ]
    )

    return response.text.strip()





def analyze_dicom_to_dict(dicom_path):
    """
    Analyzes a DICOM file and returns a dictionary with the Gemini response and extracted priority.
    """
    image_bytes = dicom_to_png_bytes(dicom_path)
    response_text = analyze_image_with_gemini(image_bytes)
    
    
    priority = None
    clean_response = response_text
    
    if response_text:
        match = re.search(r'(\d+)\s*$', response_text)
        if match:
            priority = int(match.group(1))
            
            clean_response = re.sub(r'\s*\d+\s*$', '', response_text).strip()
    
    return {
        "response": clean_response,
        "priority": priority
    }





def analyze_dicom(dicom_path):
    
    image_bytes = dicom_to_png_bytes(dicom_path)
    return analyze_image_with_gemini(image_bytes)





if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python dicom_to_gemini.py <dicom_file>")
        exit(1)

    dicom_file = sys.argv[1]
    output = analyze_dicom_to_dict(dicom_file)

    print(f"Priority: {output['priority']}")
    print(f"Summary: {output['response']}")