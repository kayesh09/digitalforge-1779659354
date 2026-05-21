"""
Cryptographic utilities for the marketplace.
Handles server-side operations; client-side encryption is in JS.
"""
import hashlib
import hmac
import secrets
from base64 import b64encode, b64decode

def generate_encryption_key():
    """Generate a secure 256-bit key for AES encryption."""
    return secrets.token_bytes(32)

def generate_iv():
    """Generate a random 128-bit IV for AES-GCM."""
    return secrets.token_bytes(16)

def hash_file(filepath):
    """Calculate SHA-256 hash of file for integrity verification."""
    sha256 = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    return sha256.hexdigest()

def verify_hmac(message, signature, secret):
    """Verify HMAC signature for webhook/API security."""
    expected = hmac.new(
        secret.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)