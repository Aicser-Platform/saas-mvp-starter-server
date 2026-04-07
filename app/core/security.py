from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from uuid import UUID
import base64
import urllib.request
import json
import threading

from app.core.config import get_settings
from app.db.database import get_db
from app.models.user import User

security = HTTPBearer()

# ── JWKS cache ────────────────────────────────────────────────────────────────
_jwks_cache: dict | None = None
_jwks_lock = threading.Lock()


def _fetch_jwks(jwks_url: str) -> dict:
    """Fetch JWKS from Supabase, with a simple in-process cache."""
    global _jwks_cache
    if _jwks_cache is not None:
        return _jwks_cache
    with _jwks_lock:
        if _jwks_cache is not None:
            return _jwks_cache
        with urllib.request.urlopen(jwks_url, timeout=10) as resp:
            _jwks_cache = json.loads(resp.read().decode())
    return _jwks_cache


# ── Token verification ────────────────────────────────────────────────────────

def verify_supabase_token(token: str) -> dict:
    """Decode and verify a Supabase JWT, returning its claims.

    Modern Supabase projects (2024+) use ES256 (asymmetric EC key).
    Older / self-hosted projects may still use HS256.
    We auto-detect from the JWT header and verify accordingly.
    """
    settings = get_settings()
    decode_opts = {"options": {"verify_aud": False}}

    # ── Inspect header WITHOUT verifying ─────────────────────────────────────
    try:
        header = jwt.get_unverified_header(token)
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Malformed token: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    alg = header.get("alg", "HS256")
    kid = header.get("kid")

    # ── ES256 / RS256: asymmetric — verify via JWKS ───────────────────────────
    if alg in ("ES256", "RS256") or kid:
        supabase_url = settings.SUPABASE_URL.rstrip("/")
        if not supabase_url:
            # Pull issuer from the unverified payload as fallback
            try:
                unverified = jwt.get_unverified_claims(token)
                iss = unverified.get("iss", "")
                # iss looks like "https://xxx.supabase.co/auth/v1"
                supabase_url = iss.replace("/auth/v1", "")
            except Exception:
                pass

        if not supabase_url:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="SUPABASE_URL is not configured in .env",
            )

        jwks_url = f"{supabase_url}/auth/v1/.well-known/jwks.json"

        try:
            jwks = _fetch_jwks(jwks_url)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Could not fetch JWKS from Supabase: {e}",
            )

        # Find matching key by kid, or try all keys
        keys = jwks.get("keys", [])
        if kid:
            matched = [k for k in keys if k.get("kid") == kid]
            keys = matched if matched else keys

        if not keys:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No matching public key found in JWKS",
                headers={"WWW-Authenticate": "Bearer"},
            )

        last_error: Exception | None = None
        for jwk_key in keys:
            try:
                return jwt.decode(token, jwk_key, algorithms=[alg], **decode_opts)
            except JWTError as e:
                last_error = e

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {last_error}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # ── HS256: symmetric — verify via SUPABASE_JWT_SECRET ────────────────────
    secret = settings.SUPABASE_JWT_SECRET
    candidates: list = [secret, secret.encode("utf-8")]
    try:
        candidates.append(base64.urlsafe_b64decode(secret + "=="))
    except Exception:
        pass

    last_error = None
    for key in candidates:
        try:
            return jwt.decode(token, key, algorithms=["HS256"], **decode_opts)
        except JWTError as e:
            last_error = e

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=f"Invalid or expired token: {last_error}",
        headers={"WWW-Authenticate": "Bearer"},
    )


# ── FastAPI dependencies ──────────────────────────────────────────────────────

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: Session = Depends(get_db),
) -> User:
    """
    Verifies the Supabase Bearer token and returns (or auto-creates) the
    corresponding local User record.
    """
    payload = verify_supabase_token(credentials.credentials)

    supabase_uid = payload.get("sub")
    email = payload.get("email")
    full_name = (
        payload.get("user_metadata", {}).get("full_name")
        or payload.get("user_metadata", {}).get("name")
        or None
    )

    if not supabase_uid:
        raise HTTPException(status_code=401, detail="Token missing subject")

    try:
        uid = UUID(supabase_uid)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid user ID in token")

    user = db.query(User).filter(User.id == uid).first()
    if not user:
        # First login — auto-create the local user record with metadata from JWT
        user = User(
            id=uid,
            email=email or f"{supabase_uid}@unknown.com",
            full_name=full_name,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    return user


def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    """Dependency that ensures the current user is an admin."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user
