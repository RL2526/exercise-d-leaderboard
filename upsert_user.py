import sqlite3
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization

db_path= "data.db"

def upsert_user(name, public_key, current_score):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO users (name, public_key, current_score, max_score, last_updated)
    VALUES (?, ?, ?, ?, strftime('%s','now'));
    """, (name, public_key, current_score, current_score))

    conn.commit()
    conn.close()

def generate_key_pair(person_name: str) -> tuple[bytes, bytes]:
    """
    Generiert ein Ed25519 Schlüsselpaar und speichert es.
    Gibt private_key_pem und public_key_pem zurück.
    """
    # Schlüsselpaar generieren
    private_key = ed25519.Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    
    # Private Key speichern (unverschlüsselt - bei Bedarf mit Passwort)
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    # Öffentlicher Key speichern
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    
    # Speichern (z.B. für Person1, Person2...)
    with open(f"keys/{person_name}_private.pem", "wb+") as f:
        f.write(private_pem)
    
    
    
    print(f"✓ Schlüsselpaar für {person_name} generiert")
    return public_pem

if __name__ == "__main__":
    print("test")
    student_name = "panda"
    public_key = generate_key_pair(student_name)
    upsert_user(student_name, public_key, 0.0)
