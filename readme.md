SENTINEL | Automated Medical Imaging Triage Framework
SENTINEL is a simulated medical imaging triage system designed to automate the prioritization of radiological scans using both metadata analysis and Generative AI. It mimics a real-world PACS (Picture Archiving and Communication System) environment by accepting DICOM files, anonymizing patient data, and flagging critical cases for immediate review.

🚀 System Architecture
The project is divided into three core components:

1. Backend (FastAPI & DICOM Server)
FastAPI Web Server: Handles authentication, image rendering, audit logging, and WebSocket communication for real-time dashboard updates.

DICOM SCP (Service Class Provider): A background server running on port 11112 that accepts incoming C-STORE requests using pynetdicom.

Triage Engine: A rule-based processing unit that anonymizes DICOM datasets and assigns urgency levels (Routine, Urgent, Critical) based on metadata keywords (e.g., "TRAUMA", "STROKE") and pixel intensity anomalies.

AI Integration: Utilizes the Gemini API to analyze DICOM pixel data for visual anomalies and tumor/foreign object detection.

2. Frontend (Modern Web Interface)
Triage Control Dashboard: A real-time interface built with HTML/CSS and Vanilla JS that displays the current study queue and system metrics.

Real-time Updates: Uses WebSockets to stream metrics (uptime, deliverability) and new study arrivals directly to the UI.

DICOM Viewer: A dedicated viewer for authorized personnel to render and inspect radiological images as PNGs.

3. Simulation Tools
Live Hospital Feed Simulator: A Python script (live_feed.py) that generates synthetic DICOM data with randomized metadata and pixel anomalies, then streams them to the Sentinel server at set intervals.

🛠 Tech Stack
Backend: Python, FastAPI, Pydicom, Pynetdicom, NumPy, Pillow.

AI: Google Generative AI (Gemini 1.5 Flash).

Frontend: HTML5, CSS3, JavaScript, WebSockets, Three.js/Vanta.js (for aesthetics).

📂 Core Files
backend/main.py: Main entry point for the FastAPI server and DICOM SCP.

backend/triage_engine.py: Logic for anonymization and rule-based triage.

backend/dicom_to_gemini.py: Pipeline for converting DICOM to image bytes and querying Gemini.

frontend/index.html: The main dashboard layout.

test_client/live_feed.py: Simulator for generating and sending DICOM traffic.

🔒 Security & Privacy
Anonymization: Every incoming DICOM file is stripped of identifying information (Name, ID, BirthDate) and assigned a unique anonymous UID before storage.

Audit Logging: Every sensitive action—including logins, logouts, and image rendering—is logged to a secure terminal audit trail.

Access Control: The system uses a predefined set of Valid Access IDs (e.g., R-001 for Dr. Rishi) to authorize API requests and image access.

⚙️ Setup & Installation
Install Dependencies:

Bash
pip install -r backend/requirements.txt
Configure API Key:
Update the api_key in backend/main.py and backend/dicom_to_gemini.py with your Gemini API Key.

Run the Backend:

Bash
uvicorn main:app --reload
Start the Simulator:

Bash
python test_client/live_feed.py
Access the Dashboard:
Open frontend/login.html in your browser and log in with a valid ID (e.g., R-001).
