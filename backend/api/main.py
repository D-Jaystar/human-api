from fastapi import FastAPI, Header, HTTPException, Request
from backend.models.schemas import ActivityLogCreate, DeviceRegister, HealthMetricCreate
from backend.api.security import check_rate_limit, generate_device_token, hash_token, verify_token
from backend.db.crud import get_device, log_activity, log_health_metric, register_device

app = FastAPI(
    title="Human API",
    description="Persoonlijke Tijd- & Focus-Engine API",
    version="1.0.0",
)


def authenticate_device(device_id: str, authorization: str | None) -> None:
    """
    Hulpfunctie om te verifiëren of het meegestuurde Bearer token
    overeenkomt met de opgeslagen hash van het apparaat in SQLite.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Ongeldig autorisatieformaat. Gebruik: Bearer <token>",
        )

    token = authorization.split(" ", 1)[1].strip()

    # Zoek apparaat op in database
    device = get_device(device_id)
    if not device:
        raise HTTPException(
            status_code=404,
            detail=f"Apparaat met ID '{device_id}' niet gevonden.",
        )

    # Verifieer token hash met timing-attack beveiliging
    if not verify_token(token, device["token_hash"]):
        raise HTTPException(
            status_code=401,
            detail="Ongeldig token voor dit apparaat.",
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
    check_rate_limit(request, max_requests=5, window_seconds=60)

    try:
        token = generate_device_token()
        token_hash = hash_token(token)

        success = register_device(payload.device_id, payload.name, token_hash)
        if not success:
            raise HTTPException(
                status_code=400,
                detail=f"Device met ID '{payload.device_id}' is al geregistreerd.",
            )

        return {
            "status": "success",
            "device_id": payload.device_id,
            "token": token,
        }

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Er is een interne serverfout opgetreden bij het registreren.",
        )


@app.post("/api/activity")
def create_activity_log(
    payload: ActivityLogCreate,
    authorization: str = Header(..., description="Bearer <device_token>"),
) -> dict:
    """
    Ontvangt en slaat een computeractiviteit-tijdblok op (venstertitel, app, duur, AFK-status).
    Beveiligd met Bearer token authenticatie.
    """
    # 1. Beveiligingscontrole: token verifiëren
    authenticate_device(payload.device_id, authorization)

    try:
        # 2. Sla het activiteit record op in SQLite
        log_id = log_activity(
            device_id=payload.device_id,
            app_name=payload.app_name,
            window_title=payload.window_title,
            is_afk=payload.is_afk,
            start_time=payload.start_time,
            end_time=payload.end_time,
            duration_sec=payload.duration_sec,
        )

        if log_id is None:
            raise HTTPException(
                status_code=500,
                detail="Kon activiteitslog niet opslaan in de database.",
            )

        return {
            "status": "success",
            "log_id": log_id,
            "message": "Activiteit succesvol gelogd.",
        }

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Er ging iets mis op de server bij het verwerken van de activiteit.",
        )


@app.post("/api/health")
def create_health_metric(
    payload: HealthMetricCreate,
    authorization: str = Header(..., description="Bearer <device_token>"),
) -> dict:
    """
    Ontvangt en slaat gezondheidsmetingen op (stappen, slaap, hartslag van telefoon).
    Beveiligd met Bearer token authenticatie.
    """
    # 1. Beveiligingscontrole: token verifiëren
    authenticate_device(payload.device_id, authorization)

    try:
        # 2. Sla de health metric op in SQLite
        metric_id = log_health_metric(
            device_id=payload.device_id,
            metric_type=payload.metric_type,
            value=payload.value,
            recorded_at=payload.recorded_at,
        )

        if metric_id is None:
            raise HTTPException(
                status_code=500,
                detail="Kon gezondheidsmeting niet opslaan in de database.",
            )

        return {
            "status": "success",
            "metric_id": metric_id,
            "message": "Gezondheidsmeting succesvol opgeslagen.",
        }

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Er ging iets mis op de server bij het verwerken van de gezondheidsdata.",
        )
