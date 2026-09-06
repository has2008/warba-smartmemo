# warba-smartmemo
Warba Bank AI Challenge - Automated Shariah-Compliant Corporate Credit Memo &amp; Documentation Copilot (Track 1)
The solution includes an Agentic Orchestration Engine powered by LangGraph (orchestration_engine.py) alongside a live interactive Streamlit application (app.py)
# 🏦 Warba SmartMemo | Corporate Banking AI Copilot
### The Corporate Banking AI Challenge — Track 1: AI-Powered Client Documentation

**Warba SmartMemo** is an enterprise-grade agentic AI solution designed to hand Corporate Relationship Managers (RMs) at **Warba Bank** their time back. It reverses the 70% administrative drag into automated, Shariah-compliant credit analysis.

---

## 🌟 Key Features
- **Lossless Financial Ingestion:** Powered by `pdfplumber` for precise tabular extraction of balance sheets and income statements.
- **Agentic Multi-Agent Orchestration:** Powered by **LangGraph**, coordinating 4 dedicated agents:
  1. *Financial Analyst Agent* (Ratios, Liquidity, EBITDA).
  2. *Shariah Governance Agent* (AAOIFI standards screening & Islamic facility structuring e.g., Commodity Murabaha).
  3. *Risk Assessment Agent* (Cross-examining RM qualitative notes against financials).
  4. *Memo Synthesizer Agent* (Standardized Credit Memo drafting).
- **Dual Engine Flexibility:** Model-agnostic architecture supporting both **Claude 3.5 Sonnet** and **GPT-4o**.
- **Human-in-the-Loop Review:** Dedicated audit interface allowing RMs to inspect, edit, and approve before Core Banking API dispatch.

---

## 🛠️ Architecture Stack
- **Frontend / UI:** Streamlit Cloud
- **Orchestration:** LangChain / LangGraph
- **Document Parsing:** `pdfplumber` & `PyPDF`
- **Security Standard:** Zero Data Retention, Banking-Grade Sandbox Deployment
