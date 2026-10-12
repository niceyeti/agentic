import os
import json
import logging
from pathlib import Path

from pydantic import SecretStr

logging.basicConfig(level=os.environ.get("LOG_LEVEL", "WARNING").upper())
logger = logging.getLogger()


def load_from_cred_dict(path: Path | str, key: str) -> SecretStr:
    if not isinstance(path, Path):
        path = Path(path)

    if not path.exists():
        raise ValueError(f"Cred path not found: {path}")

    creds = json.loads(path.read_text(encoding="utf8"))
    if key not in creds:
        raise ValueError(f"Key {key} not found in keys: ", creds.keys())

    return SecretStr(creds[key])


def load_cred(key: str) -> SecretStr:
    """load_cred is an operational pattern, not a code pattern. This attempts
    to find a json file of kvp-formatted credentials at a canonical set of
    locations."""

    local_cred_path = Path("./.cred")
    if local_cred_path.exists():
        return load_from_cred_dict(local_cred_path, key)

    canonical_cred_path = Path("/var/run/secrets/.cred")
    logger.info(
        f"Local cred path {local_cred_path} not found, backing up to {canonical_cred_path}"
    )
    if not canonical_cred_path.exists():
        raise ValueError(
            f"Creds not found at {local_cred_path} nor canonical {canonical_cred_path} using pwd={Path(".").absolute()}."
            + "Place credentials at either path, secure file ownership/permissions and ensure they are not committed and docker-ignored."
        )

    return load_from_cred_dict(canonical_cred_path, key)
