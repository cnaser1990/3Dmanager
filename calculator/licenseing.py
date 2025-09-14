# calculator/licensing.py
import os, time, hashlib, sqlite3, platform, uuid
from jose import jwt, JWTError
from django.core.exceptions import PermissionDenied
from pathlib import Path
import os

def get_data_dir():
    # Don't import settings at module level
    try:
        from django.conf import settings
        app_name = getattr(settings, "APP_NAME", "Calculator")
    except Exception:
        app_name = "Calculator"
    
    data_dir = Path.home() / ".local" / "share" / app_name
    os.makedirs(data_dir, exist_ok=True)
    return str(data_dir)

DATA_DIR = get_data_dir()
LICENSE_FILE_PATH = os.path.join(DATA_DIR, "license.lic")
STATE_DB = os.path.join(DATA_DIR, "lic_state.sqlite3")
CHECK_INTERVAL = 60  # seconds

# Get public key from settings or use a default
def get_public_key():
    try:
        from django.conf import settings
        return getattr(settings, "LICENSE_PUBLIC_KEY_PEM", None)
    except Exception:
        return None

# Fallback public key (replace with your actual RSA public key)
PUBLIC_KEY_PEM = get_public_key() or """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAmJU91mU/KwhAlRGHn3ic
LLVgk52ptb/1hh0rz3TZvU3O67gzBNZL+fT/ffaqMEe6SqCPwOlIlSOwXTF9mJVt
bosqAXzKA+vm0b0172kMhFi386n89RcMLiDw8FqnZvKBoLFGi7mv7TXOzp7uQe5L
PsFsNrBIHairGGBKZJy8PQWVJYxuR4EEJLqEk/o1DWzyEpsEcS+RdFcf7GV9SHFi
RqL4WEErxx+3ZIHW6AWl4ahaeobdyHctHC2fkshoSqssxjFuJ0DmhK6Xsw5Suklw
DOPENK8XhU+6Vn2t7q59PTVv3QJBZHAehEY9+pXaG9Q/fHR74bq8UBdDPiJsECTj
bwIDAQAB
-----END PUBLIC KEY-----"""

_cached = {"payload": None, "checked_at": 0}

def ensure_dirs():
    os.makedirs(DATA_DIR, exist_ok=True)

def get_hw_fingerprint():
    parts = [
        platform.node(),
        platform.system(),
        platform.machine(),
        hex(uuid.getnode()),
    ]
    return hashlib.sha256("|".join(parts).encode()).hexdigest()

def ensure_state_db():
    ensure_dirs()
    conn = sqlite3.connect(STATE_DB)
    cur = conn.cursor()
    cur.execute("""
        create table if not exists t(
            id integer primary key,
            last_seen_unix integer not null
        )
    """)
    cur.execute("insert or ignore into t(id,last_seen_unix) values (1,0)")
    conn.commit()
    conn.close()

def update_and_check_clock(now: int):
    ensure_state_db()
    conn = sqlite3.connect(STATE_DB)
    cur = conn.cursor()
    cur.execute("select last_seen_unix from t where id=1")
    row = cur.fetchone()
    last_seen = row[0] if row else 0
    if now + 300 < last_seen:
        conn.close()
        raise PermissionDenied("System clock rollback detected. License check failed.")
    if now > last_seen:
        cur.execute("update t set last_seen_unix=? where id=1", (now,))
        conn.commit()
    conn.close()

def read_license_file():
    ensure_dirs()
    if not os.path.exists(LICENSE_FILE_PATH):
        return None
    with open(LICENSE_FILE_PATH, "r", encoding="utf-8") as f:
        return f.read().strip()

def verify_license(token: str):
    try:
        # Changed from EdDSA to RS256
        payload = jwt.decode(token, PUBLIC_KEY_PEM, algorithms=["RS256"])
    except JWTError as e:
        raise PermissionDenied(f"Invalid license: {e}")
    now = int(time.time())
    exp = payload.get("exp")
    if exp is None or now > exp:
        raise PermissionDenied("License expired")
    hw = payload.get("hw")
    if hw and hw != get_hw_fingerprint():
        raise PermissionDenied("License not valid for this device")
    return payload

def check_license(force=False):
    now = int(time.time())
    if not force and _cached["payload"] and now - _cached["checked_at"] < CHECK_INTERVAL:
        return _cached["payload"]
    token = read_license_file()
    if not token:
        raise PermissionDenied("No license installed")
    update_and_check_clock(now)
    payload = verify_license(token)
    _cached.update({"payload": payload, "checked_at": now})
    return payload

def license_status():
    try:
        payload = check_license(force=True)
        return {
            "valid": True,
            "payload": payload,
            "expires_in_days": max(0, int((payload["exp"] - int(time.time())) / 86400)),
        }
    except PermissionDenied as e:
        return {"valid": False, "error": str(e)}