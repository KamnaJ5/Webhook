# CivicAlert — Quick Setup

## 1. Create & Activate Virtual Environment

```powershell
# Already created — just activate:
venv\Scripts\activate

# You'll see (venv) in your prompt
```

## 2. Install Dependencies

```powershell
pip install -r requirements.txt
```

## 3. Run the App

```powershell
python app.py
```

Open → **http://localhost:5000**

---

## Demo Credentials (Authority Login)

| Username | Password | Role |
|----------|----------|------|
| `admin` | `civic2024` | Primary admin |
| `authority` | `hackathon` | Second demo account |

Login page: **http://localhost:5000/admin/login**

---

## Pre-seeded Demo Issue IDs

| ID | Type | Status |
|----|------|--------|
| `CIV0000001` | Road Damage | Pending |
| `CIV0000002` | Garbage Overflow | Pending |
| `CIV0000003` | Flooding / Drain | In Progress |
| `CIV0000004` | Broken Streetlight | In Progress |
| `CIV0000005` | Water Leakage | Resolved |

Track any at: **http://localhost:5000/track**

---

## Project Structure

```
smart_civic/
├── app.py              ← Flask app (routes + auth + priority logic)
├── civic.db            ← SQLite DB (auto-created)
├── requirements.txt    ← Dependencies
├── venv/               ← Virtual environment
├── templates/
│   ├── base.html       ← Shared layout + navbar
│   ├── index.html      ← Home page
│   ├── report.html     ← Citizen: report issue
│   ├── track.html      ← Citizen: track by ID
│   ├── login.html      ← Admin login page
│   ├── admin.html      ← Authority dashboard
│   ├── issue_detail.html ← Authority: update issue
│   └── analytics.html  ← Charts & hotspots
└── static/
    ├── style.css        ← All styles
    └── uploads/         ← Photo uploads
```
