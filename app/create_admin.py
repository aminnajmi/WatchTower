from getpass import getpass
from .auth import generate_password_hash
from .config import settings

password = getpass("Admin password: ")
confirm = getpass("Confirm password: ")
if password != confirm:
    raise SystemExit("Passwords do not match")

hashed, salt = generate_password_hash(password)
print("\nAdd these values to .env:\n")
print(f"ADMIN_PASSWORD_HASH={hashed}")
print(f"ADMIN_PASSWORD_SALT={salt}")
