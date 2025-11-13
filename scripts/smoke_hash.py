import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src.utils.tx_hash_store import record_transaction_hash, list_transaction_hashes, find_transaction_hash

record_transaction_hash('test-tx-1', '2025-11-11T00:00:00')
record_transaction_hash('test-tx-2', '2025-11-11T00:01:00')

hashes = list_transaction_hashes()
print('count', len(hashes))
print('last', hashes[-1]['transaction_id'])
print('find1', find_transaction_hash('test-tx-1') is not None)
