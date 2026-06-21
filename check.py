# Run this to see what hash YOUR system generates:
import hashlib
pwd = "GhostWire@2026"
print(hashlib.sha256(pwd.encode()).hexdigest())