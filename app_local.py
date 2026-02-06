import streamlit as st
import pandas as pd
import pymysql

# ────────────────────────────────────────────────
# Page configuration
# ────────────────────────────────────────────────
st.set_page_config(
    page_title="Medical Database Assistant",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🏥 Medical Database Assistant")
st.markdown("---")

# ────────────────────────────────────────────────
# Sidebar - Connection & Status (Local friendly)
# ────────────────────────────────────────────────
with st.sidebar:
    st.header("🔌 Connection Status")

    try:
        db_config = st.secrets["medical_db"]
        GROQ_API_KEY = st.secrets.get("groq_api_key", None)

        st.success("✅ Secrets loaded from .streamlit/secrets.toml")
        
        if GROQ_API_KEY:
            st.success("✅ GROQ API Key: Loaded")
        else:
            st.warning("⚠️ GROQ API Key: Not found in secrets.toml")

    except Exception as e:
        st.error("❌ Could not load secrets. Check .streamlit/secrets.toml file.")
        st.stop()

    st.markdown("---")
    st.header("📋 Database Info")
    st.info(f"**Host:** {db_config['host']}")
    st.info(f"**Database:** {db_config['database']}")
    st.info(f"**User:** {db_config['user']}")

# ────────────────────────────────────────────────
# Database connection (cached)
# ────────────────────────────────────────────────
@st.cache_resource
def get_db_connection():
    try:
        conn = pymysql.connect(
            host=db_config["host"],
            user=db_config["user"],
            password=db_config["password"],
            database=db_config["database"],
            port=int(db_config.get("port", 3306)),
            charset=db_config.get("charset", "utf8mb4"),
            connect_timeout=10
        )
        return conn
    except Exception as e:
        st.error(f"❌ Database connection failed: {str(e)}")
        return None


# Try to connect
conn = get_db_connection()

if not conn:
    st.error("Cannot connect to database. Please check .streamlit/secrets.toml")
    st.stop()

with st.sidebar:
    st.success("✅ Database Connected!")

# ────────────────────────────────────────────────
# Main Tabs (same as before)
# ────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["🔍 Browse Data", "🔎 Search Records", "➕ Add Record"])

# Tab 1: Browse Data
with tab1:
    st.header("📋 Browse Medical Records")
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SHOW TABLES")
            tables = [row[list(row.keys())[0]] for row in cursor.fetchall()]
        
        if tables:
            selected_table = st.selectbox("Select Table", tables)
            if selected_table:
                st.subheader(f"Table: {selected_table}")
                query = f"SELECT * FROM `{selected_table}` LIMIT 100"
                with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                    cursor.execute(query)
                    rows = cursor.fetchall()
                    df = pd.DataFrame(rows)
                if not df.empty:
                    st.dataframe(df, use_container_width=True)
                    st.info(f"Showing first {len(df)} records")
                else:
                    st.warning("No data found in this table")
        else:
            st.warning("No tables found in database")
    except Exception as e:
        st.error(f"Error reading data: {str(e)}")

# Tab 2: Search
with tab2:
    st.header("🔍 Search Medical Records")
    col1, col2 = st.columns(2)
    with col1:
        search_table = st.selectbox(
            "Search in table",
            ["patients", "appointments", "doctors"],  # ← change to your real tables
            key="search_table_local"
        )
    with col2:
        search_column = st.text_input("Column name", value="name")
    search_value = st.text_input("Search value")
    
    if st.button("🔍 Search") and search_value:
        try:
            query = f"""
                SELECT * FROM `{search_table}`
                WHERE `{search_column}` LIKE %s
                LIMIT 50
            """
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute(query, (f"%{search_value}%",))
                rows = cursor.fetchall()
                df = pd.DataFrame(rows)
            if not df.empty:
                st.success(f"Found {len(df)} records")
                st.dataframe(df, use_container_width=True)
            else:
                st.warning("No records found")
        except Exception as e:
            st.error(f"Search error: {str(e)}")

# Tab 3: Add Record (example)
with tab3:
    st.header("➕ Add New Record")
    st.info("Make sure the table exists in your database first.")
    if st.button("💾 Insert Sample Patient"):
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO patients (name, age, phone, diagnosis)
                    VALUES (%s, %s, %s, %s)
                """, ("Test Patient Local", 35, "9876543210", "Sample Checkup"))
                conn.commit()
            st.success("✅ Sample record added!")
        except Exception as e:
            st.error(f"Insert error: {str(e)}")

st.markdown("---")
st.caption("Local development version – using .streamlit/secrets.toml")