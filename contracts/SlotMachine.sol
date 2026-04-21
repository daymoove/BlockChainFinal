// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract SlotRoguelike {
    address public owner;
    mapping(address => uint256) public balances; // L'argent des joueurs
    uint256 public houseBalance;                 // La trésorerie du casino

    uint256 public constant SPIN_COST = 0.01 ether;

    event SpinResult(address indexed player, uint8 reel1, uint8 reel2, uint8 reel3, uint256 amountWon);

    // 1. Le constructeur (appelé une seule fois à la création)
    // Le mot "payable" permet d'envoyer des ETH lors du déploiement (le Bankroll)
    constructor() payable {
        owner = msg.sender;       // Celui qui déploie devient le patron
        houseBalance = msg.value; // Le dépôt initial devient la caisse du casino
    }

    // 2. Modificateur de sécurité
    modifier onlyOwner() {
        require(msg.sender == owner, "Seul le patron peut faire ca !");
        _;
    }

    function deposit() public payable {
        balances[msg.sender] += msg.value;
    }

    function spin() public {
        require(balances[msg.sender] >= SPIN_COST, "Fonds insuffisants pour jouer");
        
        // 3. TRANSFERT DE LA MISE : Du joueur vers le casino
        balances[msg.sender] -= SPIN_COST;
        houseBalance += SPIN_COST;

        uint256 randomHash = uint256(keccak256(abi.encodePacked(block.timestamp, msg.sender, block.prevrandao)));

        uint8 reel1 = uint8((randomHash % 7) + 1);
        uint8 reel2 = uint8(((randomHash / 100) % 7) + 1);
        uint8 reel3 = uint8(((randomHash / 10000) % 7) + 1);

        uint256 winAmount = 0;

        if (reel1 == reel2 && reel2 == reel3) {
            if (reel1 == 1) winAmount = SPIN_COST * 2;
            else if (reel1 == 2) winAmount = SPIN_COST * 3;
            else if (reel1 == 3) winAmount = SPIN_COST * 4;
            else if (reel1 == 4) winAmount = SPIN_COST * 5;
            else if (reel1 == 5) winAmount = SPIN_COST * 7;
            else if (reel1 == 6) winAmount = SPIN_COST * 10;
            else if (reel1 == 7) winAmount = SPIN_COST * 20;
            
            // 4. PAIEMENT DES GAINS : On vérifie que le casino a de quoi payer !
            require(houseBalance >= winAmount, "La banque a saute ! Pas assez de fonds.");
            
            // On transfère l'argent du casino vers le solde du joueur
            houseBalance -= winAmount;
            balances[msg.sender] += winAmount;
        }

        emit SpinResult(msg.sender, reel1, reel2, reel3, winAmount);
    }

    function cashOut() public {
        uint256 amount = balances[msg.sender];
        require(amount > 0, "Rien a retirer");
        
        balances[msg.sender] = 0;
        (bool success, ) = payable(msg.sender).call{value: amount}("");
        require(success, "Transfer failed");
    }

    // 5. NOUVELLE FONCTION : Le boss récupère les profits
    function withdrawProfits(uint256 amount) public onlyOwner {
        require(amount <= houseBalance, "Vous essayez de retirer plus que ce que possede le casino");
        
        houseBalance -= amount; // On déduit de la caisse
        
        // On envoie l'argent sur le portefeuille personnel du boss
        (bool success, ) = payable(owner).call{value: amount}("");
        require(success, "Transfer failed");
    }
}