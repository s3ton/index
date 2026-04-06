export function decodePlotlyBdata(traceData) {
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

export function processTraces(dataArray) {
    if (!Array.isArray(dataArray)) return;
    dataArray.forEach(trace => {
        if (trace.x) trace.x = decodePlotlyBdata(trace.x);
        if (trace.y) trace.y = decodePlotlyBdata(trace.y);
        if (trace.z) trace.z = decodePlotlyBdata(trace.z);
        if (trace.customdata) trace.customdata = decodePlotlyBdata(trace.customdata);
    });
}

export function getLayoutWithMargins(layout) {
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

window.getLayoutWithMargins = getLayoutWithMargins;
window.processTraces = processTraces;

window.addEventListener('resize', () => {
    if (window.Plotly) {
        const activeCharts = document.querySelectorAll('.page-content.block .tab-content.active .js-plotly-plot, .page-content.block > .js-plotly-plot, #market-analytics-charts-container .js-plotly-plot, #page-builder .js-plotly-plot');
        activeCharts.forEach(chart => Plotly.Plots.resize(chart));
    }
});
