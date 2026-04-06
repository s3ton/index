(function() {
const sidebar = document.getElementById('sidebar');
const mobileMenuBtn = document.getElementById('mobile-menu-btn');
const sidebarBackdrop = document.getElementById('sidebar-backdrop');

const closeSidebarBtn = document.getElementById('close-sidebar-btn');

function toggleMobileMenu() {
sidebar.classList.toggle('-translate-x-full');
sidebarBackdrop.classList.toggle('hidden');
}

mobileMenuBtn.addEventListener('click', toggleMobileMenu);
closeSidebarBtn.addEventListener('click', toggleMobileMenu);
sidebarBackdrop.addEventListener('click', toggleMobileMenu);

// --- LOGICA MENU LATERALE ---
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

setTimeout(() => { window.dispatchEvent(new Event('resize')); }, 50);
});
});

// --- LOGICA SWITCH TAB SETTORI ---
document.querySelectorAll('.tab-btn').forEach(btn => {
btn.addEventListener('click', function() {
document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
this.classList.add('active');

document.querySelectorAll('.tab-content').forEach(content => {
content.classList.remove('active');
});

const tabId = this.getAttribute('data-tab');
document.getElementById(tabId).classList.add('active');
window.scrollTo({ top: 0, behavior: 'instant' });


setTimeout(() => {
window.dispatchEvent(new Event('resize'));
if(window.Plotly) {
const charts = document.querySelectorAll(`#${tabId} .js-plotly-plot`);
charts.forEach(chart => Plotly.Plots.resize(chart));
}
}, 50);
});
});

let cryptoNamesMap = {
    "BTC": "Bitcoin", "ETH": "Ethereum", "XRP": "XRP", "SOL": "Solana", "DOGE": "Dogecoin",
    "ADA": "Cardano", "LINK": "Chainlink", "AVAX": "Avalanche", "DOT": "Polkadot", "UNI": "Uniswap",
    "SKY": "Sky", "NEAR": "Near", "ATOM": "Cosmos", "POL": "Polygon", "ALGO": "Algorand",
    "APT": "Aptos", "ARB": "Arbitrum", "STX": "Stacks", "INJ": "Injective", "TIA": "Celestia",
    "GRT": "The Graph", "OP": "Optimism", "SUI": "Sui", "XLM": "Stellar Lumens", "XPL": "XPL",
    "ONDO": "Ondo", "HBAR": "Hedera", "FIL": "Filecoin", "AAVE": "Aave", "ETC": "Ethereum Classic", "LTC": "Litecoin"
};

async function loadCryptoNames() {
    // I nomi sono ora definiti localmente per evitare errori nel caricamento dei file esterni
}

const performanceChartEl = document.getElementById('performance-chart');
const compositionChartEl = document.getElementById('composition-chart');
const techPerformanceChartEl = document.getElementById('tech-performance-chart');
const techWeightsChartEl = document.getElementById('tech-weights-chart');
const extra1PerfChartEl = document.getElementById('extra1-performance-chart');
const extra1CompChartEl = document.getElementById('extra1-composition-chart');
const extra2PerfChartEl = document.getElementById('extra2-performance-chart');
const extra2WeightsChartEl = document.getElementById('extra2-weights-chart');

function decodePlotlyBdata(traceData) {
if (!traceData || typeof traceData !== 'object' || !traceData.bdata) return traceData;
try {
const b64 = traceData.bdata.replace(/[^A-Za-z0-9+/=]/g, "");
const binaryString = window.atob(b64);
const len = binaryString.length;
const bytes = new Uint8Array(len);
for (let i = 0; i < len; i++) bytes[i] = binaryString.charCodeAt(i);
const dataView = new DataView(bytes.buffer);
const arr = [];
const isLittleEndian = true;
if (traceData.dtype === 'f8' || traceData.dtype === '<f8') {
const maxLen = len - (len % 8);
for (let i = 0; i < maxLen; i += 8) arr.push(dataView.getFloat64(i, isLittleEndian));
} else if (traceData.dtype === 'f4' || traceData.dtype === '<f4') {
const maxLen = len - (len % 4);
for (let i = 0; i < maxLen; i += 4) arr.push(dataView.getFloat32(i, isLittleEndian));
} else if (traceData.dtype === 'i4' || traceData.dtype === '<i4') {
const maxLen = len - (len % 4);
for (let i = 0; i < maxLen; i += 4) arr.push(dataView.getInt32(i, isLittleEndian));
} else {
return traceData;
}

if (traceData.shape) {
const shape = traceData.shape.split(',').map(s => parseInt(s.trim(), 10));
if (shape.length === 2) {
const rows = shape[0];
const cols = shape[1];
const reshaped = [];
for (let r = 0; r < rows; r++) {
reshaped.push(arr.slice(r * cols, (r + 1) * cols));
}
return reshaped;
}
}
return arr;
} catch (e) {
console.error("Avviso: Impossibile decodificare i dati bdata.", e);
return traceData;
}
}

function processTraces(dataArray) {
if (!Array.isArray(dataArray)) return;
dataArray.forEach(trace => {
if (trace.x) trace.x = decodePlotlyBdata(trace.x);
if (trace.y) trace.y = decodePlotlyBdata(trace.y);
if (trace.z) trace.z = decodePlotlyBdata(trace.z);
if (trace.customdata) trace.customdata = decodePlotlyBdata(trace.customdata);
});
}

// Modifica 3: Gestione Margini e autosize dinamico per dispositivi mobili/tablet/desktop
window.getLayoutWithMargins = function(layout) {
const isMobile = window.innerWidth < 640;
const isTablet = window.innerWidth >= 640 && window.innerWidth < 1024;
const isHeatmap = layout._isHeatmap || false;

const newLayout = {
...layout,
autosize: true, 
margin: { 
    l: isHeatmap ? (isMobile ? 32 : 55) : 0, 
    r: isMobile ? (isHeatmap ? 38 : 5) : (isHeatmap ? 45 : 10), 
    t: isMobile ? 30 : 40, 
    b: isMobile ? 60 : 70,
    pad: 0
},
plot_bgcolor: "transparent",
paper_bgcolor: "transparent",
font: { color: '#475569' },
hoverlabel: { bgcolor: "#ffffff", bordercolor: "#e2e8f0", font: { size: 12, color: "#0f172a" } },
legend: {
    orientation: 'h',
    y: -0.15,
    yanchor: 'top',
    x: 0,
    xanchor: 'left',
    bgcolor: 'transparent',
    borderwidth: 0,
    font: { size: 12, color: '#475569' }
}
};

if (newLayout.yaxis) {
    newLayout.yaxis = { ...newLayout.yaxis, ticklabelposition: isHeatmap ? "outside" : "inside", tickfont: { color: "#94a3b8" }, title: { text: '' }, automargin: false, ticklen: 2 };
} else {
    newLayout.yaxis = { ticklabelposition: isHeatmap ? "outside" : "inside", tickfont: { color: "#94a3b8" }, title: { text: '' }, automargin: false, ticklen: 2 };
}

if (newLayout.xaxis) {
    newLayout.xaxis = { ...newLayout.xaxis, title: { text: '' }, rangeslider: { visible: false }, automargin: false, ticklen: 2 };
} else {
    newLayout.xaxis = { title: { text: '' }, rangeslider: { visible: false }, automargin: false, ticklen: 2 };
}

return newLayout;
}

// Modifica 3: Resize istantaneo di tutti i grafici visibili
window.addEventListener('resize', () => {
if(window.Plotly) {
const activeCharts = document.querySelectorAll('.page-content.block .tab-content.active .js-plotly-plot, .page-content.block > .js-plotly-plot, #market-analytics-charts-container .js-plotly-plot, #page-builder .js-plotly-plot');
activeCharts.forEach(chart => Plotly.Plots.resize(chart));
}
});

function buildAllocationTable(containerId, allocationObj, mcapObj = null) {
const container = document.getElementById(containerId);
if (!container || !allocationObj) return;
let html = `
<div class="mt-8 bg-white border border-slate-200 rounded-2xl overflow-hidden shadow-sm">
<div class="overflow-x-auto w-full">
<table class="min-w-full text-sm text-left">
<thead class="bg-slate-50 border-b border-slate-200">
<tr>
<th scope="col" class="px-3 md:px-6 py-3 md:py-4 text-[10px] md:text-xs font-bold text-slate-500 uppercase tracking-wider">Ticker</th>
<th scope="col" class="px-3 md:px-6 py-3 md:py-4 text-[10px] md:text-xs font-bold text-slate-500 uppercase tracking-wider">Asset</th>
<th scope="col" class="px-3 md:px-6 py-3 md:py-4 text-[10px] md:text-xs font-bold text-slate-500 uppercase tracking-wider text-right">Market Cap</th>
<th scope="col" class="px-3 md:px-6 py-3 md:py-4 text-[10px] md:text-xs font-bold text-slate-500 uppercase tracking-wider text-right">Allocazione</th>
<th scope="col" class="px-3 md:px-6 py-3 md:py-4 text-[10px] md:text-xs font-bold text-slate-500 uppercase tracking-wider hidden sm:table-cell"></th>
</tr>
</thead>
<tbody class="divide-y divide-slate-100">
`;

const sortedAssets = Object.entries(allocationObj).sort((a, b) => b[1] - a[1]);
for (const [asset, weight] of sortedAssets) {
const tickerName = asset.split('-')[0].replace(/\d+$/, '');
const fullName = cryptoNamesMap[asset] || tickerName;
const weightPct = (weight * 100).toLocaleString('it-IT', {minimumFractionDigits: 2, maximumFractionDigits: 2}) + '%';
let mcapDisplay = "";
if (mcapObj && mcapObj[asset]) mcapDisplay = '€ ' + (mcapObj[asset] / 1e9).toLocaleString('it-IT', {minimumFractionDigits: 2, maximumFractionDigits: 2}) + ' B';
else { const mockMcap = (Math.random() * 40 + 2).toFixed(2); mcapDisplay = `€ ${mockMcap.replace('.', ',')} B`; }
const barWidth = Math.min((weight * 100), 100).toFixed(2) + '%';
html += `
<tr class="hover:bg-slate-50/80 transition-colors group">
<td class="px-3 md:px-6 py-3 md:py-4 whitespace-nowrap font-bold text-slate-600 text-xs md:text-sm">${tickerName}</td>
<td class="px-3 md:px-6 py-3 md:py-4 whitespace-nowrap font-semibold text-[#0a1b39] text-xs md:text-sm">${fullName}</td>
<td class="px-3 md:px-6 py-3 md:py-4 whitespace-nowrap text-right font-medium text-slate-600 text-xs md:text-sm">${mcapDisplay}</td>
<td class="px-3 md:px-6 py-3 md:py-4 whitespace-nowrap text-right font-bold text-[#0050ff] text-xs md:text-sm">${weightPct}</td>
<td class="px-3 md:px-6 py-3 md:py-4 whitespace-nowrap w-32 md:w-48 hidden sm:table-cell">
<div class="w-full bg-slate-100 rounded-full h-2 overflow-hidden"><div class="bg-[#0050ff] h-2 rounded-full" style="width: ${barWidth}"></div></div>
</td>
</tr>
`;
}
html += `</tbody></table></div></div>`;
container.innerHTML = html;
}

function buildReturnsTable(tabId, rendimenti, benchmark) {
const tableContainer = document.querySelector(`#${tabId} table`);
if (!tableContainer) return;
const years = Object.keys(rendimenti).sort();
let headers = '<th class="py-3 px-4 text-left font-bold text-[#1e293b]"></th>';
years.forEach(year => headers += `<th class="py-3 px-4 font-bold text-[#1e293b] text-base">${year}</th>`);
let stratRow = '<td class="py-3 px-4 text-left text-[#1e293b] font-medium">Rendimento totale EUR</td>';
years.forEach(year => {
const val = rendimenti[year];
const valStr = val.toLocaleString('it-IT', {minimumFractionDigits: 1, maximumFractionDigits: 1});
const colorClass = val > 0 ? 'text-green-500' : (val < 0 ? 'text-red-500' : 'text-slate-800');
stratRow += `<td class="py-3 px-4 font-bold ${colorClass}">${val > 0 ? '+' : ''}${valStr}%</td>`;
});
let benchRow = '<td class="py-3 px-4 text-left text-[#1e293b] font-medium">Benchmark EUR</td>';
years.forEach(year => {
const val = benchmark[year];
const valStr = val.toLocaleString('it-IT', {minimumFractionDigits: 1, maximumFractionDigits: 1});
const colorClass = val > 0 ? 'text-green-500' : (val < 0 ? 'text-red-500' : 'text-slate-800');
benchRow += `<td class="py-3 px-4 font-bold ${colorClass}">${val > 0 ? '+' : ''}${valStr}%</td>`;
});
tableContainer.innerHTML = `
<thead><tr class="border-t-[3px] border-b-[2px] border-[#1e293b] bg-slate-50/30">${headers}</tr></thead>
<tbody>
<tr class="border-b border-slate-200 hover:bg-slate-50 transition-colors">${stratRow}</tr>
<tr class="border-b border-[#1e293b] hover:bg-slate-50 transition-colors">${benchRow}</tr>
</tbody>
`;
}

async function loadMetrics() {
function updateMetric(id, value, prefix = '', suffix = '', color = true) {
const el = document.getElementById(id);
if (el) {
if (typeof value === 'number' && !isNaN(value)) {
const numDecimals = window.innerWidth < 640 ? 0 : 2;
let valueStr = value.toLocaleString('it-IT', {minimumFractionDigits: numDecimals, maximumFractionDigits: numDecimals});
el.textContent = `${prefix}${valueStr}${suffix}`;
if (color) {
if (value > 0) { el.classList.remove('text-red-500', 'text-slate-800'); el.classList.add('text-green-500'); el.textContent = `+${el.textContent}`; }
else if (value < 0) { el.classList.remove('text-green-500', 'text-slate-800'); el.classList.add('text-red-500'); }
else { el.classList.remove('text-green-500', 'text-red-500'); el.classList.add('text-slate-800'); }
}
} else { el.textContent = '--'; el.classList.remove('text-green-500', 'text-red-500'); el.classList.add('text-slate-800'); }
}
}

function updateVariationMetric(id, currentValue, pctChange) {
const el = document.getElementById(id);
if (!el || isNaN(currentValue) || isNaN(pctChange)) { if (el) el.textContent = '--'; return; }
const prevValue = currentValue / (1 + pctChange);
const absChange = currentValue - prevValue;
const numDecimals = window.innerWidth < 640 ? 0 : 2;
const absStr = Math.abs(absChange).toLocaleString('it-IT', {minimumFractionDigits: numDecimals, maximumFractionDigits: numDecimals});
const pctStr = Math.abs(pctChange * 100).toLocaleString('it-IT', {minimumFractionDigits: numDecimals, maximumFractionDigits: numDecimals});
let sign = '';
if (pctChange > 0) { sign = '+'; el.classList.remove('text-red-500', 'text-slate-800'); el.classList.add('text-green-500'); }
else if (pctChange < 0) { sign = '-'; el.classList.remove('text-green-500', 'text-slate-800'); el.classList.add('text-red-500'); }
else { el.classList.remove('text-green-500', 'text-red-500'); el.classList.add('text-slate-800'); }
el.textContent = `${sign}€ ${absStr} / ${sign}${pctStr}%`;
}

async function fetchAndUpdate(strategy, path, allocationContainerId, tabId) {
try {
const response = await fetch(path);
if (response.ok) {
const metrics = await response.json();
const currentVal = metrics.ultimo_valore_indice;
updateMetric(`${strategy}-current-value`, currentVal, '€ ', '', false);
updateVariationMetric(`${strategy}-change-24h`, currentVal, metrics.variazione_24h_pct);
updateVariationMetric(`${strategy}-change-ytd`, currentVal, metrics.variazione_ytd_pct);
if (metrics.ultima_allocazione_pesi) buildAllocationTable(allocationContainerId, metrics.ultima_allocazione_pesi, metrics.capitalizzazione_mercato);
if (metrics.rendimenti_annuali && metrics.benchmark_annuali && tabId) buildReturnsTable(tabId, metrics.rendimenti_annuali, metrics.benchmark_annuali);
}
} catch (e) { console.error(`Error loading metrics for ${strategy}:`, e); }
}

fetchAndUpdate('main', './charts/Top5MktCap/metrics.json', 'main-allocation', 'mainStrategy');
fetchAndUpdate('tech', './charts/TechMktCap_TH/metrics.json', 'tech-allocation', 'techMarketCap');
fetchAndUpdate('extra1', './charts/DefiMktCap_TH/metrics.json', 'extra1-allocation', 'extraStrategy1');
fetchAndUpdate('extra2', './charts/PagamentiMktCap_TH/metrics.json', 'extra2-allocation', 'extraStrategy2');
}

async function loadStrategyCharts() {
const loadChart = async (url, element, tickPrefix = '€ ', isPerf = true) => {
try {
const res = await fetch(url);
if(res.ok) {
const data = await res.json();
if(element && data.data && data.layout) {
processTraces(data.data);
data.data.forEach(trace => { if(isPerf && trace.name !== "Ribilanciamento") trace.hovertemplate = `<b>%{fullData.name}</b>: ${tickPrefix}%{y:,.0f}<extra></extra>`; });
if(isPerf) { if(!data.layout.yaxis) data.layout.yaxis = {}; data.layout.yaxis.tickprefix = tickPrefix; }
Plotly.newPlot(element, data.data, getLayoutWithMargins(data.layout), {responsive: true, displayModeBar: false}).then(() => { setTimeout(() => Plotly.Plots.resize(element), 50); });
}
}
} catch(e) {}
};
loadChart('./charts/Top5MktCap/performance.json', performanceChartEl);
loadChart('./charts/Top5MktCap/weights.json', compositionChartEl, '', false);
loadChart('./charts/TechMktCap_TH/performance.json', techPerformanceChartEl);
loadChart('./charts/TechMktCap_TH/weights.json', techWeightsChartEl, '', false);
loadChart('./charts/DefiMktCap_TH/performance.json', extra1PerfChartEl);
loadChart('./charts/DefiMktCap_TH/weights.json', extra1CompChartEl, '', false);
loadChart('./charts/PagamentiMktCap_TH/performance.json', extra2PerfChartEl);
loadChart('./charts/PagamentiMktCap_TH/weights.json', extra2WeightsChartEl, '', false);
}

async function loadMarketAnalyticsCharts() {
const container = document.getElementById('market-analytics-charts-container');
if (!container) return;
const chartConfigs = [
{ file: 'btc_dominance.json', title: 'BTC Dominance', description: 'Il grafico della BTC Dominance mostra la quota di mercato di Bitcoin rispetto alle altre criptovalute listate su Conio.', height: '500px' },
{ file: 'correlation_heatmap.json', title: 'Correlazione Asset con BTC', description: 'Questa mappa di calore (heatmap) evidenzia la correlazione tra i vari asset listati su Conio e Bitcoin. Un valore di 1 indica una correlazione positiva perfetta, mentre un valore di -1 indica una correlazione negativa perfetta. Più il colore è scuro e meno gli asset sono correlati tra loro.', height: '850px' },
{ file: 'market_volume.json', title: 'Volume del Mercato Crypto', description: 'Il grafico mostra l\'evoluzione dei volumi di scambio delle criptovalute listate su Conio nel tempo.', height: '500px' }
];

for (let i = 0; i < chartConfigs.length; i++) {
const config = chartConfigs[i];
const chartId = `market-chart-${i}`;
const chartWrapper = document.createElement('div');
const isMobile = window.innerWidth < 640;
const responsiveHeight = isMobile ? (config.file === 'correlation_heatmap.json' ? '500px' : '350px') : config.height;

    chartWrapper.className = "bg-white p-2 md:p-6 rounded-2xl border border-slate-200 shadow-sm w-full mb-8";
    chartWrapper.innerHTML = `
    <h3 class="font-bold mb-3 md:mb-4 text-lg md:text-xl text-[#0a1b39]">${config.title}</h3>
    <div class="w-full overflow-hidden">
        <div id="${chartId}" style="min-height: ${responsiveHeight}; width: 100%;"></div>
    </div>
    <div class="mt-4 p-3 md:p-4 bg-slate-50 border border-slate-100 rounded-xl">
        <p class="text-xs md:text-sm text-slate-600 leading-relaxed text-left">${config.description}</p>
    </div>`;
container.appendChild(chartWrapper);

try {
const response = await fetch(`./charts/market_analytics/${config.file}`);
if (response.ok) {
const chartData = await response.json();
const chartEl = document.getElementById(chartId);
if (chartEl && chartData.data && chartData.layout) {
processTraces(chartData.data);

if (config.file === 'correlation_heatmap.json' && chartData.data[0]) {
chartData.data[0].hovertemplate = 'X: %{x}<br>Y: %{y}<br>Correlazione: %{z:.4f}<extra></extra>';
chartData.data[0].zmin = -1; chartData.data[0].zmax = 1;
chartData.data[0].colorscale = [[0.0, '#0a1a6b'],[0.5, '#0050ff'],[0.75, '#8800ff'],[1.0, '#ffffff']];
const isMobileHeatmap = window.innerWidth < 640;
chartData.data[0].colorbar = {
    thicknessmode: 'pixels',
    thickness: isMobileHeatmap ? 8 : 12,
    len: 1,
    x: 1,
    xanchor: 'left',
    xpad: 2,
    tickfont: { size: isMobileHeatmap ? 9 : 11, color: '#475569' },
    outlinewidth: 0
};

// --- MODIFICA 1: Asse Y fuori e asse X in cima ---
chartData.layout._isHeatmap = true;

// Cloniamo l'asse x inferiore su xaxis2 e lo posizioniamo "top"
chartData.layout.xaxis2 = Object.assign({}, chartData.layout.xaxis || {}, {
    overlaying: 'x',
    side: 'top',
    matches: 'x',
    showticklabels: true
});

// TRUCCO PLOTLY: Aggiungiamo una traccia invisibile legata a xaxis2 per forzare il rendering dell'asse superiore
chartData.data.push({
    x: chartData.data[0].x,
    y: chartData.data[0].y,
    type: 'scatter',
    mode: 'markers',
    marker: { color: 'rgba(0,0,0,0)' }, // Trasparente: non si vede nel grafico
    xaxis: 'x2',
    yaxis: 'y',
    showlegend: false,
    hoverinfo: 'skip'
});

// --- MODIFICA 2: Annotazione testuale a "X" ---
const zData = chartData.data[0].z;
const xData = chartData.data[0].x;
const yData = chartData.data[0].y;
chartData.layout.annotations = chartData.layout.annotations || [];

if (zData && xData && yData) {
    for (let row = 0; row < yData.length; row++) {
        for (let col = 0; col < xData.length; col++) {
            if (zData[row][col] === null || isNaN(zData[row][col])) {
                chartData.layout.annotations.push({
                    x: xData[col],
                    y: yData[row],
                    text: '✕',
                    showarrow: false,
                    font: { color: '#94a3b8', size: 24 }
                });
                            }
                        }
                    }
                }
                } else if (config.file === 'btc_dominance.json' && chartData.data[0]) {
                    chartData.data[0].hovertemplate = 'Dominance: %{y:.0f}%<extra></extra>';
                    if (!chartData.layout.yaxis) chartData.layout.yaxis = {};
                    chartData.layout.yaxis.ticksuffix = '%';
                    chartData.layout.yaxis.tickformat = '.0f';
                } else if (config.file === 'market_volume.json' && chartData.data[0]) {
                if (chartData.data[0].y && Array.isArray(chartData.data[0].y)) {
                    chartData.data[0].y = chartData.data[0].y.map(v => v / 1e9);
                }
                chartData.data[0].hovertemplate = 'Volume: €%{y:.2f} B<extra></extra>';
                if (!chartData.layout.yaxis) chartData.layout.yaxis = {};
                chartData.layout.yaxis.tickprefix = '€ ';
                chartData.layout.yaxis.ticksuffix = ' B';
                chartData.layout.yaxis.tickformat = ',.1f';
            }
            Plotly.newPlot(chartEl, chartData.data, getLayoutWithMargins(chartData.layout), { responsive: true, displayModeBar: false }).then(() => { setTimeout(() => Plotly.Plots.resize(chartEl), 50); });
        }
    }
} catch (e) { console.error(e); }
}
}

// ==========================================
// LOGICA BUILDER (STRATEGY + PAC)
// ==========================================

let pStrat1 = [];
let pStrat2 = [];

function renderPortfolioList(portfolio, listId, totalId, clearBtnId, pType, pIndex) {
const listEl = document.getElementById(listId);
const totalWeightEl = document.getElementById(totalId);
const clearBtn = document.getElementById(clearBtnId);
const emptyMsg = document.getElementById(`empty-msg-${pIndex}`);
let totalWeight = 0;
let html = '';

    if (portfolio.length === 0) {
        if (emptyMsg) emptyMsg.classList.remove('hidden');
        if (clearBtn) clearBtn.classList.add('hidden');
    } else {
        if (emptyMsg) emptyMsg.classList.add('hidden');
        if (clearBtn) clearBtn.classList.remove('hidden');
        portfolio.forEach((asset, index) => {
            totalWeight += asset.weight;
html += `
<li class="py-2.5 flex justify-between items-center group">
<div class="flex flex-col">
<span class="font-bold text-slate-700">${asset.name}</span>
<span class="text-[10px] text-slate-400 font-medium">${asset.ticker}</span>
</div>
<div class="flex items-center gap-4">
<span class="font-extrabold text-[#0050ff] bg-blue-50 px-2 py-1 rounded-md text-xs">${asset.weight}%</span>
<button onclick="removeAsset('${pType}', ${pIndex}, ${index})" class="text-slate-300 hover:text-red-500 transition-colors p-1">
<i class="fa-solid fa-trash-can text-sm"></i>
</button>
</div>
</li>`;
});
}

listEl.innerHTML = html;
totalWeightEl.textContent = `${totalWeight}%`;
if (totalWeight === 100) { 
    totalWeightEl.classList.remove('text-red-500', 'text-slate-800'); 
    totalWeightEl.classList.add('text-green-500'); 
} else { 
    totalWeightEl.classList.remove('text-green-500', 'text-slate-800'); 
    totalWeightEl.classList.add('text-red-500'); 
}
return totalWeight;
}

function updateStratUI() {
const runBtn = document.getElementById('strat-run-btn');
const w1 = renderPortfolioList(pStrat1, 'strat-list-1', 'strat-total-1', 'strat-clear-1', 'STRAT', 1);
const w2 = renderPortfolioList(pStrat2, 'strat-list-2', 'strat-total-2', 'strat-clear-2', 'STRAT', 2);
runBtn.disabled = !(w1 === 100 && (pStrat2.length === 0 || w2 === 100));
}

let activePortfolioIndex = 1;

window.openAddAssetModal = function(index) {
    activePortfolioIndex = index;
    const modal = document.getElementById('asset-modal');
    modal.classList.add('active');
    document.getElementById('modal-strat-weight').value = '';
    // Optional: focus weight input
    setTimeout(() => document.getElementById('modal-strat-asset').focus(), 100);
};

window.closeAddAssetModal = function() {
    document.getElementById('asset-modal').classList.remove('active');
};

document.getElementById('modal-confirm-btn').addEventListener('click', () => {
    const selectEl = document.getElementById('modal-strat-asset');
    const weightEl = document.getElementById('modal-strat-weight');
    const name = selectEl.options[selectEl.selectedIndex].text;
    const weight = parseInt(weightEl.value, 10);
    
    if (isNaN(weight) || weight <= 0 || weight > 100) {
        alert("Inserisci un peso valido tra 1 e 100.");
        return;
    }

    const portfolio = activePortfolioIndex === 1 ? pStrat1 : pStrat2;
    const currentTotal = portfolio.reduce((acc, a) => acc + a.weight, 0);
    
    if (currentTotal + weight > 100) {
        alert(`Il peso totale supererebbe il 100% (attuale: ${currentTotal}%).`);
        return;
    }

    const existingIndex = portfolio.findIndex(a => a.name === name);
    if (existingIndex > -1) {
        portfolio[existingIndex].weight += weight;
    } else {
        portfolio.push({ name, weight, ticker: getTickerName(selectEl.value) });
    }

    updateStratUI();
    closeAddAssetModal();
});

function getTickerName(rawValue) {
    return rawValue.toUpperCase();
}

window.togglePortfolio = function(index) {
    const content = document.getElementById(`portfolio-content-${index}`);
    const toggleBtn = document.getElementById(`portfolio-toggle-${index}`);
    const icon = toggleBtn.querySelector('i');
    
    if (content.classList.contains('hidden')) {
        content.classList.remove('hidden');
        icon.classList.remove('fa-chevron-down');
        icon.classList.add('fa-chevron-up');
    } else {
        content.classList.add('hidden');
        icon.classList.remove('fa-chevron-up');
        icon.classList.add('fa-chevron-down');
    }
    
    // Resize plotly charts if any
    setTimeout(() => { window.dispatchEvent(new Event('resize')); }, 50);
};

window.removeAsset = function(pType, pIndex, index) {
if (pType === 'STRAT') {
    if (pIndex === 1) pStrat1.splice(index, 1);
    else if (pIndex === 2) pStrat2.splice(index, 1);
    updateStratUI();
}
}

const pacToggle1 = document.getElementById('pac-toggle-1');
const pacToggle2 = document.getElementById('pac-toggle-2');
const pacInputs1 = document.getElementById('pac-inputs-1');
const pacInputs2 = document.getElementById('pac-inputs-2');

pacToggle1.addEventListener('change', () => pacInputs1.classList.toggle('hidden', !pacToggle1.checked));
pacToggle2.addEventListener('change', () => pacInputs2.classList.toggle('hidden', !pacToggle2.checked));




document.getElementById('strat-timeframe').addEventListener('change', function() {
const customDates = document.getElementById('strat-custom-dates');
if (this.value === 'CUSTOM') customDates.classList.remove('hidden'); else customDates.classList.add('hidden');
});

function calculateMetrics(prices, dailyReturns) {
if (prices.length < 2) return { returnPct: 0, volAnn: 0, maxDd: 0, sharpe: 0 };
const endPrice = prices[prices.length - 1];
const startPrice = prices[0];
const returnPct = startPrice > 0 ? ((endPrice - startPrice) / startPrice) * 100 : 0;

let meanRet = 0, volAnn = 0, sharpe = 0;
if (dailyReturns && dailyReturns.length > 0) {
meanRet = dailyReturns.reduce((a, b) => a + b, 0) / dailyReturns.length;
const variance = dailyReturns.reduce((a, b) => a + Math.pow(b - meanRet, 2), 0) / dailyReturns.length;
const stdDev = Math.sqrt(variance);
volAnn = stdDev * Math.sqrt(365) * 100;
sharpe = volAnn !== 0 ? (meanRet * 365) / (stdDev * Math.sqrt(365)) : 0;
}

let maxPrice = prices[0];
let maxDd = 0;
for(let p of prices) {
if(p > maxPrice) maxPrice = p;
const dd = (p - maxPrice) / maxPrice;
if(dd < maxDd) maxDd = dd;
}
return { returnPct, volAnn, maxDd: maxDd * 100, sharpe };
}

async function fetchCommonDates(allAssets, tfId, startId, endId) {
let dateMap = {};
for (const ticker of allAssets) {
const res = await fetch(`./data/price_data/${ticker}.json`);
if (!res.ok) throw new Error(`Dati storici per ${ticker} non trovati.`);
const data = await res.json();
for(let i=0; i<data.length; i++) {
const entry = data[i];
if(!dateMap[entry.data]) dateMap[entry.data] = {};
dateMap[entry.data][ticker] = entry.prezzo;
}
}
const allSortedDates = Object.keys(dateMap).sort();
if (allSortedDates.length === 0) throw new Error("Nessun dato disponibile.");

const tf = document.getElementById(tfId).value;
const now = new Date();
let targetStart = new Date('2000-01-01');
let targetEnd = new Date();

if (tf === '1M') { targetStart = new Date(now); targetStart.setMonth(now.getMonth() - 1); }
else if (tf === '6M') { targetStart = new Date(now); targetStart.setMonth(now.getMonth() - 6); }
else if (tf === '1Y') { targetStart = new Date(now); targetStart.setFullYear(now.getFullYear() - 1); }
else if (tf === '3Y') { targetStart = new Date(now); targetStart.setFullYear(now.getFullYear() - 3); }
else if (tf === '5Y') { targetStart = new Date(now); targetStart.setFullYear(now.getFullYear() - 5); }
else if (tf === 'YTD') { targetStart = new Date(now.getFullYear(), 0, 1); }
else if (tf === 'CUSTOM') {
const sd = document.getElementById(startId).value;
const ed = document.getElementById(endId).value;
if(sd) targetStart = new Date(sd);
if(ed) targetEnd = new Date(ed);
if(targetStart > targetEnd) throw new Error("Data di inizio successiva a data di fine.");
}

const getLocalYMD = (dateObj) => `${dateObj.getFullYear()}-${String(dateObj.getMonth() + 1).padStart(2, '0')}-${String(dateObj.getDate()).padStart(2, '0')}`;
const startStr = getLocalYMD(targetStart);
const endStr = getLocalYMD(targetEnd);

const sortedDates = allSortedDates.filter(d => d >= startStr && d <= endStr);
if (sortedDates.length === 0) throw new Error("Nessun dato disponibile nel periodo selezionato.");

let startIndex = 0;
let initialPrices = null;
for(let i = 0; i < sortedDates.length; i++) {
const d = sortedDates[i];
const prices = dateMap[d];
let hasAllPrices = true;
for(const ticker of allAssets) { if(!prices[ticker]) hasAllPrices = false; }
if(hasAllPrices) { startIndex = i; initialPrices = prices; break; }
}
if(!initialPrices) throw new Error("Punto di partenza comune non trovato per gli asset scelti.");

return { sortedDates, startIndex, initialPrices, dateMap };
}

// STRATEGY RUN
document.getElementById('strat-run-btn').addEventListener('click', async () => {
    const runBtn = document.getElementById('strat-run-btn');
    runBtn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Calcolando...';
    runBtn.disabled = true;

    try {
        const allAssets = [...new Set([...pStrat1, ...pStrat2].map(a => a.ticker))];
        const { sortedDates, startIndex, initialPrices, dateMap } = await fetchCommonDates(allAssets, 'strat-timeframe', 'strat-start-date', 'strat-end-date');

        // Portfolio A params
        const val1 = parseFloat(document.getElementById('strat-capital-1').value);
        const initialCapital1 = (isNaN(val1) || val1 <= 0) ? 1 : val1;
        const pacAmount1 = parseFloat(document.getElementById('strat-pac-amount-1').value) || 0;
        const pacFreq1 = parseInt(document.getElementById('strat-pac-frequency-1').value, 10) || 30;
        const hasPAC1 = document.getElementById('pac-toggle-1').checked;

        // Portfolio B params
        const val2 = parseFloat(document.getElementById('strat-capital-2').value);
        const initialCapital2 = (isNaN(val2) || val2 <= 0) ? 1 : val2;
        const pacAmount2 = parseFloat(document.getElementById('strat-pac-amount-2').value) || 0;
        const pacFreq2 = parseInt(document.getElementById('strat-pac-frequency-2').value, 10) || 30;
        const hasPAC2 = document.getElementById('pac-toggle-2').checked;

        // Portfolio A state
        let shares1 = {};
        let totalInvested1 = initialCapital1;
        pStrat1.forEach(a => shares1[a.ticker] = (initialCapital1 * (a.weight / 100)) / initialPrices[a.ticker]);
        let lastPacDate1Ms = new Date(sortedDates[startIndex]).getTime();

        // Portfolio B state
        let shares2 = {};
        let totalInvested2 = initialCapital2;
        pStrat2.forEach(a => shares2[a.ticker] = (initialCapital2 * (a.weight / 100)) / initialPrices[a.ticker]);
        let lastPacDate2Ms = new Date(sortedDates[startIndex]).getTime();

        let xData = [], yData1 = [], yData2 = [], dailyReturns1 = [], dailyReturns2 = [];
        let lastVal1 = null, lastVal2 = null;

        for (let i = startIndex; i < sortedDates.length; i++) {
            const d = sortedDates[i];
            const currentMs = new Date(d).getTime();
            const prices = dateMap[d];

            // Update PAC A
            if (hasPAC1 && pacAmount1 > 0 && currentMs > lastPacDate1Ms) {
                const daysDiff = (currentMs - lastPacDate1Ms) / (1000 * 60 * 60 * 24);
                if (daysDiff >= pacFreq1) {
                    pStrat1.forEach(a => { if(prices[a.ticker]) shares1[a.ticker] += (pacAmount1 * (a.weight / 100)) / prices[a.ticker]; });
                    totalInvested1 += pacAmount1;
                    lastPacDate1Ms = currentMs;
                }
            }

            // Update PAC B
            if (hasPAC2 && pacAmount2 > 0 && currentMs > lastPacDate2Ms) {
                const daysDiff = (currentMs - lastPacDate2Ms) / (1000 * 60 * 60 * 24);
                if (daysDiff >= pacFreq2) {
                    pStrat2.forEach(a => { if(prices[a.ticker]) shares2[a.ticker] += (pacAmount2 * (a.weight / 100)) / prices[a.ticker]; });
                    totalInvested2 += pacAmount2;
                    lastPacDate2Ms = currentMs;
                }
            }

            let val1 = 0, val2 = 0;
            pStrat1.forEach(a => { if(prices[a.ticker]) val1 += shares1[a.ticker] * prices[a.ticker]; });
            pStrat2.forEach(a => { if(prices[a.ticker]) val2 += shares2[a.ticker] * prices[a.ticker]; });

            if (val1 > 0 || val2 > 0) {
                xData.push(d);
                if (pStrat1.length > 0) yData1.push(val1);
                if (pStrat2.length > 0) yData2.push(val2);
                
                // Returns calculation (adjusted for PAC deposits to avoid spikes)
                if (pStrat1.length > 0 && lastVal1 !== null) {
                    const wasPacAdded = hasPAC1 && (currentMs === lastPacDate1Ms && i > startIndex);
                    const flowAdjustedVal = wasPacAdded ? (val1 - pacAmount1) : val1;
                    dailyReturns1.push((flowAdjustedVal - lastVal1) / lastVal1);
                }
                if (pStrat2.length > 0 && lastVal2 !== null) {
                    const wasPacAdded = hasPAC2 && (currentMs === lastPacDate2Ms && i > startIndex);
                    const flowAdjustedVal = wasPacAdded ? (val2 - pacAmount2) : val2;
                    dailyReturns2.push((flowAdjustedVal - lastVal2) / lastVal2);
                }

                lastVal1 = val1; lastVal2 = val2;
            }
        }

        document.getElementById('strat-results-placeholder').classList.add('hidden');
        document.getElementById('strat-results-content').classList.remove('hidden');
        document.getElementById('strat-results-content').classList.add('flex');

        // Render Metrics Table
        const renderCol = (idx, yData, dailyReturns, invested) => {
            const stats = calculateMetrics(yData, dailyReturns);
            // Override total return with (FinalValue - TotalInvested)/TotalInvested
            const finalVal = yData[yData.length - 1] || 0;
            const realReturnPct = invested > 0 ? ((finalVal - invested) / invested) * 100 : 0;

            document.getElementById(`td-stat-invested-${idx}`).textContent = '€ ' + invested.toLocaleString('it-IT', {minimumFractionDigits: 2, maximumFractionDigits: 2});
            document.getElementById(`td-stat-final-${idx}`).textContent = '€ ' + finalVal.toLocaleString('it-IT', {minimumFractionDigits: 2, maximumFractionDigits: 2});
            
            const retEl = document.getElementById(`td-stat-return-${idx}`);
            retEl.textContent = (realReturnPct >= 0 ? '+' : '') + realReturnPct.toFixed(2) + '%';
            retEl.className = realReturnPct >= 0 ? "px-4 py-3.5 font-bold text-green-500" : "px-4 py-3.5 font-bold text-red-500";
            
            document.getElementById(`td-stat-vol-${idx}`).textContent = stats.volAnn.toFixed(2) + '%';
            document.getElementById(`td-stat-dd-${idx}`).textContent = stats.maxDd.toFixed(2) + '%';
            document.getElementById(`td-stat-sharpe-${idx}`).textContent = stats.sharpe.toFixed(2);
        };

        renderCol(1, yData1, dailyReturns1, totalInvested1);
        
        const hasB = pStrat2.length > 0;
        document.getElementById('strat-th-b').classList.toggle('hidden', !hasB);
        document.querySelectorAll('[id$="-2"]').forEach(el => {
            if (el.tagName === 'TD') el.classList.toggle('hidden', !hasB);
        });

        if (hasB) renderCol(2, yData2, dailyReturns2, totalInvested2);

        const traces = [{ x: xData, y: yData1, type: 'scatter', mode: 'lines', line: { color: '#0050ff', width: 2.5 }, fill: !hasB ? 'tozeroy' : 'none', fillcolor: 'rgba(0, 80, 255, 0.05)', name: 'Portafoglio A' }];
        if (hasB) {
            traces.push({ x: xData, y: yData2, type: 'scatter', mode: 'lines', line: { color: '#ff8c00', width: 2.5 }, name: 'Portafoglio B' });
        }

        Plotly.newPlot('strat-chart', traces, window.getLayoutWithMargins({
            xaxis: { showgrid: false }, 
            yaxis: { tickprefix: '€ ', gridcolor: '#f1f5f9' }, 
            hovermode: 'x unified',
            legend: { orientation: 'h', y: -0.15 }
        }), {responsive: true, displayModeBar: false});

    } catch (e) { alert("Errore: " + e.message); } 
    finally { runBtn.innerHTML = 'Esegui Analisi'; runBtn.disabled = false; window.dispatchEvent(new Event('resize')); }
});


// PAC RUN removed — PAC is now integrated in strat-run-btn

updateStratUI();

async function initDashboard() {
await loadCryptoNames();
loadStrategyCharts();
loadMarketAnalyticsCharts();
loadMetrics();
}

initDashboard();

})();
