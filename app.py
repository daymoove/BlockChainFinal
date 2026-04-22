from flask import Flask, render_template, jsonify, request
from web3 import Web3
import json
import ast

app = Flask(__name__)


def extract_blockchain_error(exc):
    """Return a short, user-friendly blockchain error message."""
    if not getattr(exc, 'args', None):
        return str(exc)

    first_arg = exc.args[0]

    # Common Ganache/Web3 format: ValueError({...})
    if isinstance(first_arg, dict):
        data = first_arg.get('data')
        if isinstance(data, dict):
            reason = data.get('reason')
            if reason:
                return reason

        message = first_arg.get('message')
        if isinstance(message, str) and message:
            marker = 'revert '
            if marker in message:
                return message.split(marker, 1)[1].strip()
            return message

    # Fallback when error is a raw string
    if isinstance(first_arg, str):
        # Some providers return a dict serialized as string.
        try:
            parsed = ast.literal_eval(first_arg)
            if isinstance(parsed, dict):
                data = parsed.get('data')
                if isinstance(data, dict):
                    reason = data.get('reason')
                    if reason:
                        return reason

                message = parsed.get('message')
                if isinstance(message, str) and message:
                    marker = 'revert '
                    if marker in message:
                        return message.split(marker, 1)[1].strip()
                    return message
        except Exception:
            pass

        marker = 'revert '
        if marker in first_arg:
            reason = first_arg.split(marker, 1)[1]
            # Keep only the revert reason, drop trailing serialized fields.
            reason = reason.split("',", 1)[0]
            reason = reason.split('\\n', 1)[0]
            reason = reason.strip(" {}[]'\"")
            if reason:
                return reason
        return first_arg

    return str(exc)

# --- CONFIGURATION WEB3 ---
ganache_url = "http://127.0.0.1:7545"
w3 = Web3(Web3.HTTPProvider(ganache_url))

player_address = "0x3D987b5C6956599Beefc7A39161Fa4e5B647631b"
private_key = "0x76d04b221738e945c1f8596b93f49e692fdc8e278c42c683b63cae99572e4fc7"
contract_address = "0xc3FA5b8114fE14E8D91926Dd8A988A9eEBC1e82c"

# Adresse MetaMask du joueur réel (renseignée via /api/connect).
user_address = None

# Chargement de l'ABI
with open('abi.json', 'r') as file:
    contract_abi = json.load(file)
contract = w3.eth.contract(address=contract_address, abi=contract_abi)

# --- ROUTES DE L'API WEB ---

@app.route('/')
def home():
    # Sert la page HTML qui se trouve dans le dossier 'templates'
    return render_template('index.html')

@app.route('/api/balance', methods=['GET'])
def get_balance():
    balance = contract.functions.balances(player_address).call()
    return jsonify({'balance': str(w3.from_wei(balance, 'ether'))})

@app.route('/api/deposit', methods=['POST'])
def deposit():
    data = request.json
    amount = float(data.get('amount', 0))
    if amount <= 0:
        return jsonify({'error': 'Montant invalide'}), 400

    try:
        tx = contract.functions.deposit().build_transaction({
            'from': player_address,
            'value': w3.to_wei(amount, 'ether'),
            'nonce': w3.eth.get_transaction_count(player_address),
            'gas': 2000000,
            'gasPrice': w3.to_wei('50', 'gwei')
        })
        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        w3.eth.wait_for_transaction_receipt(tx_hash)
        return jsonify({'success': True, 'message': f'Dépôt de {amount} ETH réussi'})
    except Exception as e:
        return jsonify({'error': extract_blockchain_error(e)}), 500

@app.route('/api/spin', methods=['POST'])
def spin():
    try:
        tx = contract.functions.spin().build_transaction({
            'from': player_address,
            'nonce': w3.eth.get_transaction_count(player_address),
            'gas': 2000000,
            'gasPrice': w3.to_wei('50', 'gwei')
        })
        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        

        # Lecture des logs pour récupérer les 3 chiffres et les gains
        logs = contract.events.SpinResult().process_receipt(receipt)
        if logs:
            result = logs[0]['args']
            amount_won = w3.from_wei(result['amountWon'], 'ether')
            
            return jsonify({
                'success': True, 
                'reel1': result['reel1'],  # On récupère le 1er chiffre
                'reel2': result['reel2'],  # On récupère le 2ème chiffre
                'reel3': result['reel3'],  # On récupère le 3ème chiffre
                'amountWon': str(amount_won),
                'won': amount_won > 0      # C'est gagné si le montant est supérieur à 0
            })
        return jsonify({'error': 'Aucun log trouvé'}), 500
    except Exception as e:
        return jsonify({'error': extract_blockchain_error(e)}), 500

@app.route('/api/cashout', methods=['POST'])
def cashout():
    try:
        tx = contract.functions.cashOut().build_transaction({
            'from': player_address,
            'nonce': w3.eth.get_transaction_count(player_address),
            'gas': 2000000,
            'gasPrice': w3.to_wei('50', 'gwei')
        })
        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        w3.eth.wait_for_transaction_receipt(tx_hash)
        return jsonify({'success': True, 'message': 'Cash-out effectué'})
    except Exception as e:
        return jsonify({'error': extract_blockchain_error(e)}), 500

@app.route('/api/gameAccount', methods=['GET'])
def game_account():
    """Adresse du compte de jeu (proxy) — le front y enverra l'ETH via MetaMask."""
    return jsonify({'address': player_address})


@app.route('/api/connect', methods=['POST'])
def connect_user():
    """Le front déclare ici l'adresse MetaMask du joueur après connexion."""
    global user_address
    data = request.json or {}
    addr = (data.get('address') or '').strip()
    if not addr:
        return jsonify({'error': 'Adresse requise'}), 400
    try:
        user_address = Web3.to_checksum_address(addr)
        return jsonify({
            'success': True,
            'userAddress': user_address,
            'gameAccount': player_address,
        })
    except Exception:
        return jsonify({'error': 'Adresse invalide'}), 400


@app.route('/api/cashoutToUser', methods=['POST'])
def cashout_to_user():
    """
    1) Retire le solde du contract vers le compte de jeu (contract.cashOut()).
    2) Renvoie ces ETH du compte de jeu vers l'adresse MetaMask du joueur.
    """
    global user_address
    if not user_address:
        return jsonify({'error': 'Aucun joueur connecté via MetaMask'}), 400
    try:
        # Montant à transférer : le solde courant du compte de jeu dans le contract.
        amount = contract.functions.balances(player_address).call()
        if amount == 0:
            return jsonify({'error': 'Rien a retirer'}), 400

        # 1. CashOut : contract -> compte de jeu
        tx = contract.functions.cashOut().build_transaction({
            'from': player_address,
            'nonce': w3.eth.get_transaction_count(player_address),
            'gas': 2000000,
            'gasPrice': w3.to_wei('50', 'gwei')
        })
        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        w3.eth.wait_for_transaction_receipt(tx_hash)

        # 2. Transfert : compte de jeu -> MetaMask du joueur
        transfer = {
            'from': player_address,
            'to': user_address,
            'value': amount,
            'nonce': w3.eth.get_transaction_count(player_address),
            'gas': 21000,
            'gasPrice': w3.to_wei('50', 'gwei'),
            'chainId': w3.eth.chain_id,
        }
        signed_transfer = w3.eth.account.sign_transaction(transfer, private_key)
        transfer_hash = w3.eth.send_raw_transaction(signed_transfer.raw_transaction)
        w3.eth.wait_for_transaction_receipt(transfer_hash)

        return jsonify({
            'success': True,
            'amount': str(w3.from_wei(amount, 'ether')),
            'to': user_address,
        })
    except Exception as e:
        return jsonify({'error': extract_blockchain_error(e)}), 500


if __name__ == '__main__':
    # Lance le serveur local sur le port 5000
    print("🚀 Serveur démarré sur http://127.0.0.1:5000")
    app.run(debug=True)