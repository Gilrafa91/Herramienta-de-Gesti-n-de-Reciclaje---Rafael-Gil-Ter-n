import streamlit as st
import pandas as pd
from datetime import datetime
import sqlite3

st.set_page_config(page_title="Gestión de Reciclaje", layout="wide")

st.title("♻️ Gestión de Reciclaje")
st.subheader("Rafael Gil Terán")

# Base de datos
conn = sqlite3.connect('residuos.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS residuos (
    id INTEGER PRIMARY KEY, fecha TEXT, tipo TEXT, cantidad REAL, unidad TEXT,
    origen TEXT, valorizacion TEXT, valor_ganancia REAL, notas TEXT
)''')
conn.commit()

# Registro
with st.expander("📝 Registrar Entrada", expanded=True):
    with st.form("registro"):
        col1, col2 = st.columns(2)
        fecha = col1.date_input("Fecha", datetime.today())
        tipo = col2.selectbox("Material", ["Papel", "Cartón", "Plástico", "Vidrio", "Orgánico", "Madera", "Latas", "Metales", "Otros"])
        
        col3, col4 = st.columns(2)
        cantidad = col3.number_input("Cantidad", min_value=0.0, value=1000.0)
        unidad = col4.selectbox("Unidad", ["ton", "kg"])
        
        origen = st.text_input("Cliente / Origen", "Ej: Empresa XYZ")
        valorizacion = st.selectbox("Valorización", ["Reciclaje", "Disposición Final", "Otro"])
        notas = st.text_area("Notas")
        
        if st.form_submit_button("💾 Guardar", type="primary"):
            ganancia = round(cantidad * 100 * (950 if unidad == "ton" else 0.95), 2)
            c.execute("INSERT INTO residuos VALUES (NULL,?,?,?,?,?,?,?,?)", 
                      (str(fecha), tipo, cantidad, unidad, origen, valorizacion, ganancia, notas))
            conn.commit()
            st.success("✅ Guardado!")

# Ver registros
st.header("📋 Registros")
df = pd.read_sql_query("SELECT * FROM residuos ORDER BY fecha DESC", conn)

if not df.empty:
    st.dataframe(df, use_container_width=True)
    
    col1, col2 = st.columns(2)
    col1.metric("Total Gestionado", f"{df['cantidad'].sum():,.1f} ton")
    col2.metric("Valor Estimado", f"${df['valor_ganancia'].sum():,.2f}")
else:
    st.info("No hay registros todavía")

st.caption("Versión Ultra Simple - Rafael Gil Terán")
