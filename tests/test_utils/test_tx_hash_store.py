import os
import uuid
from src.utils.tx_hash_store import record_transaction_hash, list_transaction_hashes, find_transaction_hash, HASHES_FILE
from src.utils.json_utils import load_json, save_json


def test_record_and_find_transaction_hash(tmp_path, monkeypatch):
    # Redirect data folder to temp directory by monkeypatching json_utils to use temp path
    # Since json_utils uses current_app when available, and falls back to default location,
    # we monkeypatch os.path.join in this module's scope by temporarily changing CWD
    cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        # ensure empty file
        save_json(HASHES_FILE, [])
        tx_id = str(uuid.uuid4())
        assert record_transaction_hash(tx_id, '2025-11-11T00:00:00') is True
        entry = find_transaction_hash(tx_id)
        assert entry is not None
        assert entry['transaction_id'] == tx_id
        hashes = list_transaction_hashes()
        assert any(h['transaction_id'] == tx_id for h in hashes)
    finally:
        os.chdir(cwd)
