// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract SlotRoguelike {
    mapping(address => uint256) public balances;
    uint256 public constant SPIN_COST = 0.01 ether;

    // L'événement inclut maintenant les 3 rouleaux (reels) !
    event SpinResult(address indexed player, uint8 reel1, uint8 reel2, uint8 reel3, uint256 amountWon);

    function deposit() public payable {
        balances[msg.sender] += msg.value;
    }

    function spin() public {
        require(balances[msg.sender] >= SPIN_COST, "Fonds insuffisants pour jouer");
        
        balances[msg.sender] -= SPIN_COST;

        // 1. Création d'une "graine" pseudo-aléatoire (Mock pour Ganache)
        uint256 randomHash = uint256(keccak256(abi.encodePacked(block.timestamp, msg.sender, block.prevrandao)));

        // 2. Extraction de 3 chiffres entre 1 et 7
        // (Modulo 7 donne 0 à 6. On ajoute 1 pour avoir 1 à 7)
        uint8 reel1 = uint8((randomHash % 7) + 1);
        uint8 reel2 = uint8(((randomHash / 100) % 7) + 1);
        uint8 reel3 = uint8(((randomHash / 10000) % 7) + 1);

        uint256 winAmount = 0;

        // 3. Condition de victoire : les 3 chiffres sont identiques
        if (reel1 == reel2 && reel2 == reel3) {
            
            // 4. Calcul des gains progressifs selon le chiffre
            if (reel1 == 1) winAmount = SPIN_COST * 2;       // 1-1-1 : x2
            else if (reel1 == 2) winAmount = SPIN_COST * 3;  // 2-2-2 : x3
            else if (reel1 == 3) winAmount = SPIN_COST * 4;  // 3-3-3 : x4
            else if (reel1 == 4) winAmount = SPIN_COST * 5;  // 4-4-4 : x5
            else if (reel1 == 5) winAmount = SPIN_COST * 7;  // 5-5-5 : x7
            else if (reel1 == 6) winAmount = SPIN_COST * 10; // 6-6-6 : x10
            else if (reel1 == 7) winAmount = SPIN_COST * 20; // 7-7-7 : x20 (Jackpot!)
            
            balances[msg.sender] += winAmount;
        }

        // On envoie les 3 chiffres et les gains dans la blockchain
        emit SpinResult(msg.sender, reel1, reel2, reel3, winAmount);
    }

    function cashOut() public {
        uint256 amount = balances[msg.sender];
        require(amount > 0, "Rien a retirer");
        
        balances[msg.sender] = 0;
        (bool success, ) = payable(msg.sender).call{value: amount}("");
        require(success, "Transfer failed");
    }
}