from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from src.managers.AccountManager import AccountManager
from src.utils.jwt_auth import admin_required, get_current_user
from src.utils.tx_hash_store import list_transaction_hashes, find_transaction_hash

account_bp = Blueprint('accounts', __name__)
account_manager = AccountManager()

@account_bp.route('', methods=['GET'])
@jwt_required()
def get_accounts():
    currUser = get_current_user()
    # admin can get access to ALL accs | regular users only get their accs
    if currUser['role'] == 'admin' and request.args.get('all') == 'true': accounts = account_manager.get_all_accounts()
    else: accounts = account_manager.get_user_accounts(currUser['user_id'])
    res = []
    for acc in accounts: res.append(acc.to_dict())
    return jsonify(accounts=res), 200


@account_bp.route('/<account_id>', methods=['GET'])
@jwt_required()
def get_account(account_id):
    currUser = get_current_user()
    acc = account_manager.get_account_by_id(account_id)
    if not acc: return jsonify(error="account not found"), 404
    if currUser['role'] != 'admin' and acc.user_id != currUser['user_id']: return jsonify(error="unauthorized access to account"), 403 # check if user has access to this account
    return jsonify(acc.to_dict()), 200


@account_bp.route('', methods=['POST'])
@jwt_required()
def create_account():
    currUser = get_current_user()
    data = request.get_json()
    required_fields = ['account_type']
    for ff in required_fields:
        if ff not in data: return jsonify(error=f"missing required field: {ff}"), 400

    if 'user_id' not in data or currUser['role'] != 'admin': data['user_id'] = currUser['user_id'] # set user_id to current user unless specified by admin
    try:
        accId = account_manager.create_account(data)
        if accId: return jsonify(message="account created successfully", account_id=accId),201
        else: return jsonify(error="failed to create account"), 500
    except ValueError as e: return jsonify(error=str(e)), 400


@account_bp.route('/<account_id>', methods=['PUT'])
@jwt_required()
def update_account(account_id):
    currUser = get_current_user()
    acc = account_manager.get_account_by_id(account_id)
    if not acc: return jsonify(error="account not found"), 404
    if currUser['role'] != 'admin' and acc.user_id != currUser['user_id']: return jsonify(error="unauthorized access to account"), 403 # check if user has access to this acc

    data = request.get_json()
    if 'balance' in data: del data['balance'] # dont allow changing balance directly
    res = account_manager.update_account(account_id, data)
    if res: return jsonify(message="account updated successfully"),200
    else: return jsonify(error="failed to update account"),500


@account_bp.route('/<account_id>/close', methods=['POST'])
@jwt_required()
def close_account(account_id):
    currUser = get_current_user()
    acc = account_manager.get_account_by_id(account_id)
    if not acc: return jsonify(error="account not found"), 404
    if currUser['role'] != 'admin' and acc.user_id != currUser['user_id']: return jsonify(error="unauthorized access to account"),403 # check if user has access to this acc

    try:
        res = account_manager.close_account(account_id)
        if res: return jsonify(message="account closed successfully"),200
        else: return jsonify(error="failed to close account"), 500
    except ValueError as e: return jsonify(error=str(e)), 400


@account_bp.route('/<account_id>/deposit', methods=['POST'])
@jwt_required()
def deposit(account_id):
    currUser = get_current_user()
    acc = account_manager.get_account_by_id(account_id)
    if not acc: return jsonify(error="account not found"),404
    if currUser['role'] != 'admin' and acc.user_id != currUser['user_id']: return jsonify(error="unauthorized access to account"), 403

    data = request.get_json()
    if 'amount' not in data: return jsonify(error="amount is required"), 400
    try:
        amount = float(data['amount'])
        desc = data.get('description')
        newblnc, tx_id = account_manager.deposit(account_id,amount,desc)
        hash_entry = find_transaction_hash(tx_id)
        if newblnc is not None: return jsonify(message="deposit successful", balance=newblnc, transaction_id=tx_id, transaction_hash=hash_entry['hash'] if hash_entry else None), 200
        else: return jsonify(error="failed to process deposit"), 500
    except ValueError as e: return jsonify(error=str(e)), 400


@account_bp.route('/<account_id>/withdraw', methods=['POST'])
@jwt_required()
def withdraw(account_id):
    currUser = get_current_user()
    acc = account_manager.get_account_by_id(account_id)
    if not acc: return jsonify(error="account not found"), 404
    if currUser['role'] != 'admin' and acc.user_id != currUser['user_id']: return jsonify(error="unauthorized access to account"), 403

    data = request.get_json()
    if 'amount' not in data: return jsonify(error="amount is required"), 400
    try:
        amount = float(data['amount'])
        desc = data.get('description')
        newblnc, tx_id = account_manager.withdraw(account_id, amount, desc)
        hash_entry = find_transaction_hash(tx_id)
        if newblnc is not None: return jsonify(message="withdrawal successful", balance=newblnc, transaction_id=tx_id, transaction_hash=hash_entry['hash'] if hash_entry else None),200
        else: return jsonify(error="failed to process withdrawal"),500
    except ValueError as e: return jsonify(error=str(e)), 400


@account_bp.route('/transfer', methods=['POST'])
@jwt_required()
def transfer():
    currUser = get_current_user()
    data = request.get_json()
    # Support both IDs and account numbers; IDs take precedence if provided
    if 'from_account_id' in data:
        from_account = account_manager.get_account_by_id(data['from_account_id'])
    elif 'from_account_number' in data:
        from_account = account_manager.get_account_by_number(data['from_account_number'])
        if from_account:
            data['from_account_id'] = from_account.account_id
    else:
        return jsonify(error="missing required field: from_account_id or from_account_number"), 400

    # Resolve destination
    if 'to_account_id' in data:
        to_account = account_manager.get_account_by_id(data['to_account_id'])
    elif 'to_account_number' in data:
        to_account = account_manager.get_account_by_number(data['to_account_number'])
        if to_account:
            data['to_account_id'] = to_account.account_id
    else:
        return jsonify(error="missing required field: to_account_id or to_account_number"), 400

    if not from_account: return jsonify(error="source account not found"), 404
    if not to_account: return jsonify(error="destination account not found"), 404
    if from_account.account_id == to_account.account_id:
        return jsonify(error="cannot transfer to the same account"), 400
    if currUser['role'] != 'admin' and from_account.user_id != currUser['user_id']:
        return jsonify(error="unauthorized access to source account"), 403

    try:
        amount = float(data['amount'])
        desc = data.get('description')
        tx_id = account_manager.transfer(data['from_account_id'], data['to_account_id'], amount, desc)
        hash_entry = find_transaction_hash(tx_id)
        if tx_id:
            return jsonify(
                message="transfer successful",
                transaction_id=tx_id,
                transaction_hash=hash_entry['hash'] if hash_entry else None,
                to_account_id=data.get('to_account_id'),
                to_account_number=data.get('to_account_number')
            ), 200
        else: return jsonify(error="failed to process transfer"),500
    except ValueError as e: return jsonify(error=str(e)), 400


@account_bp.route('/multi-transfer', methods=['POST'])
@jwt_required()
def multi_transfer():
    currUser = get_current_user()
    data = request.get_json()
    required_fields = ['from_account_id', 'transfers']
    for ff in required_fields:
        if ff not in data:
            return jsonify(error=f"missing required field: {ff}"), 400
    from_account = account_manager.get_account_by_id(data['from_account_id'])
    if not from_account:
        return jsonify(error="source account not found"), 404
    if currUser['role'] != 'admin' and from_account.user_id != currUser['user_id']:
        return jsonify(error="unauthorized access to source account"), 403
    try:
        desc = data.get('description')
        results = account_manager.multi_transfer(data['from_account_id'], data['transfers'], desc)
        return jsonify(message="multi-transfer successful", transactions=results), 200
    except ValueError as e:
        return jsonify(error=str(e)), 400

@account_bp.route('/transfer-by-number', methods=['POST'])
@jwt_required()
def transfer_by_account_number():
    currUser = get_current_user()
    data = request.get_json()
    required_fields = ['from_account_id', 'to_account_number', 'amount']
    for ff in required_fields:
        if ff not in data:
            return jsonify(error=f"missing required field: {ff}"), 400
    from_account = account_manager.get_account_by_id(data['from_account_id'])
    if not from_account:
        return jsonify(error="source account not found"), 404
    if currUser['role'] != 'admin' and from_account.user_id != currUser['user_id']:
        return jsonify(error="unauthorized access to source account"), 403
    dest = account_manager.get_account_by_number(data['to_account_number'])
    if not dest:
        return jsonify(error="destination account not found"), 404
    if dest.account_id == from_account.account_id:
        return jsonify(error="cannot transfer to the same account"), 400
    try:
        amount = float(data['amount'])
        desc = data.get('description') or 'transfer by account number'
        tx_id = account_manager.transfer(from_account.account_id, dest.account_id, amount, desc)
        hash_entry = find_transaction_hash(tx_id)
        return jsonify(message="transfer successful", transaction_id=tx_id, transaction_hash=hash_entry['hash'] if hash_entry else None, to_account_id=dest.account_id, to_account_number=dest.account_number), 200
    except ValueError as e:
        return jsonify(error=str(e)), 400


# ===================== ADMIN HASH VIEW ROUTES ===================== #
@account_bp.route('/transaction-hashes', methods=['GET'])
@jwt_required()
@admin_required
def get_transaction_hashes():
    limit = request.args.get('limit', type=int)
    hashes = list_transaction_hashes(limit=limit)
    return jsonify(hashes=hashes, count=len(hashes)), 200


@account_bp.route('/transaction-hashes/<transaction_id>', methods=['GET'])
@jwt_required()
@admin_required
def get_transaction_hash(transaction_id):
    entry = find_transaction_hash(transaction_id)
    if not entry:
        return jsonify(error="transaction hash not found"), 404
    return jsonify(entry), 200


@account_bp.route('/<account_id>/transactions', methods=['GET'])
@jwt_required()
def get_account_transactions(account_id):
    currUser = get_current_user()
    acc = account_manager.get_account_by_id(account_id)
    if not acc: return jsonify(error="account not found"), 404
    if currUser['role'] != 'admin' and acc.user_id != currUser['user_id']: return jsonify(error="unauthorized access to account"), 403
    transcs = account_manager.get_transactions(account_id=account_id)
    res = []
    for tr in transcs: res.append(tr.to_dict())
    return jsonify(transactions=res),200


@account_bp.route('/user/transactions', methods=['GET'])
@jwt_required()
def get_user_transactions():
    currUser = get_current_user()
    transcs = account_manager.get_transactions(user_id=currUser['user_id'])
    res = []
    for tr in transcs: res.append(tr.to_dict())
    return jsonify(transactions=res),200