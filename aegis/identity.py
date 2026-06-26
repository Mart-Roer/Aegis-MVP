"""
identity.py  --  the shared cross-bank identifier
=================================================
THE PROBLEM THIS SOLVES
-----------------------
Two banks each hold "Jan de Vries, born 1980-03-02". To check whether they mean
the SAME person, they must compare something -- but they cannot pass each other
raw names and addresses (that is sharing personal data). So every bank derives
the SAME opaque code from the SAME identifying fields, using one agreed function.
Same person in, same code out, at every bank. Banks then match on the code.

WHAT THIS FILE PRODUCES
-----------------------
  canonicalize(attrs)        -> a normalised byte-string of the identity fields,
                                so trivial differences (case, spacing) don't
                                produce different codes.
  shared_identifier(attrs)   -> the opaque code (a hex string) used everywhere
                                else in Aegis as the "entity id".

HONEST LIMITATION  (read this -- it is the crux)
------------------------------------------------
This is a KEYED HASH (HMAC): hash(consortium_key, fields). It is a deliberate
STAND-IN for the real thing. A keyed hash is deterministic and the consortium
key is shared by all members, which means a curious member bank can still take a
guessed identity, compute its code, and test it -- a "dictionary attack". Names
and birthdates are low-entropy and guessable, so a plain/keyed hash of them is
re-identifiable. Under GDPR this is why such a hash is still *personal data*.

>>> The production system MUST replace this function with an OBLIVIOUS PRF (the
    engine of the Stage-1 PSI protocol): a code computed with a key no single
    party can use alone, so nobody can brute-force guesses offline. The rest of
    Aegis is built to call this one function, so swapping in the OPRF is a
    drop-in change. <<<

ALSO: matching is EXACT. A typo or a changed address yields a different code and
a silent miss. Hence the strict canonicalisation below, and the preference for
stable, high-entropy fields (LEI for companies; national id + date of birth for
persons, where lawful) -- exactly the standardisation AMLA's RTS is producing.
"""

import hmac
import hashlib

# The fields every member bank agrees to feed in, in this fixed order.
# In production these are fixed by the consortium's data standard.
CANON_FIELDS = ("family_name", "given_name", "birth_date", "national_id")


def canonicalize(attrs: dict) -> bytes:
    """Normalise identity fields so cosmetic differences don't break matching."""
    parts = []
    for field in CANON_FIELDS:
        value = str(attrs.get(field, "")).strip().lower()
        value = " ".join(value.split())          # collapse internal whitespace
        parts.append(value)
    return "|".join(parts).encode("utf-8")


def shared_identifier(attrs: dict, consortium_key: bytes) -> str:
    """Return the opaque shared code for a person.

    STAND-IN for an oblivious PRF -- see the module docstring. Same attrs +
    same consortium_key -> same code at every bank; that is what enables
    cross-bank matching without exchanging raw personal data."""
    canon = canonicalize(attrs)
    return hmac.new(consortium_key, canon, hashlib.sha256).hexdigest()
