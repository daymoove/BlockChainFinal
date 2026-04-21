from flask import Flask, render_template, jsonify, request
from web3 import Web3
import json

app = Flask(__name__)

# --- CONFIGURATION WEB3 ---
ganache_url = "http://127.0.0.1:7545"
w3 = Web3(Web3.HTTPProvider(ganache_url))

player_address = "PLACEHOLDER"
private_key = "PLACEHOLDER"
contract_address = "PLACEHOLDER"

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
        return jsonify({'error': str(e)}), 500

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
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Lance le serveur local sur le port 5000
    print("🚀 Serveur démarré sur http://127.0.0.1:5000")
    app.run(debug=True)