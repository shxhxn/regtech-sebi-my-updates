"""
Tamper-evident audit log -- a hash chain over every significant pipeline event
(extraction run, verification run, diff run, operations build). Each entry's
hash depends on the previous entry's hash, so altering or deleting any past
entry breaks the chain from that point forward and is immediately detectable.
This is deterministic, local, and free -- no blockchain network needed, but
the same tamper-evidence property a regulator cares about.
"""
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from src.config import OUTPUT

LOG_PATH = OUTPUT / "audit_log.json"
GENESIS_HASH = "0" * 64

def _hash_entry(entry_without_hash: dict) -> str:
    blob = json.dumps(entry_without_hash, sort_keys=True, default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()

def load_log():
    if LOG_PATH.exists():
        return json.load(open(LOG_PATH))
    return []

def save_log(log):
    OUTPUT.mkdir(exist_ok=True)
    json.dump(log, open(LOG_PATH, "w"), indent=2)

def append_event(event_type: str, details: dict, timestamp: str = None):
    log = load_log()
    prev_hash = log[-1]["hash"] if log else GENESIS_HASH
    entry = {
        "index": len(log),
        "timestamp": timestamp or datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        "details": details,
        "prev_hash": prev_hash,
    }
    entry["hash"] = _hash_entry(entry)
    log.append(entry)
    save_log(log)
    return entry

def verify_chain():
    """Walks the whole chain and recomputes every hash. Returns (is_valid, first_broken_index)."""
    log = load_log()
    if not log:
        return True, None
    prev_hash = GENESIS_HASH
    for entry in log:
        if entry["prev_hash"] != prev_hash:
            return False, entry["index"]
        check = dict(entry)
        stored_hash = check.pop("hash")
        if _hash_entry(check) != stored_hash:
            return False, entry["index"]
        prev_hash = entry["hash"]
    return True, None
