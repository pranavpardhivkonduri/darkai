# DarkAI — Understanding the Criminal Misuse of Artificial Intelligence

> **B.Tech AI & ML Final Year Academic Project** — Full-stack cybersecurity prototype

---

## Abstract

Artificial Intelligence has enabled a new class of cyber threats including deepfakes, voice cloning, AI-generated phishing, intelligent malware, identity theft, and automated social engineering. Conventional cybersecurity tools were not designed to counter these AI-generated threats.

**DarkAI** proposes an AI-driven cybersecurity framework that uses AI itself to detect and prevent AI-based cyberattacks in real-time.

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, TypeScript, Vite, Tailwind CSS, Recharts |
| Backend | Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy |
| Database | SQLite (dev) / PostgreSQL (prod) |
| Auth | JWT (python-jose), bcrypt (passlib), TOTP (pyotp) |
| ML/AI | scikit-learn, OpenCV, Librosa, NumPy, SciPy |
| Security | MFA/TOTP, RBAC, SHA-256 hash-chain audit ledger |

---

## Project Structure

```
darkai/
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI app entry point
│   │   ├── config.py          # Central configuration
│   │   ├── api/               # Route handlers
│   │   │   ├── auth.py        # Authentication endpoints
│   │   │   ├── analysis.py    # Analysis endpoints
│   │   │   └── routes.py      # Dashboard, incidents, audit, etc.
│   │   ├── models/            # SQLAlchemy ORM models
│   │   ├── schemas/           # Pydantic request/response schemas
│   │   ├── services/
│   │   │   ├── ml/            # AI/ML detection modules
│   │   │   │   ├── phishing_detector.py
│   │   │   │   ├── deepfake_detector.py
│   │   │   │   ├── voice_detector.py
│   │   │   │   └── anomaly_detector.py
│   │   │   ├── risk_engine.py
│   │   │   ├── audit_service.py
│   │   │   └── watermark_service.py
│   │   ├── auth/              # JWT, security, dependencies
│   │   └── database/          # DB session and initialization
│   ├── requirements.txt
│   └── .env
├── frontend/
│   ├── src/
│   │   ├── pages/             # All page components
│   │   ├── components/        # Reusable UI components
│   │   ├── contexts/          # React context (Auth)
│   │   ├── lib/               # API client, utilities
│   │   └── types/             # TypeScript types
│   ├── package.json
│   └── vite.config.ts
├── start_backend.bat
├── start_frontend.bat
└── README.md
```

---

## Quick Start

### Prerequisites

- Python 3.10+ (with pip)
- Node.js 18+ (with npm)

### 1. Backend Setup

```bash
cd backend

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
source venv/bin/activate       # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Copy environment file
copy .env.example .env

# Start backend (database is auto-created on first run)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Or simply run:** `start_backend.bat`

### 2. Frontend Setup

```bash
cd frontend

# Install npm dependencies
npm install

# Start development server
npm run dev
```

**Or simply run:** `start_frontend.bat`

### 3. Access the Application

| Service | URL |
|---------|-----|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| API Documentation | http://localhost:8000/api/docs |
| Health Check | http://localhost:8000/api/health |

---

## Demo Credentials

| Role | Username | Password | Capabilities |
|------|----------|----------|-------------|
| Admin | `admin` | `Admin@1234` | Full access, user management |
| Security Analyst | `analyst` | `Analyst@1234` | Analysis, incidents, reports |
| User | `user` | `User@1234` | Submit content, view own results |

---

## AI/ML Modules

### 1. Phishing Detector (`phishing_detector.py`)
- **Model**: TF-IDF + Logistic Regression
- **Features**: N-gram TF-IDF text features, URL structural analysis
- **Classes**: Legitimate, Suspicious, Phishing
- **Dataset**: Curated demonstration dataset (~70 samples)
- **Note**: Prototype dataset. Replace `TRAINING_DATA` with Enron + SpamAssassin corpus for production.

### 2. Deepfake Detector (`deepfake_detector.py`)
- **Approach**: Signal-processing feature extraction (OpenCV)
- **Features**: DCT frequency analysis, Local Binary Patterns, noise estimation, color correlation, block artifacts
- **Supports**: JPG, PNG, MP4, AVI
- **Note**: Prototype detector. For production, replace with EfficientNet-based FaceForensics++ model.

### 3. Voice Clone Detector (`voice_detector.py`)
- **Model**: Isolation Forest on audio features
- **Features**: MFCC (13 coeff), spectral centroid, bandwidth, rolloff, ZCR, RMS, chroma, silence ratio, F0
- **Dataset**: Synthetic reference distribution (natural speech statistics from literature)
- **Note**: Prototype. Production system would use ASVspoof 2019 labelled corpus.

### 4. Behavioral Anomaly Detector (`anomaly_detector.py`)
- **Model**: Isolation Forest with StandardScaler
- **Features**: Login hour (cyclic encoded), failed attempts, new device, unusual location, access frequency, session duration, request rate
- **Dataset**: Synthetic normal behavior distribution
- **Note**: Per-user baseline learning would improve real-world performance.

### 5. Risk Engine (`risk_engine.py`)
- Combines all detector scores with configurable weights
- Thresholds: 0-29=LOW, 30-59=MEDIUM, 60-79=HIGH, 80-100=CRITICAL
- All thresholds defined in `config.py`

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/v1/auth/register | Register new user |
| POST | /api/v1/auth/login | Login |
| POST | /api/v1/auth/mfa/verify | Verify MFA TOTP |
| GET | /api/v1/auth/mfa/setup | Get MFA QR code |
| POST | /api/v1/auth/mfa/enable | Enable MFA |
| POST | /api/v1/analyze/text | Phishing text analysis |
| POST | /api/v1/analyze/url | URL analysis |
| POST | /api/v1/analyze/image | Deepfake image analysis |
| POST | /api/v1/analyze/video | Deepfake video analysis |
| POST | /api/v1/analyze/audio | Voice clone detection |
| POST | /api/v1/analyze/behavior | Behavioral anomaly |
| GET | /api/v1/dashboard/statistics | Dashboard stats |
| GET | /api/v1/dashboard/timeline | Threat timeline |
| GET | /api/v1/incidents | List incidents |
| POST | /api/v1/incidents/{id}/status | Update incident status |
| GET | /api/v1/alerts | Security alerts |
| POST | /api/v1/watermark/create | Create watermark |
| POST | /api/v1/watermark/verify | Verify watermark |
| GET | /api/v1/audit/logs | Audit log entries |
| POST | /api/v1/audit/verify | Verify audit chain |
| POST | /api/v1/reports/generate/{id} | Generate report |

---

## Demo Workflow (Presentation Guide)

### Demo 1: Phishing Detection
1. Login as `user` → Dashboard
2. Go to **Threat Analyzer** → select **Text/Email**
3. Click **Load Demo** (loads phishing email sample)
4. Click **Analyze** — backend runs TF-IDF+LR classifier
5. See: risk score, label (PHISHING), confidence, indicators, XAI explanation
6. Go to **Incidents** — auto-created high-risk incident
7. Login as `analyst` → update incident status, add notes
8. Go to **Reports** → generate incident report

### Demo 2: Deepfake Detection
1. Go to **Threat Analyzer** → **Image**
2. Upload any `.jpg/.png` image
3. Backend runs DCT/LBP/noise analysis
4. See manipulation score and indicators

### Demo 3: Voice Clone Detection
1. Go to **Threat Analyzer** → **Audio**
2. Upload a `.wav/.mp3` file
3. Backend extracts MFCC, spectral, ZCR features
4. Isolation Forest scores anomaly

### Demo 4: Behavioral Anomaly
1. Go to **Threat Analyzer** → **Behavior**
2. Click **Load Demo** (login at 3AM, 4 failed attempts, new device)
3. See ANOMALOUS result with contributing factors

### Demo 5: Watermarking
1. Go to **Watermarking** → **Register**
2. Upload a file, enter owner and content ID
3. See SHA-256 hash stored
4. Switch to **Verify** tab, upload SAME file → AUTHENTIC
5. (Demo) Re-upload a DIFFERENT file with same content ID → MODIFIED

### Demo 6: Audit Chain
1. Go to **Audit Ledger**
2. Click **Verify Chain** → VALID
3. All events from analyses are listed with hashes
4. Show: each record's hash includes previous hash (chain linkage)

---

## Security Features

- JWT authentication with configurable expiry
- bcrypt password hashing (never plain-text passwords)
- TOTP-based MFA (Google Authenticator compatible)
- Role-based access control (ADMIN / ANALYST / USER)
- File validation: extension whitelist, size limits, path traversal prevention
- Account lockout after 5 failed login attempts
- SHA-256 hash-chain tamper-evident audit ledger

---

## Limitations (Documented)

1. **Phishing Detector**: Trained on a small demonstration dataset. Not suitable for production use without a real corpus (e.g., Enron + SpamAssassin).

2. **Deepfake Detector**: Feature-based signal processing, not a deep neural network. Cannot reliably detect all GAN-generated deepfakes. A production system would use FaceForensics++ with EfficientNet.

3. **Voice Clone Detector**: Trained on a synthetic reference distribution. Real performance requires labelled natural/synthetic speech data (e.g., ASVspoof 2019).

4. **Behavioral Anomaly**: Uses a synthetic normal-behavior baseline. Per-user historical baseline learning would significantly improve real-world performance.

5. **Report Generation**: JSON format only. PDF generation can be added with `reportlab` as an enhancement.

---

## Future Scope

- Integrate pre-trained deepfake detection models (FaceForensics++)
- Train voice clone detector on ASVspoof dataset
- Add real-time streaming analysis
- Implement federated learning for privacy-preserving model updates
- Add blockchain integration for immutable audit records
- Add email/SMS alerting via SMTP/Twilio
- Extend to browser extension for in-browser phishing detection
- Add MITRE ATT&CK framework mapping

---

## Ethical AI Statement

DarkAI provides automated risk indicators for cybersecurity analysis. Results should be reviewed by qualified personnel before being treated as definitive evidence of malicious or criminal activity. False positives are possible with any automated system. Human oversight is a core design principle.

---

*B.Tech AI & ML Academic Project — Not for production use without further security review and hardening.*
