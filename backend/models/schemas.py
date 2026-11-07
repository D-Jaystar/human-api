from pydantic import BaseModel, Field


class DeviceRegister(BaseModel):
    """
    Schema voor het aanmelden van een nieuw apparaat.
    """
    device_id: str = Field(..., min_length=2, description="Uniek ID van het apparaat (bijv. pc-01 of pixel-8)")
    name: str = Field(..., min_length=1, description="Leesbare naam (bijv. Laptop Werk)")


class ActivityLogCreate(BaseModel):
    """
    Schema voor het valideren van binnenkomende activiteitenlogs.
    """
    device_id: str = Field(..., min_length=1, description="Het apparaat dat de activiteit logt")
    app_name: str = Field(..., min_length=1, description="Naam van de applicatie (bijv. IntelliJ, Chrome)")
    window_title: str = Field(default="", description="Titel van het actieve venster")
    is_afk: bool = Field(default=False, description="Of de gebruiker afwezig / inactief was")
    start_time: str = Field(..., description="ISO 8601 timestamp van begin (bijv. 2026-11-07T12:00:00)")
    end_time: str = Field(..., description="ISO 8601 timestamp van eind (bijv. 2026-11-07T12:05:00)")
    duration_sec: int = Field(..., ge=0, description="Duur in seconden (mag nooit negatief zijn)")


class HealthMetricCreate(BaseModel):
    """
    Schema voor het valideren van binnenkomende gezondheidsmetingen.
    """
    device_id: str = Field(..., min_length=1, description="Het apparaat dat de meting verstuurt")
    metric_type: str = Field(..., min_length=1, description="Type meting (bijv. steps, sleep_minutes, heart_rate)")
    value: float = Field(..., description="De numerieke meetwaarde")
    recorded_at: str = Field(..., description="ISO 8601 timestamp van het meetmoment")
