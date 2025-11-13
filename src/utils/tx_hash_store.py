import hashlib
from datetime import datetime
from typing import List, Dict, Optional

from .json_utils import load_json, save_json

HASHES_FILE = 'transaction_hashes.json'


def _ensure_list(data):
    return data if isinstance(data, list) else []


def hash_transaction_id(transaction_id: str) -> str:
    return hashlib.sha256(transaction_id.encode('utf-8')).hexdigest()


def record_transaction_hash(
    transaction_id: str,
    created_at = None,
    *,
    from_user_id: Optional[str] = None,
    to_user_id: Optional[str] = None,
    from_account_id: Optional[str] = None,
    to_account_id: Optional[str] = None,
    from_account_number: Optional[str] = None,
    to_account_number: Optional[str] = None,
) -> bool:
    """Hash a transaction_id and store it in a separate JSON database with metadata.

    Schema item: { transaction_id, hash, created_at, from_user_id?, to_user_id?, from_account_id?, to_account_id?, from_account_number?, to_account_number? }
    """
    # Convert datetime to ISO string if needed
    if created_at is None:
        created_ts = datetime.utcnow().isoformat()
    elif isinstance(created_at, datetime):
        created_ts = created_at.isoformat()
    else:
        created_ts = created_at
    
    entry = {
        'transaction_id': transaction_id,
        'hash': hash_transaction_id(transaction_id),
        'created_at': created_ts,
        'from_user_id': from_user_id,
        'to_user_id': to_user_id,
        'from_account_id': from_account_id,
        'to_account_id': to_account_id,
        'from_account_number': from_account_number,
        'to_account_number': to_account_number,
    }

    data = _ensure_list(load_json(HASHES_FILE))
    data.append(entry)
    return save_json(HASHES_FILE, data)


def list_transaction_hashes(limit: Optional[int] = None) -> List[Dict]:
    data = _ensure_list(load_json(HASHES_FILE))
    if limit is not None and limit >= 0:
        return data[-limit:]
    return data


def find_transaction_hash(transaction_id: str) -> Optional[Dict]:
    data = _ensure_list(load_json(HASHES_FILE))
    for item in data:
        if item.get('transaction_id') == transaction_id:
            return item
    return None
