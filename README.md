# 🐘 AI-Powered SQL Analytics Dashboard

[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)](https://streamlit.io)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-336791?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Supabase](https://img.shields.io/badge/Supabase-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white)](https://supabase.com)
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Groq](https://img.shields.io/badge/Groq-FF6B00?style=for-the-badge&logo=groq&logoColor=white)](https://groq.com)
[![Plotly](https://img.shields.io/badge/Plotly-3F4F75?style=for-the-badge&logo=plotly&logoColor=white)](https://plotly.com)

**Ask questions in plain English • Get SQL results + charts instantly • Enterprise-grade PostgreSQL**

---

## 🚀 Live Demo

> **Try it yourself:** [Your Streamlit Cloud URL here]

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🔍 **Natural Language to SQL** | Ask questions in plain English, AI generates SQL automatically |
| 📊 **Auto Charts** | Visualizations generated instantly from query results |
| 🔗 **Multi-Table JOINs** | Query across 4 normalized tables with relationships |
| 🐘 **PostgreSQL** | Enterprise-grade database with Supabase cloud hosting |
| 📜 **Query History** | Save and reuse previous queries with one click |
| 💡 **Example Questions** | Pre-built queries to get started immediately |
| 📥 **CSV Export** | Download any query result with one click |
| 🔒 **Security** | SQL injection protection and safe query execution |
| 🎨 **Professional UI** | Clean, responsive design with dark/light mode support |

---

## 📁 Database Schema

| Table | Rows | Description | Key Columns |
|-------|------|-------------|-------------|
| **sales** | 10,000 | Transaction data | transaction_id, sale_date, customer, product, revenue |
| **customers** | 100 | Customer details | customer_id, customer_name, email, customer_segment |
| **products** | 10 | Product information | product_id, product_name, category, supplier, cost |
| **regions** | 5 | Region management | region_id, region_name, manager, office |

### Entity Relationship Diagram

---

## 🛠️ Tech Stack

### Frontend & Backend
- **Framework:** Streamlit 1.35.0
- **Language:** Python 3.12
- **Database:** PostgreSQL (Supabase)
- **AI/LLM:** Groq API (Llama 3.1 8B)
- **Visualization:** Plotly 5.19.0
- **Data Processing:** Pandas 2.2.0, NumPy 1.26.4

### Deployment
- **Frontend Hosting:** Streamlit Cloud
- **Database Hosting:** Supabase (PostgreSQL)
- **Version Control:** Git / GitHub

---

## 🏃‍♂️ Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/olalekanijagbemi-VR/nlp-sql-dashboard.git
cd nlp-sql-dashboard