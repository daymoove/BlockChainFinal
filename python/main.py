from web3 import Web3
import json
import time

# 1. Connexion à Ganache (par défaut sur le port 7545)
ganache_url = "http://127.0.0.1:7545"
w3 = Web3(Web3.HTTPProvider(ganache_url))

if w3.is_connected():
    print("Connecté à Ganache")
else:
    print("Erreur de connexion à Ganache")
    exit()

# 2. Configuration du compte (Prenez une adresse et sa clé privée depuis Ganache)
player_address = "PLACEHOLDER"
private_key = "PLACEHOLDER"

# 3. Configuration du contrat (Copiez depuis Remix après déploiement)
contract_address = "PLACEHOLDER"
try:
    with open('abi.json', 'r') as file:
        contract_abi = json.load(file) # Charge le contenu du fichier
        print("ABI chargée avec succès !")
except FileNotFoundError:
    print("Erreur : Le fichier abi.json est introuvable.")
    exit()
except json.JSONDecodeError:
    print("Erreur : Le fichier abi.json est mal formaté.")
    exit()

contract = w3.eth.contract(address=contract_address, abi=contract_abi)

def deposit_funds(amount_in_ether):
    print(f"\n--- Dépôt de {amount_in_ether} ETH ---")
    tx = contract.functions.deposit().build_transaction({
        'from': player_address,
        'value': w3.to_wei(amount_in_ether, 'ether'),
        'nonce': w3.eth.get_transaction_count(player_address),
        'gas': 2000000,
        'gasPrice': w3.to_wei('50', 'gwei')
    })
    
    signed_tx = w3.eth.account.sign_transaction(tx, private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    w3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"Dépôt réussi. Hash: {w3.to_hex(tx_hash)}")

def play_spin():
    print("\nLancement de la machine à sous...")
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
        
        # Récupération des logs de l'événement "SpinResult"
        logs = contract.events.SpinResult().process_receipt(receipt)
        if logs:
            result = logs[0]['args']
            if result['won']:
                print(f"GAGNÉ ! Gain : {w3.from_wei(result['amountWon'], 'ether')} ETH")
            else:
                print("PERDU ! Vous perdez votre mise.")
                
        # Affichage du solde actuel
        balance = contract.functions.balances(player_address).call()
        print(f"Solde interne actuel : {w3.from_wei(balance, 'ether')} ETH")
        
    except Exception as e:
        print(f"Erreur lors du tirage : {e}")

# --- Simulation de la boucle de jeu ---
if __name__ == "__main__":
    # 1. On dépose un peu de fonds au début de la "Run"
    deposit_funds(0.05)
    
    # 2. Le joueur décide de faire 3 tirages
    for i in range(3):
        play_spin()
        time.sleep(1) # Petite pause pour simuler l'animation
        
    print("\nFin du cycle. Le joueur doit maintenant choisir s'il Cash-out ou continue !")