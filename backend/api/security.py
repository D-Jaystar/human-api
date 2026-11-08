import hashlib
import secrets
import time
from collections import defaultdict
from fastapi import HTTPException, Request

# In-memory opslag voor verzoeken per IP: { "127.0.0.1": [1700000010.2, 1700000012.5, ...] }
_RATE_LIMIT_STORE: dict[str, list[float]] = defaultdict(list)


def generate_device_token() -> str:
    """
    Genereert een cryptografisch veilige willekeurige token voor een apparaat (256-bit entropie).
    """
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    """
    Hasht een platte token met SHA-256 zodat tokens nooit in plaintext
    in de database worden opgeslagen.
    """
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def verify_token(plain_token: str, stored_hash: str) -> bool:
    """
    Verifieert of een meegegeven platte token overeenkomt met de opgeslagen hash.
    Gebruikt secrets.compare_digest om timing attacks tegen te gaan.
    """
    candidate_hash = hash_token(plain_token)
    return secrets.compare_digest(candidate_hash, stored_hash)


def check_rate_limit(request: Request, max_requests: int = 5, window_seconds: int = 60) -> None:
    """
    Anti-Intruder & Anti-Farming bescherming:
    Houdt per IP-adres bij hoeveel verzoeken er binnenkomen.
    Wordt de limiet overschreden? Dan wordt het verzoek direct afgekapt met HTTP 429.
    """
    # Achterhaal het IP-adres van de bezoeker
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()

    # Schoon timestamps op die ouder zijn dan het tijdvenster (sliding window)
    _RATE_LIMIT_STORE[client_ip] = [
        timestamp for timestamp in _RATE_LIMIT_STORE[client_ip]
        if now - timestamp < window_seconds
    ]

    # Controleer of de limiet bereikt is
    if len(_RATE_LIMIT_STORE[client_ip]) >= max_requests:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit bereikt! Maximaal {max_requests} registraties per {window_seconds} seconden.",
        )

    # Voeg het huidige verzoek toe aan de geschiedenis
    _RATE_LIMIT_STORE[client_ip].append(now)
