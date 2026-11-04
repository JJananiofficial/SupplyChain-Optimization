
# SupplyChain Optimizer

### An Intelligent, Sustainability-Aware Supply Chain Decision-Support Platform for SMEs

<p align="center">
  <a href="https://supplychain-optimization-jananij.streamlit.app/">
    <strong>🚀 Launch SupplyChain Optimizer</strong>
  </a>
</p>

SupplyChain Optimizer is a Python-based application designed to help businesses make better sourcing, distribution and logistics decisions. It combines mathematical optimisation, operational scenario analysis and sustainability evaluation in one interactive platform.

The application models a multi-echelon supply chain connecting suppliers, warehouses and customers. It identifies cost-efficient allocation strategies while considering operational constraints, delivery requirements and environmental impact.

---

## 🌐 Live Application

**Try the application:**  
https://supplychain-optimization-jananij.streamlit.app/

**Source Code:**  
https://github.com/JJananiofficial/SupplyChain-Optimization

---

## Overview

Supply chain decisions often involve competing priorities: reducing procurement and transportation costs, meeting customer demand, managing limited warehouse capacity and minimising environmental impact.

SupplyChain Optimizer addresses these challenges through a mathematical optimisation engine and an interactive Streamlit dashboard.

## Key Features

### 1. Supply Chain Network Management

- Manage suppliers, warehouses and customers.
- Configure inbound and outbound transportation routes.
- Upload datasets using CSV templates.
- Validate network data and operational constraints.

### 2. Mathematical Optimisation

- Linear programming-based cost minimisation.
- Supplier capacity and warehouse capacity constraints.
- Customer demand fulfilment.
- Warehouse flow conservation.
- Transportation route capacity constraints.
- Delivery-time eligibility.

### 3. Scenario Analysis

Evaluate the impact of operational disruptions and changing business conditions:

- Supplier price fluctuations.
- Supplier outages.
- Changes in customer demand.
- Warehouse capacity reductions.
- Carbon emission restrictions.

### 4. Sustainability and Pareto Analysis

- Calculate transportation-related emissions.
- Compare cost and environmental performance.
- Generate cost-emission trade-off solutions.
- Explore sustainability constraints using the epsilon-constraint method.

### 5. Decision-Support Dashboard

- Interactive operational overview.
- Network and data management.
- Optimisation results.
- Scenario laboratory.
- Sustainability analysis.
- Exportable results and methodology.

---

## Mathematical Model

The core optimisation objective minimises total procurement, transportation and warehouse handling costs.

The model considers:

- Supplier capacity constraints.
- Warehouse capacity constraints.
- Warehouse flow conservation.
- Customer demand fulfilment.
- Inbound and outbound route capacities.
- Delivery-time restrictions.
- Non-negativity constraints.
- Optional carbon emission limits.

---

## Technology Stack

| Component | Technology |
|---|---|
| Programming Language | Python |
| Application Framework | Streamlit |
| Optimisation | PuLP / Linear Programming |
| Data Processing | Pandas, NumPy |
| Visualisation | Plotly |
| Authentication and Persistence | SQLite |
| Testing | Pytest |

---

## Getting Started

### Prerequisites

- Python 3.10 or later
- pip

### Installation

**1. Clone the repository**

```bash
git clone https://github.com/JJananiofficial/SupplyChain-Optimization.git
cd SupplyChain-Optimization
```

**2. Install dependencies**

```bash
pip install -r requirements.txt
```

**3. Launch the application**

```bash
streamlit run app.py
```

Open the local URL displayed in your terminal.

---

## Project Structure

```text
SupplyChain-Optimization/
│
├── app.py
├── supplychain/
│   ├── auth.py
│   ├── data_validation.py
│   ├── dynamic_optimizer.py
│   ├── optimizer.py
│   ├── scenario_analysis.py
│   └── pareto_analysis.py
│
├── data/
│   ├── benchmark/
│   ├── sample/
│   └── templates/
│
├── docs/
├── tests/
├── requirements.txt
├── packages.txt
└── DEPLOYMENT.md
```

---

## Research and Development Scope

The current implementation uses a deterministic, single-period, multi-echelon supply chain model.

Potential extensions include:

- Multi-period inventory optimisation.
- Stochastic and robust optimisation.
- Multi-product supply chain modelling.
- Mixed-integer optimisation.
- Carbon-aware transportation planning.
- Advanced disruption and resilience modelling.

---

## Project Status

**Active Development**

This project is being developed as an applied operations research and business analytics initiative, with an emphasis on practical decision support for manufacturing SMEs.

---

## License

License information will be added separately.

---

<p align="center">
  <strong>SupplyChain Optimizer</strong><br>
  Optimising Supply Chains. Balancing Cost, Delivery and Sustainability.
</p>
