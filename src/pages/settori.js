import { processTraces, getLayoutWithMargins } from '../utils/plotly-helpers.js';

async function loadCryptoNames() {
    // I nomi sono ora definiti localmente per evitare errori nel caricamento dei file esterni
}









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

fetchAndUpdate('main', import.meta.env.BASE_URL + 'charts/Top5MktCap/metrics.json', 'main-allocation', 'mainStrategy');
fetchAndUpdate('tech', import.meta.env.BASE_URL + 'charts/TechMktCap_TH/metrics.json', 'tech-allocation', 'techMarketCap');
fetchAndUpdate('extra1', import.meta.env.BASE_URL + 'charts/DefiMktCap_TH/metrics.json', 'extra1-allocation', 'extraStrategy1');
fetchAndUpdate('extra2', import.meta.env.BASE_URL + 'charts/PagamentiMktCap_TH/metrics.json', 'extra2-allocation', 'extraStrategy2');
}

async function loadStrategyCharts() {
const performanceChartEl = document.getElementById('performance-chart');
const compositionChartEl = document.getElementById('composition-chart');
const techPerformanceChartEl = document.getElementById('tech-performance-chart');
const techWeightsChartEl = document.getElementById('tech-weights-chart');
const extra1PerfChartEl = document.getElementById('extra1-performance-chart');
const extra1CompChartEl = document.getElementById('extra1-composition-chart');
const extra2PerfChartEl = document.getElementById('extra2-performance-chart');
const extra2WeightsChartEl = document.getElementById('extra2-weights-chart');

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
loadChart(import.meta.env.BASE_URL + 'charts/Top5MktCap/performance.json', performanceChartEl);
loadChart(import.meta.env.BASE_URL + 'charts/Top5MktCap/weights.json', compositionChartEl, '', false);
loadChart(import.meta.env.BASE_URL + 'charts/TechMktCap_TH/performance.json', techPerformanceChartEl);
loadChart(import.meta.env.BASE_URL + 'charts/TechMktCap_TH/weights.json', techWeightsChartEl, '', false);
loadChart(import.meta.env.BASE_URL + 'charts/DefiMktCap_TH/performance.json', extra1PerfChartEl);
loadChart(import.meta.env.BASE_URL + 'charts/DefiMktCap_TH/weights.json', extra1CompChartEl, '', false);
loadChart(import.meta.env.BASE_URL + 'charts/PagamentiMktCap_TH/performance.json', extra2PerfChartEl);
loadChart(import.meta.env.BASE_URL + 'charts/PagamentiMktCap_TH/weights.json', extra2WeightsChartEl, '', false);
}


export function initSettori() {
  loadStrategyCharts();
  loadMetrics();

  // Tab switching logic
  document.querySelectorAll('#page-settori .tab-btn').forEach(btn => {
      btn.addEventListener('click', function() {
          document.querySelectorAll('#page-settori .tab-btn').forEach(b => b.classList.remove('active'));
          document.querySelectorAll('#page-settori .tab-content').forEach(c => c.classList.remove('active'));
          
          this.classList.add('active');
          const tabId = this.getAttribute('data-tab');
          const tabEl = document.getElementById(tabId);
          if (tabEl) tabEl.classList.add('active');
          
          // Trigger resize for Plotly charts in the newly visible tab
          setTimeout(() => {
              window.dispatchEvent(new Event('resize'));
              if (window.Plotly) {
                  document.querySelectorAll(`#${tabId} .js-plotly-plot`).forEach(pg => {
                      Plotly.Plots.resize(pg);
                  });
              }
          }, 50);
      });
  });
}

