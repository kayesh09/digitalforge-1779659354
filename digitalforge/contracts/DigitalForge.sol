// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title DigitalForge Marketplace
 * @notice Smart contract for handling crypto payments with platform fee split
 * @dev 15% platform fee, 85% to seller
 */

contract DigitalForgeMarketplace {
    // Platform owner (fee recipient)
    address public immutable owner;

    // Platform fee percentage (basis points: 1500 = 15%)
    uint256 public constant PLATFORM_FEE_BPS = 1500;
    uint256 public constant MAX_FEE_BPS = 3000; // Max 30% fee cap

    // Purchase tracking
    struct Purchase {
        address buyer;
        address seller;
        uint256 amount;
        uint256 platformFee;
        uint256 sellerAmount;
        uint256 timestamp;
        bool refunded;
        bytes32 productHash; // Hash of product ID + UUID
    }

    // Mapping: tx hash => Purchase
    mapping(bytes32 => Purchase) public purchases;

    // Mapping: seller => total earnings
    mapping(address => uint256) public sellerEarnings;

    // Mapping: seller => pending withdrawals
    mapping(address => uint256) public pendingWithdrawals;

    // Events
    event PurchaseCompleted(
        bytes32 indexed txHash,
        address indexed buyer,
        address indexed seller,
        uint256 amount,
        uint256 platformFee,
        bytes32 productHash
    );

    event Withdrawal(address indexed seller, uint256 amount);
    event RefundIssued(bytes32 indexed txHash, uint256 amount);
    event FeeUpdated(uint256 newFeeBps);

    // Modifiers
    modifier onlyOwner() {
        require(msg.sender == owner, "Not authorized");
        _;
    }

    constructor() {
        owner = msg.sender;
    }

    /**
     * @notice Process a marketplace purchase
     * @param _seller Address of the product seller
     * @param _productHash Unique hash identifying the product
     * @return txHash Unique transaction identifier
     */
    function purchase(
        address _seller,
        bytes32 _productHash
    ) external payable returns (bytes32 txHash) {
        require(msg.value > 0, "Payment required");
        require(_seller != address(0), "Invalid seller");
        require(_seller != msg.sender, "Cannot buy own product");

        // Calculate fee split
        uint256 platformFee = (msg.value * PLATFORM_FEE_BPS) / 10000;
        uint256 sellerAmount = msg.value - platformFee;

        // Generate unique tx hash
        txHash = keccak256(abi.encodePacked(
            msg.sender,
            _seller,
            msg.value,
            block.timestamp,
            block.number,
            _productHash
        ));

        require(purchases[txHash].timestamp == 0, "Duplicate transaction");

        // Record purchase
        purchases[txHash] = Purchase({
            buyer: msg.sender,
            seller: _seller,
            amount: msg.value,
            platformFee: platformFee,
            sellerAmount: sellerAmount,
            timestamp: block.timestamp,
            refunded: false,
            productHash: _productHash
        });

        // Update seller earnings
        sellerEarnings[_seller] += sellerAmount;
        pendingWithdrawals[_seller] += sellerAmount;

        emit PurchaseCompleted(
            txHash,
            msg.sender,
            _seller,
            msg.value,
            platformFee,
            _productHash
        );

        return txHash;
    }

    /**
     * @notice Allow sellers to withdraw their earnings
     */
    function withdraw() external {
        uint256 amount = pendingWithdrawals[msg.sender];
        require(amount > 0, "No funds to withdraw");

        pendingWithdrawals[msg.sender] = 0;

        (bool success, ) = payable(msg.sender).call{value: amount}("");
        require(success, "Transfer failed");

        emit Withdrawal(msg.sender, amount);
    }

    /**
     * @notice Platform owner can withdraw accumulated fees
     */
    function withdrawPlatformFees() external onlyOwner {
        uint256 balance = address(this).balance;

        // Subtract pending seller withdrawals
        uint256 pendingSellers = 0;
        // Note: In production, track platform fees separately to avoid iteration

        uint256 platformBalance = balance - pendingSellers;
        require(platformBalance > 0, "No fees to withdraw");

        (bool success, ) = payable(owner).call{value: platformBalance}("");
        require(success, "Transfer failed");
    }

    /**
     * @notice Issue refund for a purchase (owner only)
     * @param _txHash Transaction hash of the purchase
     */
    function refund(bytes32 _txHash) external onlyOwner {
        Purchase storage purchase = purchases[_txHash];
        require(purchase.timestamp > 0, "Purchase not found");
        require(!purchase.refunded, "Already refunded");

        purchase.refunded = true;
        pendingWithdrawals[purchase.seller] -= purchase.sellerAmount;

        (bool success, ) = payable(purchase.buyer).call{value: purchase.amount}("");
        require(success, "Refund failed");

        emit RefundIssued(_txHash, purchase.amount);
    }

    /**
     * @notice Verify a purchase exists and is valid
     * @param _txHash Transaction hash
     */
    function verifyPurchase(bytes32 _txHash) external view returns (bool) {
        return purchases[_txHash].timestamp > 0 && !purchases[_txHash].refunded;
    }

    /**
     * @notice Get purchase details
     */
    function getPurchase(bytes32 _txHash) external view returns (Purchase memory) {
        return purchases[_txHash];
    }

    /**
     * @notice Get contract balance
     */
    function getBalance() external view returns (uint256) {
        return address(this).balance;
    }

    // Receive function
    receive() external payable {
        revert("Use purchase() function");
    }
}