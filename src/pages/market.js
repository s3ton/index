import { processTraces, getLayoutWithMargins } from '../utils/plotly-helpers.js';

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
const response = await fetch(`${import.meta.env.BASE_URL}charts/market_analytics/${config.file}`);
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


export function initMarket() {
  loadMarketAnalyticsCharts();
}
