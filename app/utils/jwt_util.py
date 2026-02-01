from jose import jwt
import secrets
import time

JWT_SECRET = "lfO8KbuHklqCLpYMczpxK5fm0fzcVVcAeRdrJEqN0Hk="

payload = {
    "iss": "supabase",
    "ref": "localhost",
    "role": "anon",
    "iat": int(time.time()),
    "exp": int(time.time()) + 3600 * 24 * 30,  # 30일 후 만료
}

# PyJWT 1.4.0: jwt.encode(payload, secret)
anon_key = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
print("ANON_KEY:", anon_key)

service_payload = dict(payload, role="service_role")
service_key = jwt.encode(service_payload, JWT_SECRET, algorithm="HS256")
print("SERVICE_ROLE_KEY:", service_key)
