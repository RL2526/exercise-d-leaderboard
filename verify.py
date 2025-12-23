import json
import sqlite3
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.exceptions import InvalidSignature

db_path= "data.db"

def get_public_key_by_name(name):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute(
        "SELECT public_key FROM users WHERE name = ?",
        (name,)
    )
    row = cur.fetchone()
    conn.close()

    if row is None:
        return None  
    return row[0]

def verify_signed_json(username, payload: dict) -> bool:
    # 1. Signature als rohe UTF-8 Bytes
    signature_str = payload.get("signature")
    if not signature_str:
        return False

    signature = bytes.fromhex(signature_str)

    # 2. Message kanonisch serialisieren
    message = payload["result"]

    # 3. Public Key aus DB (UTF-8 → bytes)
    public_key_str = get_public_key_by_name(username)
    if not public_key_str:
        return False

    public_key_bytes = public_key_str.encode("utf-8")

    try:
        public_key = Ed25519PublicKey.from_public_bytes(public_key_bytes)
    except ValueError:
        return False

    # 4. Verify
    try:
        public_key.verify(signature, message)
        return True
    except InvalidSignature:
        return False
