import './styles.css';
import settoriHtml from './pages/settori.html?raw';
import marketHtml from './pages/market.html?raw';
import builderHtml from './pages/builder.html?raw';

import { initSettori } from './pages/settori.js';
import { initMarket } from './pages/market.js';
import { initBuilder } from './pages/builder.js';

document.getElementById('page-settori').innerHTML = settoriHtml;
document.getElementById('page-market').innerHTML = marketHtml;
document.getElementById('page-builder').innerHTML = builderHtml;

// Shared utilities map for ticker names
window.cryptoNamesMap = {
    "BTC": "Bitcoin", "ETH": "Ethereum", "XRP": "XRP", "SOL": "Solana", "DOGE": "Dogecoin",
    "ADA": "Cardano", "LINK": "Chainlink", "AVAX": "Avalanche", "DOT": "Polkadot", "UNI": "Uniswap",
    "SKY": "Sky", "NEAR": "Near", "ATOM": "Cosmos", "POL": "Polygon", "ALGO": "Algorand",
    "APT": "Aptos", "ARB": "Arbitrum", "STX": "Stacks", "INJ": "Injective", "TIA": "Celestia",
    "GRT": "The Graph", "OP": "Optimism", "SUI": "Sui", "XLM": "Stellar Lumens", "XPL": "XPL",
    "ONDO": "Ondo", "HBAR": "Hedera", "FIL": "Filecoin", "AAVE": "Aave", "ETC": "Ethereum Classic", "LTC": "Litecoin"
};

// Sidebar Logic
const sidebar = document.getElementById('sidebar');
const mobileMenuBtn = document.getElementById('mobile-menu-btn');
const sidebarBackdrop = document.getElementById('sidebar-backdrop');
const closeSidebarBtn = document.getElementById('close-sidebar-btn');

function toggleMobileMenu() {
    sidebar.classList.toggle('-translate-x-full');
    sidebarBackdrop.classList.toggle('hidden');
}

if (mobileMenuBtn) mobileMenuBtn.addEventListener('click', toggleMobileMenu);
if (closeSidebarBtn) closeSidebarBtn.addEventListener('click', toggleMobileMenu);
if (sidebarBackdrop) sidebarBackdrop.addEventListener('click', toggleMobileMenu);

document.querySelectorAll('.sidebar-btn').forEach(btn => {
    btn.addEventListener('click', function() {
        document.querySelectorAll('.sidebar-btn').forEach(b => {
            b.classList.remove('text-[#0050ff]', 'bg-blue-50', 'active');
            b.classList.add('text-slate-600', 'hover:bg-slate-50');
        });
        this.classList.remove('text-slate-600', 'hover:bg-slate-50');
        this.classList.add('text-[#0050ff]', 'bg-blue-50', 'active');

        const pageId = this.getAttribute('data-page');
        document.querySelectorAll('.page-content').forEach(page => {
            page.classList.add('hidden');
            page.classList.remove('block');
        });
        document.getElementById(pageId).classList.remove('hidden');
        document.getElementById(pageId).classList.add('block');
        window.scrollTo({ top: 0, behavior: 'instant' });

        if (window.innerWidth < 768) {
            sidebar.classList.add('-translate-x-full');
            sidebarBackdrop.classList.add('hidden');
        }

        setTimeout(() => { 
            window.dispatchEvent(new Event('resize')); 
            // Force Plotly resize for graphs in the visible page
            if (window.Plotly) {
                document.querySelectorAll(`#${pageId} .js-plotly-plot`).forEach(el => {
                    Plotly.Plots.resize(el);
                });
            }
        }, 100);
    });
});


// Load the different modules
async function initDashboard() {
    initSettori();
    initMarket();
    initBuilder();
}

initDashboard();
