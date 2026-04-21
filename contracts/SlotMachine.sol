// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract SlotRoguelike {
    mapping(address => uint256) public balances;
    uint256 public constant SPIN_COST = 0.01 ether; // Coût d'un tirage (en $LUCK ou ETH natif)

    // Événement émis à chaque tirage pour que Python puisse l'écouter
    event SpinResult(address indexed player, bool won, uint256 amountWon);

    // Le joueur dépose des fonds dans la machine
    function deposit() public payable {
        balances[msg.sender] += msg.value;
    }

    // Fonction principale du tirage
    function spin() public {
        require(balances[msg.sender] >= SPIN_COST, "Fonds insuffisants pour jouer");
        
        // On déduit la mise
        balances[msg.sender] -= SPIN_COST;

        // MOCK ALÉATOIRE : Pour test local Ganache UNIQUEMENT. 
        // En production, utilisez Chainlink VRF.
        uint256 random = uint256(keccak256(abi.encodePacked(block.timestamp, msg.sender, block.prevrandao))) % 100;

        bool won = false;
        uint256 winAmount = 0;

        // Logique de base : 40% de chance de gagner (peut être modifié par des NFTs plus tard)
        if (random < 40) {
            won = true;
            winAmount = SPIN_COST * 2; // Multiplicateur x2 basique
            balances[msg.sender] += winAmount;
        }

        // On avertit l'interface (Python) du résultat
        emit SpinResult(msg.sender, won, winAmount);
    }

    // Le joueur "Cash-out" (Retire ses gains)
    function cashOut() public {
        uint256 amount = balances[msg.sender];
        require(amount > 0, "Rien a retirer");
        
        balances[msg.sender] = 0;
        payable(msg.sender).transfer(amount);
    }
}