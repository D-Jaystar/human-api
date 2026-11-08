from fastapi import FastAPI, HTTPException, Request
from backend.models.schemas import DeviceRegister
from backend.api.security import generate_device_token, hash_token, check_rate_limit
from backend.db.crud import register_device

app = FastAPI(
    title="Human API",
    description="Persoonlijke Tijd- & Focus-Engine API",
    version="1.0.0",
)


@app.get("/health")
def health_check() -> dict:
    """
    Eenvoudig test-endpoint om te controleren of de API server online is.
    """
    return {"status": "ok", "message": "Human API is running"}


@app.post("/api/devices/register")
def register_new_device(payload: DeviceRegister, request: Request) -> dict:
    """
    Registreert een nieuw apparaat en levert een eenmalig geheim API-token op.
    Beveiligd tegen Burp Intruder / token-farming via rate limiting.
    """
    # 1. Beveiliging: Blokkeer geautomatiseerde spam / token farms (max 5 per minuut per IP)
    check_rate_limit(request, max_requests=5, window_seconds=60)

    try:
        # 2. Genereer een cryptografische token en hash hem direct
        token = generate_device_token()
        token_hash = hash_token(token)

        # 3. Sla het apparaat veilig op in SQLite
        success = register_device(payload.device_id, payload.name, token_hash)
        if not success:
            raise HTTPException(
                status_code=400,
                detail=f"Device met ID '{payload.device_id}' is al geregistreerd.",
            )

        # 4. Geef het token eenmalig terug aan de client
        return {
            "status": "success",
            "device_id": payload.device_id,
            "token": token,
        }

    except HTTPException:
        # Gooi verwachte HTTP-fouten (zoals 400 of 429) netjes door naar de client
        raise
    except Exception as e:
        # Vang onverwachte database- of netwerkcrashes af (geen stacktrace leaken!)
        raise HTTPException(
            status_code=500,
            detail="Er is een interne serverfout opgetreden bij het registreren.",
        )
