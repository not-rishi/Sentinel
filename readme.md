<p align="center">
  <img src="frontend/assets/logo.png" alt="Sentinel Logo" width="200"/>
</p>

<h1 align="center">SENTINEL</h1>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue" />
  <img src="https://img.shields.io/badge/FastAPI-Backend-009688" />
  <img src="https://img.shields.io/badge/DICOM-PACS%20Simulation-success" />
  <img src="https://img.shields.io/badge/AI-Gemini-purple" />
  <img src="https://img.shields.io/badge/WebSockets-Real--Time-orange" />
  <img src="https://img.shields.io/badge/Medical-Imaging-critical" />
  <img src="https://img.shields.io/badge/Privacy-DICOM%20Anonymization-blueviolet" />
  <img src="https://img.shields.io/badge/Status-Actively%20Developed-success" />
</p>

<p align="center">
Sentinel is an automated medical imaging triage framework that simulates a modern PACS (Picture Archiving and Communication System) workflow. It accepts DICOM studies, anonymizes patient information, prioritizes cases based on metadata and AI-assisted image analysis, and delivers a real-time dashboard for radiological triage.
</p>

<table align="center">
  <tr>
    <td align="center" width="550">

<img src="frontend/assets/spectre-logo.png" width="300" alt="Spectre 2026">

**✧ Spectre 2026 Hackathon — 3rd Position**

<sub>Awarded for <b>SENTINEL</b>, an AI-powered Medical Imaging Triage Framework.</sub>

  </td>
  </tr>
</table>

---

# ▸ Repository Structure

```text
SENTINEL/
│
├── backend/
│   ├── dicom_to_gemini.py
│   ├── main.py
│   ├── requirements.txt
│   └── triage_engine.py
│
├── frontend/
│   ├── assets/
│   │   └── logo.png
│   ├── app.js
│   ├── index.html
│   ├── login.html
│   ├── style.css
│   ├── viewer-logic.js
│   └── viewer.html
│
├── test_client/
│   ├── sample_data/
│   │   ├── 01_routine.dcm
│   │   ├── 02_urgent_meta.dcm
│   │   ├── 03_urgent_pixel.dcm
│   │   ├── 04_critical.dcm
│   │   ├── angio.dcm
│   │   ├── brain.dcm
│   │   ├── head.dcm
│   │   └── smtg.dcm
│   ├── generate_dummies.py
│   ├── live_feed.py
│   ├── sender.py
│   └── test_dicom_server.py
│
└── README.md
```

---

# ▸ System Architecture

Sentinel is composed of three tightly integrated components that emulate a real-world hospital imaging workflow.

---

## ✦ Backend (FastAPI + DICOM Server)

The backend serves as the central processing engine responsible for receiving, analyzing and managing radiological studies.

### Features

- FastAPI REST server
- Built-in DICOM SCP using **pynetdicom**
- Accepts incoming C-STORE requests
- Automatic DICOM anonymization
- Metadata-driven triage engine
- AI-assisted image analysis using Gemini
- Audit logging
- Real-time WebSocket communication

### Responsibilities

- Authentication
- DICOM ingestion
- Patient data anonymization
- Urgency classification
- AI inference
- Dashboard updates
- Viewer authorization

---

## ✦ Frontend Dashboard

A lightweight web dashboard designed for radiologists and authorized personnel.

### Features

- Live triage queue
- Real-time study arrival updates
- Dashboard metrics
- DICOM image viewer
- Authentication portal
- Responsive interface

### Live Metrics

- System uptime
- Total studies received
- Delivery status
- Current processing queue
- Critical case count

---

## ✦ Simulation Tools

Sentinel includes utilities that simulate a live hospital imaging environment for testing and demonstrations.

### Features

- Synthetic DICOM generation
- Randomized metadata
- Pixel anomaly injection
- Continuous streaming
- PACS traffic simulation

---

# ▸ Automated Triage Pipeline

Every incoming study passes through the following workflow:

```
Incoming DICOM Study
        │
        ▼
 DICOM SCP Receiver
        │
        ▼
 Patient Data Anonymization
        │
        ▼
 Metadata Analysis
        │
        ▼
 Pixel Intensity Analysis
        │
        ▼
 Gemini AI Image Review
        │
        ▼
 Priority Assignment
        │
        ▼
 Dashboard Update
        │
        ▼
 Authorized Viewer Access
```

---

# ▸ Triage Levels

Sentinel classifies studies into three urgency categories.

| Level | Description |
|--------|-------------|
| 🟢 Routine | No abnormal findings detected. |
| 🟠 Urgent | Metadata or image anomalies require prompt review. |
| 🔴 Critical | High-priority cases such as trauma, stroke, tumors or significant anomalies requiring immediate attention. |

---

# ▸ AI Integration

Sentinel utilizes Google's **Gemini 1.5 Flash** model to assist with medical image analysis.

The AI pipeline performs:

- DICOM to image conversion
- Pixel interpretation
- Tumor indication detection
- Foreign object detection
- Visual anomaly analysis
- Additional confidence during triage

AI decisions complement the rule-based engine and are intended for simulation purposes only.

---

# ▸ Security & Privacy

Sentinel incorporates several security mechanisms to mimic real clinical environments.

### DICOM Anonymization

Every received study automatically removes identifying patient information including:

- Patient Name
- Patient ID
- Birth Date
- Other identifying metadata

Each study receives a unique anonymous identifier before storage.

### Audit Logging

The backend records important system events including:

- User login
- User logout
- Image rendering
- Viewer access
- Study processing
- AI analysis requests

### Access Control

Only predefined access IDs are permitted to view medical studies.

Example:

```
R-001 → Dr. Rishi
```

---

# ▸ Core Files

### Backend

```
backend/main.py
```

FastAPI server, authentication, WebSockets and DICOM SCP.

```
backend/triage_engine.py
```

Metadata analysis, anonymization and urgency assignment.

```
backend/dicom_to_gemini.py
```

Converts DICOM images into Gemini-compatible inputs and processes AI responses.

---

### Frontend

```
frontend/index.html
```

Main dashboard.

```
frontend/login.html
```

Secure login portal.

```
frontend/viewer.html
```

Authorized DICOM image viewer.

---

### Simulation

```
test_client/live_feed.py
```

Generates continuous synthetic hospital imaging traffic.

---

# ▸ Tech Stack

```text
Backend
- Python 3.10+
- FastAPI
- Pydicom
- Pynetdicom
- NumPy
- Pillow

Artificial Intelligence
- Google Gemini 1.5 Flash

Frontend
- HTML5
- CSS3
- JavaScript
- WebSockets
- Three.js
- Vanta.js

Medical Imaging
- DICOM
- PACS Simulation
```

---

# ▸ Setup

## Prerequisites

- Python 3.10+
- Google Gemini API Key

---

## Installation

Clone the repository

```bash
git clone https://github.com/yourusername/sentinel.git
cd sentinel
```

Install dependencies

```bash
pip install -r backend/requirements.txt
```

Configure your Gemini API Key inside:

```
backend/main.py
backend/dicom_to_gemini.py
```

Run the backend

```bash
uvicorn backend.main:app --reload
```

Start the hospital simulator

```bash
python test_client/live_feed.py
```

Open the dashboard

```
frontend/login.html
```

Login using a valid access ID.

Example:

```
R-001
```

---

# ▸ Specifications

| Component | Specification |
|------------|---------------|
| Backend Framework | FastAPI |
| DICOM Server | pynetdicom SCP |
| Image Processing | Pydicom + Pillow |
| AI Model | Gemini 1.5 Flash |
| Communication | REST + WebSockets |
| Viewer | Browser-based PNG Renderer |
| Authentication | Access ID Validation |
| Privacy | Automatic DICOM Anonymization |
| Logging | Audit Trail |
| Simulation | Live DICOM Feed Generator |

---

# ▸ Future Improvements

- PostgreSQL integration
- HL7 support
- Docker deployment
- Role-based authentication
- AI confidence visualization
- Multi-hospital simulation
- FHIR interoperability
- Study history and reporting

---

<h2 align="center">MIT License</h2>

<p align="center">
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files to deal in the Software
without restriction, including without limitation the rights to use, copy,
modify, merge, publish, distribute, sublicense, and/or sell copies of the Software.
</p>
