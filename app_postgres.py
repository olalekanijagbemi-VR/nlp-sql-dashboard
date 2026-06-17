"""
PostgreSQL Version - AI-Powered SQL Analytics Dashboard
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import re
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

# ==================== PAGE CONFIG ====================
st.set_page_config(
    page_title="AI SQL Analytics Dashboard (PostgreSQL)",
    page_icon="🐘",
    layout="wide"
)

# ==================== POSTGRESQL CONNECTION ====================
def get_db_connection():
    """Create PostgreSQL connection using secrets or env"""
    try:
        # For Streamlit Cloud
        conn = psycopg2.connect(st.secrets["DATABASE_URL"])
        return conn
    except:
        # For local testing
        conn = psycopg2.connect(
            host="db.sopxwbreracachgzvlcl.supabase.co",
            port="5432",
            database="postgres",
            user="postgres",
            password="Postgres101"
        )
        return conn

@st.cache_data(ttl=300)
def get_table_schema():
    """Get schema from PostgreSQL"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get all tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        tables = [t[0] for t in cursor.fetchall()]
        
        schema_info = {}
        for table in tables:
            # Get columns
            cursor.execute(f"""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = '{table}'
            """)
            columns = cursor.fetchall()
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            row_count = cursor.fetchone()[0]
            
            # Get sample
            cursor.execute(f"SELECT * FROM {table} LIMIT 3")
            sample = cursor.fetchall()
            if sample:
                colnames = [desc[0] for desc in cursor.description]
                sample_dict = [dict(zip(colnames, row)) for row in sample]
            else:
                sample_dict = []
            
            schema_info[table] = {
                "columns": [{"name": c[0], "type": c[1]} for c in columns],
                "row_count": row_count,
                "sample": sample_dict
            }
        
        conn.close()
        return schema_info
    except Exception as e:
        conn.close()
        return None

@st.cache_data(ttl=60)
def get_table_stats():
    """Get database stats from PostgreSQL"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        stats = {}
        cursor.execute("SELECT COALESCE(SUM(revenue), 0) as total FROM sales")
        stats['total_revenue'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM sales")
        stats['total_transactions'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT customer) FROM sales")
        stats['unique_customers'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT product) FROM sales")
        stats['unique_products'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT MIN(date), MAX(date) FROM sales")
        min_date, max_date = cursor.fetchone()
        stats['min_date'] = min_date
        stats['max_date'] = max_date
        
        conn.close()
        return stats
    except Exception as e:
        conn.close()
        return None

def execute_sql(sql_query):
    """Execute SQL query on PostgreSQL"""
    if not sql_query:
        return None, "No query provided"
    
    try:
        # Clean SQL
        sql_query = sql_query.strip()
        sql_query = re.sub(r';+$', '', sql_query)
        
        # Security check
        dangerous = ['drop', 'delete', 'insert', 'update', 'alter', 'create', 'truncate']
        if any(k in sql_query.lower() for k in dangerous):
            return None, f"⚠️ Security: {dangerous} operations are not allowed"
        
        conn = get_db_connection()
        result_df = pd.read_sql_query(sql_query, conn)
        conn.close()
        return result_df, None
    except Exception as e:
        return None, str(e)

# ==================== GROQ AI FUNCTIONS ====================
def generate_sql(question, schema_info, api_key, model="llama-3.1-8b-instant"):
    if not schema_info:
        return None
    
    schema_text = ""
    for table_name, info in schema_info.items():
        columns_desc = ", ".join([f"{col['name']} ({col['type']})" for col in info['columns']])
        schema_text += f"\nTable: {table_name}\nColumns: {columns_desc}\nRows: {info['row_count']:,}\n"
        if info['sample']:
            schema_text += f"Sample: {info['sample'][0]}\n"
    
    relationships = """
RELATIONSHIPS:
- sales.customer -> customers.customer_name (JOIN on customer = customer_name)
- sales.product -> products.product_name (JOIN on product = product_name)
- sales.region -> regions.region_name (JOIN on region = region_name)
"""
    
    prompt = f"""Convert to PostgreSQL SQL.

DATABASE SCHEMA:
{schema_text}

{relationships}

CRITICAL RULES:
1. Return ONLY ONE SQL query - absolutely NO multiple statements
2. Do NOT include any explanations, comments, or extra text
3. Do NOT include semicolons
4. Use PostgreSQL syntax
5. For aggregation queries, do NOT add LIMIT
6. For non-aggregation queries, add LIMIT 100

Question: {question}

SQL:"""
    
    try:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are a PostgreSQL expert. Return ONLY ONE SQL query."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1,
            "max_tokens": 500
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            sql_query = result['choices'][0]['message']['content'].strip()
            
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
        else:
            st.error(f"Groq API error: {response.status_code}")
            return None
            
    except Exception as e:
        st.error(f"Groq API error: {str(e)}")
        return None

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
    <style>
        .main-header {
            background: linear-gradient(135deg, #336791 0%, #0064a5 100%);
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
        .elephant {
            font-size: 1.5rem;
            margin-right: 0.5rem;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1><span class="elephant">🐘</span> AI-Powered SQL Analytics (PostgreSQL)</h1>
        <p>Ask questions in plain English • Enterprise-grade database</p>
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
        
        model = st.selectbox("AI Model:", ["llama-3.1-8b-instant", "llama-3.3-70b-versatile", "gemma2-9b-it"], index=0)
        st.divider()
        
        st.markdown("### 🐘 PostgreSQL Database")
        try:
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
        except:
            st.info("🔄 Connect to Supabase first")
        
        st.divider()
        
        st.markdown("### 💡 Example Questions")
        examples = [
            "Show top 5 products by revenue",
            "Show total revenue by region",
            "Show customers with their total revenue and segment",
            "Show top 3 products by revenue in each region"
        ]
        for ex in examples:
            if st.button(f"📌 {ex}", key=ex):
                st.session_state.example_question = ex
                st.session_state.auto_submit = True
                st.rerun()
    
    # ==================== MAIN CONTENT ====================
    if 'example_question' in st.session_state:
        question = st.session_state.example_question
        del st.session_state.example_question
    else:
        question = st.text_area(
            "💬 Ask your question in plain English:",
            placeholder="Example: Show me the top 10 products by revenue for Q4 2024",
            height=80,
            key="question_input"
        )
    
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
                    st.error(f"❌ {error}")
                else:
                    st.success(f"✅ {len(df)} rows returned")
                    st.dataframe(df, use_container_width=True, height=400)
                    
                    csv = df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Download CSV",
                        data=csv,
                        file_name=f"query_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
            else:
                st.error("Failed to generate SQL")

if __name__ == "__main__":
    main()