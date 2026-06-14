import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
import sqlite3
import gspread
from google.oauth2.service_account import Credentials
import json

st.set_page_config(page_title="Gestión de Reciclaje - Rafael Gil", layout="wide")

st.title("♻️ Gestión de Reciclaje y Valorización")
st.subheader("Rafael Gil Terán")
st.caption("Datos guardados en Google Sheets + Base Local")

# ==================== GOOGLE SHEETS ====================
st.sidebar.header("🔗 Google Sheets")
use_sheets = st.sidebar.checkbox("Guardar en Google Sheets", value=True)

if use_sheets:
    credentials_json = st.sidebar.text_area("Pega aquí tu JSON de credenciales (Service Account)", height=200)
    
    if credentials_json:
        try:
            creds_dict = json.loads(credentials_json)
            creds = Credentials.from_service_account_info(creds_dict, scopes=["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
            client = gspread.authorize(creds)
            sheet = client.open("Residuos_Rafael").sheet1
            st.sidebar.success("✅ Conectado a Google Sheets")
        except:
            st.sidebar.error("Error al conectar. Verifica el JSON")

# Base de datos local
conn = sqlite3.connect('residuos.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS residuos (
    id INTEGER PRIMARY KEY, fecha TEXT, tipo TEXT, cantidad REAL, unidad TEXT,
    origen TEXT, valorizacion TEXT, valor_ganancia REAL, notas TEXT
)''')
conn.commit()

# Registro
with st.expander("📝 Registrar Nueva Entrada", expanded=True):
    with st.form("registro"):
        col1, col2 = st.columns(2)
        fecha = col1.date_input("Fecha", datetime.today())
        tipo = col2.selectbox("Tipo de Material", ["Papel", "Cartón", "Plástico", "Vidrio", "Orgánico", "Madera", "Latas", "Metales", "Peligroso", "Residuo No Valorizable", "Otros"])
        
        col3, col4 = st.columns(2)
        cantidad = col3.number_input("Cantidad", min_value=0.0, value=1000.0)
        unidad = col4.selectbox("Unidad", ["ton", "kg"])
        
        origen = st.text_input("Origen / Cliente", "Ej: Empresa XYZ")
        valorizacion = st.selectbox("Valorización", ["Reciclaje", "Compost", "Disposición Final", "Otro"])
        notas = st.text_area("Notas")
        
        if st.form_submit_button("💾 Guardar Registro", type="primary"):
            ganancia_por_ton = {"Papel":130,"Cartón":85,"Plástico":260,"Vidrio":65,"Orgánico":45,
                               "Madera":75,"Latas":320,"Metales":380,"Peligroso":-150,
                               "Residuo No Valorizable":0,"Otros":40}
            factor = 1 if unidad == "ton" else 0.001
            ganancia = round(cantidad * ganancia_por_ton.get(tipo, 50) * factor * 950, 2)
            
            c.execute("INSERT INTO residuos VALUES (NULL,?,?,?,?,?,?,?,?)", 
                      (str(fecha), tipo, cantidad, unidad, origen, valorizacion, ganancia, notas))
            conn.commit()
            st.success("✅ Guardado en base local")

            # Guardar en Google Sheets
            if use_sheets and 'sheet' in locals():
                try:
                    row = [str(fecha), tipo, cantidad, unidad, origen, valorizacion, ganancia, notas]
                    sheet.append_row(row)
                    st.success("✅ También guardado en Google Sheets")
                except:
                    st.warning("No se pudo guardar en Google Sheets")

# Mostrar datos
st.header("📊 Dashboard")
df = pd.read_sql_query("SELECT * FROM residuos ORDER BY fecha DESC", conn)

if not df.empty:
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Gestionado", f"{df['cantidad'].sum():,.1f} ton")
    col2.metric("Valor Estimado", f"${df['valor_ganancia'].sum():,.2f}")
    
    fig = px.pie(df, names='valorizacion', values='cantidad', title="Reciclaje vs Disposición Final")
    st.plotly_chart(fig, use_container_width=True)
    
    st.dataframe(df, use_container_width=True)
else:
    st.info("No hay registros aún")

st.caption("Herramienta Profesional con Google Sheets - Rafael Gil Terán")
