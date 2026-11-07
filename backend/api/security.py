import hashlib
import secrets


def generate_device_token() -> str:
    """
    Genereert een cryptografisch veilige willekeurige token voor een apparaat.
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
