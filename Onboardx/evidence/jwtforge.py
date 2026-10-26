import base64, json, hmac, hashlib

n = "xD4jfmL2QO0XY54lckzWGUjfV8aVSyoeh4unWs_m4CBvUzIYDH19lg0xci0dK1GBF_41fG0dgo0D67HOh1Cz-2-s4Ev6mulcEV5ldE-AmXRM2gE5UJzepARdDbZL24s1KLq1dQOyQG5T_HPgkcifa6bw3omtWzHVXI6WidhHHSGbJGcvbWKWVXVxDA6EDPMtOJpPYf3qKcO1GzWHS3zE-CNpqmBOQayqs-OtgUbZNOmEdGq_wDPajsKKKfzUNmGfzyeRJ9DX_wBTlpy_M7LVEtBcxORt9z-J9C7pjLT6nsFkLyzdeQ3UdYn-dQmPGbKQaYcztlt6PBwTNeaBLpGiyw"

def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

def b64dec(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))

# Build DER for RSAPublicKey
n_bytes = b64dec(n)
def der_len(x: int) -> bytes:
    if x < 128:
        return bytes([x])
    b = x.to_bytes((x.bit_length()+7)//8, 'big')
    return bytes([0x80 | len(b)]) + b

def der_int(x: bytes) -> bytes:
    x = x.lstrip(b"\x00") or b"\x00"
    if x[0] & 0x80:
        x = b"\x00" + x
    return b"\x02" + der_len(len(x)) + x

seq = der_int(n_bytes) + der_int(b"\x01")
body = b"\x30" + der_len(len(seq)) + seq
pem_body = base64.b64encode(body).decode()
pem = "-----BEGIN PUBLIC KEY-----\n" + "\n".join(pem_body[i:i+64] for i in range(0, len(pem_body), 64)) + "\n-----END PUBLIC KEY-----\n"
open("pub.pem","w").write(pem)
print(pem)

def make_token(claims, key, alg="HS256"):
    header = {"alg": alg, "kid": "prod-rsa-key-2026", "typ": "JWT"}
    h = b64url(json.dumps(header).encode())
    p = b64url(json.dumps(claims).encode())
    signing_input = f"{h}.{p}".encode()
    sig = hmac.new(key, signing_input, hashlib.sha256).digest()
    return f"{h}.{p}.{b64url(sig)}"

claims = {"sub": 4, "username": "hunter01", "role": "admin", "iat": 1791688987, "exp": 1791710587}
pub_key = open("pub.pem").read().encode()
tok = make_token(claims, pub_key)
print("Token:", tok)
