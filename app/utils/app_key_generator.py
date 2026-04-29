from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
import base64

# Generate RSA private key
private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

# Get the corresponding public key
public_key = private_key.public_key()

# Serialize the keys to PEM format
private_key_pem = private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption(),
)
public_key_pem = public_key.public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo,
)

# Encode keys to Base64
private_key_base64 = base64.b64encode(private_key_pem).decode("utf-8")
public_key_base64 = base64.b64encode(public_key_pem).decode("utf-8")

# Print or use the Base64-encoded keys
print("Base64-encoded RSA Private Key:")
print(private_key_base64)
print("Base64-encoded RSA Public Key:")
print(public_key_base64)
