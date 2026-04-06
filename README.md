# Conio Analytics • Strategy Builder

A professional, modularized crypto analytics platform built with **Vite**, **Plotly.js**, and **Tailwind CSS**. This project provides deep-dive market insights, sectoral indices, and a powerful custom strategy backtesting engine.

---

## 🛠 Project Architecture

The application has been refactored from a monolithic `index.html` into a maintainable, component-based modular structure:

### **1. Core & Orchestration**
- **`index.html`**: The main application shell. It contains the navigation layout and empty containers (`#page-settori`, `#page-market`, `#page-builder`) where content is dynamically injected.
- **`src/main.js`**: The application's "brain". It handles sidebar navigation, page routing, and initializes the correct JavaScript module for each section.
- **`src/styles.css`**: Centralized custom styling and responsive design tokens.

### **2. Modular Pages (`src/pages/`)**
Each major section is split into its own HTML template and JS logic:
- **Settori (Indici Settoriali)**: Dynamic indices (Tech, DeFi, Payments) with automated tab-switching and performance metrics.
- **Market Analytics**: Macro-level crypto market stats, dominance charts, and volatility analysis.
- **Strategy Builder**: A complete backtesting suite with Portfolios A/B comparison and PAC (Dollar Cost Averaging) support.

### **3. Shared Utilities & Assets**
- **`src/utils/plotly-helpers.js`**: Centralized logic for processing binary data and standardizing Chart layouts.
- **`public/data/` & `public/charts/`**: Static JSON data and pre-rendered charts used for high-performance dashboard loading.

---

## 🚀 Getting Started

### **Local Development**
To run the project on your machine:

1. **Install Dependencies**:
   ```bash
   npm install
   ```
2. **Start Dev Server**:
   ```bash
   npm run dev
   ```
3. **Build for Production**:
   ```bash
   npm run build
   ```

---

## 🌎 Deployment (GitHub Pages)

The project is configured for **fully automated deployment** via **GitHub Actions**.

- **Workflow**: Every time you push to the `main` branch, the `.github/workflows/deploy.yml` action triggers.
- **Build Process**: It installs dependencies, runs `npm run build`, and deploys the resulting `dist/` folder to the `gh-pages` branch.
- **Base Path**: Since the site is hosted on a sub-path (`/index/`), the `vite.config.js` is set with `base: '/index/'`. All internal links and fetch calls use `import.meta.env.BASE_URL` to ensure correct path resolution.

---

## ⚙️ Technical Highlights

- **Dynamic Loading**: HTML is imported via Vite's `?raw` loader to keep index files small and modular.
- **Initialization Safety**: All DOM-dependent logic is encapsulated in `init()` functions to ensure elements exist before the JavaScript attempts to interact with them.
- **Responsive Charts**: Automatic Plotly resize listeners handle window scaling and transitions between dashboard sections.
- **Binary Data Handling**: Custom decoding for optimized `bdata` payloads from backend market sources.

---
&copy; 2026 Conio Analytics
