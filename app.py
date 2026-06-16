"""
Professional NLP to SQL Analytics Dashboard
Full features: Charts, Query History, Multiple Tables, Auto-Execute Examples
"""

import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from groq import Groq
import re
import os
import numpy as np
from datetime import datetime

# ==================== PAGE CONFIG ====================
st.set_page_config(
    page_title="AI SQL Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== AUTO-CREATE DATABASE ====================
DB_PATH = "sales.db"

def create_database_if_missing():
    """Create database directly if it doesn't exist"""
    if os.path.exists(DB_PATH):
        return True
    
    with st.spinner("📦 Creating database (10,000+ rows)..."):
        try:
            conn = sqlite3.connect(DB_PATH)
            
            # Products
            products = ["Laptop", "Phone", "Tablet", "Headphones", "Monitor", 
                       "Keyboard", "Mouse", "Desk Chair", "Webcam", "USB Cable"]
            customers = [f"Customer_{i}" for i in range(1, 101)]
            regions = ["North", "South", "East", "West", "Central"]
            dates = pd.date_range("2023-01-01", "2024-12-31")
            
            np.random.seed(42)
            data = []
            
            for transaction_id in range(10000):
                product = np.random.choice(products)
                price = np.random.randint(50, 2000)
                quantity = np.random.randint(1, 11)
                revenue = price * quantity
                random_date = dates[np.random.randint(0, len(dates))]
                
                data.append({
                    "transaction_id": transaction_id + 1,
                    "date": random_date.strftime("%Y-%m-%d"),
                    "customer": np.random.choice(customers),
                    "region": np.random.choice(regions),
                    "product": product,
                    "category": np.random.choice(["Electronics", "Accessories", "Furniture"]),
                    "quantity": quantity,
                    "price": price,
                    "revenue": revenue
                })
            
            df = pd.DataFrame(data)
            df["date"] = pd.to_datetime(df["date"])
            df["month"] = df["date"].dt.month
            df["year"] = df["date"].dt.year
            df["quarter"] = df["date"].dt.quarter
            
            df.to_sql("sales", conn, if_exists="replace", index=False)
            conn.close()
            
            st.success("✅ Database created with 10,000 rows!")
            return True
            
        except Exception as e:
            st.error(f"Database creation failed: {str(e)}")
            return False

# Check and create database
if not os.path.exists(DB_PATH):
    if create_database_if_missing():
        st.rerun()
    else:
        st.stop()

# ==================== CUSTOM CSS ====================
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
    }
    .main-header h1 {
        margin: 0;
        font-size: 2.5rem;
        font-weight: 700;
    }
    .main-header p {
        margin: 0.5rem 0 0 0;
        opacity: 0.9;
        font-size: 1.1rem;
    }
    .success-box {
        padding: 1rem;
        background: #d4edda;
        color: #155724;
        border-radius: 8px;
        border: 1px solid #c3e6cb;
        margin: 1rem 0;
    }
    .error-box {
        padding: 1rem;
        background: #f8d7da;
        color: #721c24;
        border-radius: 8px;
        border: 1px solid #f5c6cb;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# ==================== CONSTANTS ====================
DB_PATH = "sales.db"
SUPPORTED_MODELS = ["llama-3.1-8b-instant", "llama-3.3-70b-versatile", "gemma2-9b-it"]

# ==================== DATABASE FUNCTIONS ====================
def db_exists():
    return os.path.exists(DB_PATH)

@st.cache_data(ttl=300)
def get_table_schema():
    if not db_exists():
        return None
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [t[0] for t in cursor.fetchall()]
        
        schema_info = {}
        for table in tables:
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            row_count = cursor.fetchone()[0]
            sample_df = pd.read_sql_query(f"SELECT * FROM {table} LIMIT 3", conn)
            
            schema_info[table] = {
                "columns": [{"name": col[1], "type": col[2]} for col in columns],
                "row_count": row_count,
                "sample": sample_df.to_dict('records')
            }
        
        return schema_info
    except Exception as e:
        return None
    finally:
        conn.close()

@st.cache_data(ttl=60)
def get_table_stats():
    if not db_exists():
        return None
    
    conn = sqlite3.connect(DB_PATH)
    try:
        stats = {}
        revenue_df = pd.read_sql_query("SELECT SUM(revenue) as total FROM sales", conn)
        stats['total_revenue'] = revenue_df['total'].iloc[0] if not revenue_df.empty else 0
        count_df = pd.read_sql_query("SELECT COUNT(*) as count FROM sales", conn)
        stats['total_transactions'] = count_df['count'].iloc[0] if not count_df.empty else 0
        cust_df = pd.read_sql_query("SELECT COUNT(DISTINCT customer) as count FROM sales", conn)
        stats['unique_customers'] = cust_df['count'].iloc[0] if not cust_df.empty else 0
        prod_df = pd.read_sql_query("SELECT COUNT(DISTINCT product) as count FROM sales", conn)
        stats['unique_products'] = prod_df['count'].iloc[0] if not prod_df.empty else 0
        date_df = pd.read_sql_query("SELECT MIN(date) as min_date, MAX(date) as max_date FROM sales", conn)
        stats['min_date'] = date_df['min_date'].iloc[0] if not date_df.empty else None
        stats['max_date'] = date_df['max_date'].iloc[0] if not date_df.empty else None
        return stats
    except Exception as e:
        return None
    finally:
        conn.close()

def execute_sql(sql_query):
    if not db_exists():
        return None, "Database not found"
    
    try:
        sql_query = sql_query.strip()
        sql_query = re.sub(r';+$', '', sql_query)
        
        dangerous = ['drop', 'delete', 'insert', 'update', 'alter', 'create', 'truncate']
        if any(k in sql_query.lower() for k in dangerous):
            return None, f"⚠️ Security: {dangerous} operations are not allowed"
        
        conn = sqlite3.connect(DB_PATH)
        result = pd.read_sql_query(sql_query, conn)
        conn.close()
        return result, None
    except Exception as e:
        return None, str(e)

# ==================== GROQ AI FUNCTIONS ====================
def generate_sql(question, schema_info, api_key, model="llama-3.1-8b-instant"):
    if not schema_info:
        return None
    
    client = Groq(api_key=api_key)
    
    schema_text = ""
    for table_name, info in schema_info.items():
        columns_desc = ", ".join([f"{col['name']} ({col['type']})" for col in info['columns']])
        schema_text += f"\nTable: {table_name}\nColumns: {columns_desc}\nRows: {info['row_count']:,}\n"
        if info['sample']:
            schema_text += f"Sample: {info['sample'][0]}\n"
    
    prompt = f"""You are an expert SQLite SQL generator. Convert the user's question to SQL.

DATABASE SCHEMA:
{schema_text}

RULES:
1. Return ONLY the SQL query, no explanations, no comments
2. Do NOT include semicolons at the end
3. Use proper SQLite syntax
4. For aggregation queries (SUM, COUNT, AVG, GROUP BY), do NOT add LIMIT
5. For non-aggregation queries, add LIMIT 100
6. Use appropriate column names from the correct tables

User Question: {question}

SQL:"""
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are an SQL expert. Generate only SQL queries, no explanations."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=500
        )
        
        sql_query = response.choices[0].message.content.strip()
        sql_query = re.sub(r'```sql\n?', '', sql_query)
        sql_query = re.sub(r'```\n?', '', sql_query)
        sql_query = re.sub(r'--.*?(\n|$)', '\n', sql_query)
        sql_query = re.sub(r'/\*.*?\*/', '', sql_query, flags=re.DOTALL)
        sql_query = sql_query.rstrip(';')
        sql_query = ' '.join(sql_query.split())
        
        sql_lower = sql_query.lower()
        is_aggregation = any(word in sql_lower for word in ['count(', 'sum(', 'avg(', 'group by', 'max(', 'min('])
        if not is_aggregation and 'limit' not in sql_lower:
            sql_query += " LIMIT 100"
        
        return sql_query
    except Exception as e:
        return None

# ==================== CHART FUNCTIONS ====================
def auto_generate_chart(df, sql_query):
    if df.empty or len(df) < 2:
        return None
    
    numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object', 'datetime64']).columns.tolist()
    date_cols = [col for col in df.columns if any(word in col.lower() for word in ['date', 'month', 'year', 'quarter'])]
    
    if not numeric_cols:
        return None
    
    if date_cols and numeric_cols:
        fig = px.line(df, x=date_cols[0], y=numeric_cols[0], 
                      title=f"Trend Over Time ({numeric_cols[0]})", 
                      markers=True, template="plotly_white")
        return fig
    elif categorical_cols and numeric_cols:
        x_col = categorical_cols[0]
        y_col = numeric_cols[0]
        if len(numeric_cols) > 1:
            fig = px.bar(df, x=x_col, y=numeric_cols, 
                        title=f"{x_col} vs {', '.join(numeric_cols[:2])}",
                        barmode='group', template="plotly_white")
        else:
            fig = px.bar(df, x=x_col, y=y_col,
                        title=f"{y_col} by {x_col}",
                        text_auto=True, template="plotly_white",
                        color=x_col if len(df) <= 20 else None)
        return fig
    elif len(numeric_cols) >= 2:
        fig = px.scatter(df, x=numeric_cols[0], y=numeric_cols[1],
                        title=f"{numeric_cols[0]} vs {numeric_cols[1]}",
                        trendline="ols", template="plotly_white")
        return fig
    elif len(df) <= 15 and categorical_cols and numeric_cols:
        fig = px.pie(df, values=numeric_cols[0], names=categorical_cols[0],
                    title=f"Distribution of {numeric_cols[0]}",
                    hole=0.3, template="plotly_white")
        return fig
    return None

# ==================== QUERY HISTORY ====================
def save_to_history(question, sql, success, row_count=None, error=None):
    if 'query_history' not in st.session_state:
        st.session_state.query_history = []
    
    st.session_state.query_history.insert(0, {
        'timestamp': datetime.now().strftime("%H:%M:%S"),
        'date': datetime.now().strftime("%Y-%m-%d"),
        'question': question,
        'sql': sql,
        'success': success,
        'rows': row_count,
        'error': error
    })
    st.session_state.query_history = st.session_state.query_history[:20]

# ==================== MAIN APP ====================
def main():
    st.markdown("""
    <div class="main-header">
        <h1>📊 AI-Powered SQL Analytics</h1>
        <p>Ask questions in plain English • Get instant insights with charts</p>
    </div>
    """, unsafe_allow_html=True)
    
    # ==================== SIDEBAR ====================
    with st.sidebar:
        st.markdown("### 🔑 Configuration")
        
        try:
            api_key = st.secrets["GROQ_API_KEY"]
            st.success("✅ API Key loaded from secrets")
        except:
            api_key = st.text_input("Groq API Key:", type="password", key="api_key")
            if not api_key:
                st.warning("⚠️ Enter your Groq API key to continue")
                st.stop()
        
        model = st.selectbox("AI Model:", SUPPORTED_MODELS, index=0)
        st.divider()
        
        st.markdown("### 📁 Database Overview")
        if db_exists():
            stats = get_table_stats()
            if stats:
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("💰 Revenue", f"${stats['total_revenue']:,.0f}")
                    st.metric("📦 Products", stats['unique_products'])
                with col2:
                    st.metric("🧾 Transactions", f"{stats['total_transactions']:,}")
                    st.metric("👥 Customers", stats['unique_customers'])
                if stats['min_date'] and stats['max_date']:
                    st.caption(f"📅 {stats['min_date']} → {stats['max_date']}")
            else:
                st.error("Could not load stats")
        else:
            st.error("❌ Database not found")
            st.stop()
        st.divider()
        
        st.markdown("### 📜 Query History")
        if 'query_history' in st.session_state and st.session_state.query_history:
            for i, q in enumerate(st.session_state.query_history[:7]):
                icon = "✅" if q['success'] else "❌"
                if st.button(f"{icon} {q['question'][:35]}...", key=f"hist_{i}"):
                    st.session_state.reuse_question = q['question']
                    st.session_state.auto_submit = True
                    st.rerun()
                st.caption(f"{q['timestamp']} • {q['rows']} rows" if q['success'] else f"{q['timestamp']} • Error")
        else:
            st.info("No queries yet")
        st.divider()
        
        st.markdown("### 💡 Example Questions")
        st.markdown("**Simple:**")
        examples_simple = [
            "Show top 5 products by revenue",
            "Show total revenue by region",
            "Show monthly sales for 2024",
            "Which customer spent the most money?"
        ]
        for ex in examples_simple:
            if st.button(f"📌 {ex}", key=f"simple_{ex[:15]}"):
                st.session_state.example_question = ex
                st.session_state.auto_submit = True
                st.rerun()
        
        st.markdown("**JOIN Queries:**")
        examples_join = [
            "Show customers with their total revenue and segment",
            "Show products with total sales and supplier information",
            "Show sales by region with manager name"
        ]
        for ex in examples_join:
            if st.button(f"🔗 {ex}", key=f"join_{ex[:15]}"):
                st.session_state.example_question = ex
                st.session_state.auto_submit = True
                st.rerun()
        
        st.markdown("**Complex:**")
        examples_complex = [
            "Show top 3 products by revenue in each region",
            "Compare revenue by quarter for 2023 vs 2024",
            "Find customers who spent above average"
        ]
        for ex in examples_complex:
            if st.button(f"⚡ {ex}", key=f"complex_{ex[:15]}"):
                st.session_state.example_question = ex
                st.session_state.auto_submit = True
                st.rerun()
    
    # ==================== MAIN CONTENT ====================
    if 'reuse_question' in st.session_state:
        question = st.session_state.reuse_question
        del st.session_state.reuse_question
    elif 'example_question' in st.session_state:
        question = st.session_state.example_question
        del st.session_state.example_question
    else:
        question = st.text_area(
            "💬 Ask your question in plain English:",
            placeholder="Example: Show me the top 10 products by revenue for Q4 2024",
            height=80,
            key="question_input"
        )
    
    # ==================== SUBMIT LOGIC ====================
    auto_submit = st.session_state.get('auto_submit', False)
    
    col1, col2 = st.columns([1, 4])
    with col1:
        submit = st.button("🚀 Generate", type="primary", use_container_width=True)
    
    if auto_submit:
        submit = True
        st.session_state.auto_submit = False
    
    # ==================== PROCESS QUERY ====================
    if submit and question:
        with st.spinner("🤔 Analyzing and generating SQL..."):
            schema_info = get_table_schema()
            if not schema_info:
                st.error("Could not load database schema")
                return
            
            sql = generate_sql(question, schema_info, api_key, model)
            
            if sql:
                with st.expander("🔍 View Generated SQL", expanded=True):
                    st.code(sql, language='sql')
                
                with st.spinner("⚡ Executing query..."):
                    df, error = execute_sql(sql)
                
                if error:
                    st.markdown(f'<div class="error-box">❌ {error}</div>', unsafe_allow_html=True)
                    save_to_history(question, sql, False, error=error)
                else:
                    st.markdown(f'<div class="success-box">✅ Query executed successfully! {len(df)} rows returned</div>', unsafe_allow_html=True)
                    save_to_history(question, sql, True, len(df))
                    
                    st.subheader("📋 Results")
                    st.dataframe(df, use_container_width=True, height=400)
                    
                    if len(df) > 0:
                        st.subheader("📊 Visualizations")
                        fig = auto_generate_chart(df, sql)
                        if fig:
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.info("ℹ️ Data format not suitable for automatic charting")
                    
                    csv = df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Download CSV",
                        data=csv,
                        file_name=f"query_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
            else:
                st.error("Failed to generate SQL. Please rephrase your question.")
    
    elif submit and not question:
        st.warning("⚠️ Please enter a question first")
    
    # ==================== DATABASE SCHEMA REFERENCE ====================
    with st.expander("📖 Database Schema Reference", expanded=False):
        schema_info = get_table_schema()
        if schema_info:
            for table_name, info in schema_info.items():
                st.markdown(f"**Table: `{table_name}`** ({info['row_count']:,} rows)")
                col_names = [f"`{col['name']}` ({col['type']})" for col in info['columns']]
                st.write(" | ".join(col_names))
                if info['sample']:
                    st.caption(f"Sample: {info['sample'][0]}")
                st.divider()

if __name__ == "__main__":
    main()