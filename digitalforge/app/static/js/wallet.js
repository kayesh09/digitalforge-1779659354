/**
 * DigitalForge Wallet Integration
 * Handles Web3 wallet connections using ethers.js v6
 */

let walletProvider = null;
let walletSigner = null;
let walletAddress = null;

async function initWallet() {
    if (typeof window.ethereum === 'undefined') {
        console.log('MetaMask not installed');
        return false;
    }

    // Check if already connected
    try {
        const provider = new ethers.BrowserProvider(window.ethereum);
        const accounts = await provider.listAccounts();
        if (accounts.length > 0) {
            walletAddress = accounts[0].address;
            walletProvider = provider;
            updateWalletUI();
            return true;
        }
    } catch (err) {
        console.error('Wallet check failed:', err);
    }
    return false;
}

async function connectWallet() {
    if (typeof window.ethereum === 'undefined') {
        window.open('https://metamask.io/download/', '_blank');
        return;
    }

    try {
        const provider = new ethers.BrowserProvider(window.ethereum);

        // Request account access
        const accounts = await provider.send('eth_requestAccounts', []);
        walletAddress = accounts[0];
        walletProvider = provider;

        // Update backend with wallet address
        await updateBackendWallet(walletAddress);

        updateWalletUI();

        // Dispatch custom event for other components
        window.dispatchEvent(new CustomEvent('walletConnected', {
            detail: { address: walletAddress }
        }));

    } catch (err) {
        console.error('Wallet connection failed:', err);
        alert('Failed to connect wallet: ' + err.message);
    }
}

async function updateBackendWallet(address) {
    try {
        const response = await fetch('/api/user/wallet', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({ wallet_address: address })
        });

        if (!response.ok) {
            const error = await response.json();
            console.warn('Backend wallet update failed:', error);
        }
    } catch (err) {
        console.error('Backend update error:', err);
    }
}

async function disconnectWallet() {
    walletProvider = null;
    walletSigner = null;
    walletAddress = null;
    updateWalletUI();
}

function updateWalletUI() {
    // Find all wallet buttons on page
    const walletBtns = document.querySelectorAll('[data-wallet-btn]');

    walletBtns.forEach(btn => {
        if (walletAddress) {
            btn.innerHTML = `
                <div class="flex items-center gap-2">
                    <div class="w-2 h-2 bg-green-400 rounded-full"></div>
                    <span class="font-mono">${walletAddress.slice(0, 6)}...${walletAddress.slice(-4)}</span>
                </div>
            `;
            btn.onclick = disconnectWallet;
        } else {
            btn.innerHTML = `
                <div class="flex items-center gap-2">
                    <i data-lucide="wallet" class="w-4 h-4"></i>
                    <span>Connect Wallet</span>
                </div>
            `;
            btn.onclick = connectWallet;
        }
    });

    // Re-initialize icons if lucide is available
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }
}

async function getNetwork() {
    if (!walletProvider) return null;
    const network = await walletProvider.getNetwork();
    return network;
}

async function switchToBase() {
    if (!walletProvider) return;

    try {
        await window.ethereum.request({
            method: 'wallet_switchEthereumChain',
            params: [{ chainId: '0x2105' }] // Base mainnet
        });
    } catch (err) {
        // If chain not added, add it
        if (err.code === 4902) {
            await window.ethereum.request({
                method: 'wallet_addEthereumChain',
                params: [{
                    chainId: '0x2105',
                    chainName: 'Base Mainnet',
                    nativeCurrency: { name: 'ETH', symbol: 'ETH', decimals: 18 },
                    rpcUrls: ['https://mainnet.base.org'],
                    blockExplorerUrls: ['https://basescan.org']
                }]
            });
        }
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', initWallet);

// Listen for account changes
if (window.ethereum) {
    window.ethereum.on('accountsChanged', (accounts) => {
        if (accounts.length === 0) {
            disconnectWallet();
        } else {
            walletAddress = accounts[0];
            updateWalletUI();
        }
    });

    window.ethereum.on('chainChanged', () => {
        window.location.reload();
    });
}