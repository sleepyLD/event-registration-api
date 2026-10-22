"""Generate local credentials without printing or replacing existing secrets."""
from pathlib import Path
import secrets

path = Path(__file__).resolve().parents[1] / ".env"
try:
    with path.open("x", encoding="utf-8") as stream:
        stream.write("POSTGRES_DB=event_registration\nPOSTGRES_USER=event_app\n")
        stream.write("POSTGRES_PASSWORD=" + secrets.token_urlsafe(32) + "\n")
except FileExistsError:
    print("Existing .env preserved.")
else:
    print("Local .env created; credentials are not printed.")
