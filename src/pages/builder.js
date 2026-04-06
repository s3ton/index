import { processTraces, getLayoutWithMargins } from '../utils/plotly-helpers.js';

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
if (runBtn) {
    runBtn.disabled = !(w1 === 100 && (pStrat2.length === 0 || w2 === 100));
}
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
const res = await fetch(`${import.meta.env.BASE_URL}data/price_data/${ticker}.json`);
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




// PAC RUN removed — PAC is now integrated in strat-run-btn



export function initBuilder() {
  const pacToggle1 = document.getElementById('pac-toggle-1');
  const pacToggle2 = document.getElementById('pac-toggle-2');
  const pacInputs1 = document.getElementById('pac-inputs-1');
  const pacInputs2 = document.getElementById('pac-inputs-2');

  if (pacToggle1) pacToggle1.addEventListener('change', () => pacInputs1.classList.toggle('hidden', !pacToggle1.checked));
  if (pacToggle2) pacToggle2.addEventListener('change', () => pacInputs2.classList.toggle('hidden', !pacToggle2.checked));

  const timeframeSelect = document.getElementById('strat-timeframe');
  if (timeframeSelect) {
      timeframeSelect.addEventListener('change', function() {
          const customDates = document.getElementById('strat-custom-dates');
          if (this.value === 'CUSTOM') customDates.classList.remove('hidden'); else customDates.classList.add('hidden');
      });
  }

  const modalConfirmBtn = document.getElementById('modal-confirm-btn');
  if (modalConfirmBtn) {
      modalConfirmBtn.addEventListener('click', () => {
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
  }

  updateStratUI();

  // STRATEGY RUN
  const runBtn = document.getElementById('strat-run-btn');
  if (runBtn) {
    runBtn.addEventListener('click', async () => {
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

            Plotly.newPlot('strat-chart', traces, getLayoutWithMargins({
                xaxis: { showgrid: false }, 
                yaxis: { tickprefix: '€ ', gridcolor: '#f1f5f9' }, 
                hovermode: 'x unified',
                legend: { orientation: 'h', y: -0.15 }
            }), {responsive: true, displayModeBar: false});

        } catch (e) { alert("Errore: " + e.message); } 
        finally { if (runBtn) { runBtn.innerHTML = 'Esegui Analisi'; runBtn.disabled = false; } window.dispatchEvent(new Event('resize')); }
    });
  }

  updateStratUI();
}




