"""
channel.py  --  the sealed message channels that keep Aegis blind
=================================================================
WHY THIS EXISTS
---------------
Aegis routes messages between banks, but must not learn the entity being asked
about, nor which banks match. We make that REAL (not just a promise) with two
sealed channels. Aegis holds neither key, so it can only relay opaque blobs.

  1. BROADCAST channel (querying bank  ->  all member banks)
     Sealed with a symmetric key shared by the MEMBER BANKS but NOT Aegis.
     So every bank can read the query; Aegis cannot.

  2. REPLY channel (each member bank  ->  the querying bank)
     Sealed to the querying bank's one-time PUBLIC key. Only the querying bank
     (which holds the matching private key) can open the replies -- not Aegis,
     and not the other banks. So no one sees another bank's recipe.

These are ordinary, well-tested primitives (no home-made crypto):
  * Fernet  = authenticated symmetric encryption, for the broadcast.
  * RSA-OAEP wrapping a fresh Fernet key = "seal to a public key", for replies.

TRUST ASSUMPTION (state this in the video): the member banks share the broadcast
key with each other but not with Aegis. In production you would replace the
shared symmetric key with per-bank public keys so banks need not share a secret;
the structure here is identical.
"""

import base64
import json

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding


# ---- broadcast channel: readable by member banks, opaque to Aegis ----------
def new_broadcast_key() -> bytes:
    """The symmetric key shared among member banks (Aegis never gets this)."""
    return Fernet.generate_key()


def broadcast_seal(broadcast_key: bytes, payload: dict) -> bytes:
    return Fernet(broadcast_key).encrypt(json.dumps(payload).encode())


def broadcast_open(broadcast_key: bytes, blob: bytes) -> dict:
    return json.loads(Fernet(broadcast_key).decrypt(blob).decode())


# ---- reply channel: sealed to the querying bank's public key ---------------
def new_reply_keypair():
    """A one-time keypair the querying bank makes for a single query.
    Returns (private_key_object, public_key_pem_string)."""
    priv = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pub_pem = priv.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("ascii")
    return priv, pub_pem


def _oaep():
    return padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()),
                        algorithm=hashes.SHA256(), label=None)


def reply_seal(reply_pub_pem: str, payload: dict) -> dict:
    """Seal a reply so ONLY the querying bank can open it (hybrid RSA+Fernet)."""
    pub = serialization.load_pem_public_key(reply_pub_pem.encode("ascii"))
    fkey = Fernet.generate_key()
    body = Fernet(fkey).encrypt(json.dumps(payload).encode())
    wrapped = pub.encrypt(fkey, _oaep())
    return {"wrapped_key": base64.b64encode(wrapped).decode(), "body": body.decode()}


def reply_open(reply_priv, sealed: dict) -> dict:
    fkey = reply_priv.decrypt(base64.b64decode(sealed["wrapped_key"]), _oaep())
    return json.loads(Fernet(fkey).decrypt(sealed["body"].encode()).decode())
