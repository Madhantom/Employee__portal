from py_vapid import Vapid01
from cryptography.hazmat.primitives import serialization
import base64

vapid = Vapid01()
vapid.generate_keys()

def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")

public_raw = vapid.public_key.public_bytes(
    encoding=serialization.Encoding.X962,
    format=serialization.PublicFormat.UncompressedPoint,
)
private_raw = vapid.private_key.private_numbers().private_value.to_bytes(32, "big")

print("VAPID_PUBLIC_KEY  =", b64url(public_raw))
print("VAPID_PRIVATE_KEY =", b64url(private_raw))