"""
NLP to SQL Analytics Dashboard - Fixed SQL Cleaning
"""

import streamlit as st
import sqlite3
import pandas as pd
from groq import Groq
import re
import os
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="AI SQL Analytics Dashboard",
    page_icon="📊",
    layout="wide"
)

# Get absolute path to database
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sales.db")

# Simple function to check if database exists
def db_exists():
    return os.path.exists(DB_PATH)

# Get table schema
def get_table_schema():
    """Extract database schema for AI prompt"""
    if not db_exists():
        return None
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("PRAGMA table_info(sales)")
        columns = cursor.fetchall()
        cursor.execute("SELECT COUNT(*) FROM sales")
        total_rows = cursor.fetchone()[0]
        cursor.execute("SELECT DISTINCT product FROM sales LIMIT 5")
        products = [p[0] for p in cursor.fetchall()]
        
        return {
            "columns": [{"name": col[1], "type": col[2]} for col in columns],
            "total_rows": total_rows,
            "products": products
        }
    except Exception as e:
        return None
    finally:
        conn.close()

# Generate SQL - IMPROVED CLEANING
def generate_sql(question, schema, api_key):
    if schema is None:
        return None
    
    client = Groq(api_key=api_key)
    
    columns_desc = ", ".join([f"{col['name']} ({col['type']})" for col in schema['columns']])
    
    prompt = f"""Convert to SQLite SQL. Table 'sales' has columns: {columns_desc}
Total rows: {schema['total_rows']:,}
Products: {', '.join(schema['products'])}

IMPORTANT RULES:
1. Return ONLY the SQL query, no explanations, no comments
2. Do NOT include semicolons at the end
3. Do NOT include LIMIT for aggregation queries (COUNT, SUM, AVG, GROUP BY)
4. For non-aggregation queries, add LIMIT 1000

Question: {question}

SQL:"""
    
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=500
        )
        
        sql_query = response.choices[0].message.content.strip()
        
        # Remove markdown code blocks
        sql_query = re.sub(r'```sql\n?', '', sql_query)
        sql_query = re.sub(r'```\n?', '', sql_query)
        
        # Remove any comments (-- or /* */)
        sql_query = re.sub(r'--.*?(\n|$)', '\n', sql_query)
        sql_query = re.sub(r'/\*.*?\*/', '', sql_query, flags=re.DOTALL)
        
        # Remove trailing semicolons
        sql_query = sql_query.rstrip(';')
        
        # Clean up extra whitespace
        sql_query = ' '.join(sql_query.split())
        
        # Check if query is an aggregation
        sql_lower = sql_query.lower()
        is_aggregation = any(word in sql_lower for word in ['count(', 'sum(', 'avg(', 'group by', 'max(', 'min('])
        
        # Add LIMIT only for non-aggregation queries
        if not is_aggregation and 'limit' not in sql_lower:
            sql_query += " LIMIT 1000"
        
        return sql_query
    except Exception as e:
        st.error(f"Error generating SQL: {str(e)}")
        return None

# Execute SQL
def execute_sql(sql_query):
    if not db_exists():
        return None, "Database not found"
    
    try:
        # Clean the SQL more aggressively
        sql_query = sql_query.strip()
        sql_query = re.sub(r';+$', '', sql_query)  # Remove trailing semicolons
        
        conn = sqlite3.connect(DB_PATH)
        
        # Security check
        dangerous = ['drop', 'delete', 'insert', 'update', 'alter', 'create', 'truncate']
        if any(k in sql_query.lower() for k in dangerous):
            conn.close()
            return None, "Dangerous operation not allowed"
        
        # Execute query
        result = pd.read_sql_query(sql_query, conn)
        conn.close()
        return result, None
    except Exception as e:
        return None, str(e)

# Main app
def main():
    st.title("📊 AI-Powered SQL Analytics Dashboard")
    st.caption("Ask questions in plain English")
    
    # Sidebar
    with st.sidebar:
        st.header("🔑 API Key")
        api_key = st.text_input("Groq API Key:", type="password")
        if not api_key:
            st.warning("Enter your Groq API key")
            st.stop()
        st.success("✅ Ready")
        
        st.divider()
        st.subheader("📁 Database")
        
        if db_exists():
            try:
                conn = sqlite3.connect(DB_PATH)
                count = pd.read_sql_query("SELECT COUNT(*) as c FROM sales", conn)['c'][0]
                conn.close()
                st.metric("Total Records", f"{count:,}")
                st.success("✅ Database connected")
            except Exception as e:
                st.error(f"Error: {str(e)}")
        else:
            st.error("Database not found. Run: python setup_database.py")
            st.stop()
        
        st.divider()
        st.subheader("💡 Examples")
        examples = [
            "Show top 5 products by revenue",
            "Show total revenue by region",
            "Show monthly sales for 2024",
            "Which customer spent the most money?",
            "Show average order value by product category"
        ]
        for ex in examples:
            if st.button(ex, key=ex):
                st.session_state.example = ex
                st.rerun()
    
    # Check database
    if not db_exists():
        st.error("⚠️ Database not found! Please run: python setup_database.py")
        st.stop()
    
    # Question input
    if 'example' in st.session_state:
        question = st.session_state.example
        del st.session_state.example
    else:
        question = st.text_area("💬 Ask your question:", height=100)
    
    col1, col2 = st.columns([1, 4])
    with col1:
        submit = st.button("🚀 Generate & Execute", type="primary")
    
    if submit and question:
        with st.spinner("Converting to SQL..."):
            schema = get_table_schema()
            if schema is None:
                st.error("Could not load database schema")
                return
            
            sql = generate_sql(question, schema, api_key)
            
            if sql:
                st.code(sql, language='sql')
                
                with st.spinner("Executing..."):
                    df, error = execute_sql(sql)
                
                if error:
                    st.error(f"Error: {error}")
                else:
                    st.success(f"✅ {len(df)} rows returned")
                    st.dataframe(df, use_container_width=True)
                    
                    # Download CSV
                    csv = df.to_csv(index=False).encode()
                    st.download_button(
                        "📥 Download CSV", 
                        csv, 
                        f"query_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                    )
    
    elif submit and not question:
        st.warning("⚠️ Please enter a question first")

if __name__ == "__main__":
    main()