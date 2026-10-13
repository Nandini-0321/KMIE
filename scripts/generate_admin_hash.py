"""
scripts/generate_admin_hash.py
Utility script to generate a secure Werkzeug password hash for ADMIN_PASSWORD_HASH.
Usage:
    python scripts/generate_admin_hash.py
    python scripts/generate_admin_hash.py <password>
"""
import sys
from werkzeug.security import generate_password_hash


def main():
    if len(sys.argv) > 1:
        raw_password = sys.argv[1]
    else:
        try:
            import getpass
            raw_password = getpass.getpass("Enter password to hash: ")
        except Exception:
            raw_password = input("Enter password to hash: ")

    if not raw_password:
        print("Error: Password cannot be empty.")
        sys.exit(1)

    hashed = generate_password_hash(raw_password, method="scrypt")
    print("\nGenerated Password Hash:")
    print(hashed)
    print("\nCopy this value into your .env file as:")
    print(f"ADMIN_PASSWORD_HASH={hashed}\n")


if __name__ == "__main__":
    main()
