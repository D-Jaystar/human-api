# 🧠 Human API: Persoonlijke Tijd- & Focus-Engine

Een modulair, lokaal gehost meetsysteem voor schermactiviteit, focus, cognitieve belasting en gezondheidstelemetrie.

---

## 💡 Filosofie: Waarom een Human API?

Traditionele productiviteits-apps falen vaak omdat ze handmatige discipline vereisen: zodra je druk of moe bent, stop je met invullen. De **Human API** draait dit om:
* **Nul Handmatige Frictie:** Achtergrondscripts op je pc registreren passief waar tijd en aandacht naartoe gaan.
* **Van Ruwe Tijd naar Mentale Status:** Meet naast totale schermtijd ook de *Fragmentation Rate* (hoe vaak je wisselt tussen vensters) en inactiviteit (AFK).
* **100% Eigenaarschap & Privacy:** Alle data blijft lokaal op je eigen systeem in SQLite met Write-Ahead Logging (WAL) en beveiliging via cryptografische Bearer tokens.

---

## 🏛️ Architectuur & Componenten

```
human_api/
├── backend/
│   ├── api/
│   │   ├── main.py         # FastAPI REST API (Swagger UI, endpoints)
│   │   └── security.py     # Token hashing (SHA-256), timing attack defense, rate limiting
│   ├── db/
│   │   ├── database.py     # SQLite WAL-mode verbinding & automatische backups
│   │   └── crud.py         # Database bewerkingen (devices, activity, health, hourly_stats)
│   └── models/
│       └── schemas.py      # Pydantic validatiemodellen
└── pc_logger/
    ├── tracker.py          # Windows voorgrondvenster & proces-inspectie (User32 / psutil)
    ├── idle.py             # AFK-detectie via GetLastInputInfo (milliseconde nauwkeurig)
    └── logger.py           # Context switch engine met offline wachtrij en API-verzending
```

---

## 🚀 Snelle Start

### 1. Installatie
Clone de repository en activeer de virtuele omgeving:
```powershell
git clone https://github.com/D-Jaystar/human-api.git
cd human_api
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Database Initialiseren
```powershell
python backend/db/database.py
```

### 3. Server Starten
Start de FastAPI-server:
```powershell
uvicorn backend.api.main:app --reload
```
Open **http://127.0.0.1:8000/docs** in je browser om de interactieve Swagger UI te bekijken.

### 4. Windows Logger Starten
```powershell
python pc_logger/logger.py
```

---

## 🗺️ Roadmap

- [x] **Fase 1:** SQL Database (WAL-mode), Pydantic Validatie & Beveiligde FastAPI Server
- [x] **Fase 2:** Windows Computer Logger (Window tracker, AFK detectie, offline buffer)
- [ ] **Fase 3:** Android Telefoon Bridge (Health Connect data, schermtijd sync)
- [ ] **Fase 4:** Dashboard & Cognitieve Belasting (Focus score & visualisatie)
