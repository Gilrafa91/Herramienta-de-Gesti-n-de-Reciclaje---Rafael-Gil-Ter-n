import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
from fpdf import FPDF
import sqlite3

st.set_page_config(page_title="RAFAEL GIL | Gestión de Reciclaje", layout="wide", page_icon="♻️")

# Estilo profesional
st.markdown("""
<style>
    .main-header {font-size: 2.5rem; color: #1E3A8A; font-weight: bold;}
    .metric-card {background-color: #f0f7ff; padding: 15px; border-radius: 10px; border: 1px solid #bfdbfe;}
</style>
""", unsafe_allow_html=True)

# Configuración
if 'moneda' not in st.session_state:
    st.session_state.moneda = "CLP"  # Predeterminado Chile

st.sidebar.header("⚙️ Configuración")
moneda = st.sidebar.selectbox("Moneda", ["CLP", "USD", "EUR"], index=0)
st.session_state.moneda = moneda
simbolo = {"CLP": "$", "USD": "US$", "EUR": "€"}[moneda]

st.title("♻️ RAFAEL GIL TERÁN")
st.markdown("<h2 style='color: #1E3A8A;'>Gestión Profesional de Residuos y Reciclaje</h2>", unsafe_allow_html=True)
st.caption("Ingeniero en Recursos Naturales | Especialista en Valorización y Economía Circular")

st.markdown("---")

# Base de datos
conn = sqlite3.connect('residuos.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS residuos (
    id INTEGER PRIMARY KEY, fecha TEXT, tipo TEXT, cantidad REAL, unidad TEXT,
    origen TEXT, valorizacion TEXT, valor_ganancia REAL, co2_evitado REAL, notas TEXT
)''')
conn.commit()

# Registro
with st.expander("📋 Registrar Nueva Entrada", expanded=True):
    with st.form("registro"):
        col1, col2, col3 = st.columns(3)
        fecha = col1.date_input("Fecha", datetime.today())
        tipo = col2.selectbox("Tipo de Material", ["Papel", "Cartón", "Plástico", "Vidrio", "Orgánico", "Madera", "Latas", "Metales", "Peligroso", "Residuo No Valorizable", "Otros"])
        valorizacion = col3.selectbox("Valorización", ["Reciclaje", "Compost", "Disposición Final", "Otro"])
        
        col4, col5 = st.columns(2)
        cantidad = col4.number_input("Cantidad", min_value=0.0, value=1000.0)
        unidad = col5.selectbox("Unidad", ["ton", "kg"])
        
        origen = st.text_input("Origen / Cliente", "Ej: Empresa XYZ")
        notas = st.text_area("Notas / Observaciones", height=80)
        
        if st.form_submit_button("💾 Guardar Registro", type="primary"):
            ganancia_por_ton = {"Papel":130,"Cartón":85,"Plástico":260,"Vidrio":65,"Orgánico":45,
                               "Madera":75,"Latas":320,"Metales":380,"Peligroso":-150,
                               "Residuo No Valorizable":0,"Otros":40}
            factor = 1 if unidad == "ton" else 0.001
            ganancia = round(cantidad * ganancia_por_ton.get(tipo, 50) * factor * {"CLP":950,"USD":1,"EUR":0.92}.get(moneda,1), 2)
            co2 = round(cantidad * 1500 * factor * (1 if valorizacion in ["Reciclaje", "Compost"] else 0.2), 1)
            
            c.execute("INSERT INTO residuos VALUES (NULL,?,?,?,?,?,?,?,?,?)", 
                      (str(fecha), tipo, cantidad, unidad, origen, valorizacion, ganancia, co2, notas))
            conn.commit()
            st.success("✅ Registro guardado correctamente")

# Filtros y Dashboard
st.header("📊 Dashboard General")

col_f1, col_f2 = st.columns(2)
fecha_inicio = col_f1.date_input("Desde", datetime.today().replace(day=1))
fecha_fin = col_f2.date_input("Hasta", datetime.today())

df = pd.read_sql_query("SELECT * FROM residuos ORDER BY fecha DESC", conn)
if not df.empty:
    df['fecha'] = pd.to_datetime(df['fecha'])
    df_filtrado = df[(df['fecha'] >= pd.to_datetime(fecha_inicio)) & (df['fecha'] <= pd.to_datetime(fecha_fin))]
else:
    df_filtrado = pd.DataFrame()

if not df_filtrado.empty:
    total = df_filtrado['cantidad'].sum()
    ganancia_total = df_filtrado['valor_ganancia'].sum()
    co2_total = df_filtrado['co2_evitado'].sum()
    porc = (df_filtrado[df_filtrado['valorizacion'].isin(["Reciclaje", "Compost"])]['cantidad'].sum() / total * 100) if total > 0 else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Gestionado", f"{total:,.1f} ton")
    col2.metric("Valor Estimado", f"{simbolo}{ganancia_total:,.2f}")
    col3.metric("CO₂ Evitado", f"{co2_total:,.1f} kg")
    col4.metric("Tasa de Reciclaje", f"{porc:.1f}%")

    # Gráfico Circular
    fig = px.pie(df_filtrado, names='valorizacion', values='cantidad', title="Distribución General")
    st.plotly_chart(fig, use_container_width=True)

# Certificados (mantengo la versión corregida)
st.header("🎖️ Certificados de Reciclaje")

if not df_filtrado.empty:
    registro = st.selectbox("Seleccionar registro", options=df_filtrado.index,
                           format_func=lambda x: f"{df_filtrado.loc[x,'fecha'].date()} | {df_filtrado.loc[x,'tipo']} - {df_filtrado.loc[x,'cantidad']} {df_filtrado.loc[x,'unidad']}")
    
    if st.button("📜 Generar Certificado PDF", type="primary"):
        row = df_filtrado.loc[registro]
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 20)
        pdf.cell(0, 20, "CERTIFICADO DE RECICLAJE", ln=1, align='C')
        pdf.set_font("Arial", size=12)
        pdf.cell(0, 10, f"Certificado N° REC-{int(row['id']):04d}", ln=1, align='C')
        pdf.ln(10)
        pdf.cell(0, 8, f"Cliente: {row['origen']}", ln=1)
        pdf.cell(0, 8, f"Material: {row['tipo']}", ln=1)
        pdf.cell(0, 8, f"Cantidad: {row['cantidad']} {row['unidad']}", ln=1)
        pdf.cell(0, 8, f"Proceso: {row['valorizacion']}", ln=1)
        pdf.cell(0, 8, f"CO2 Evitado: {row['co2_evitado']} kg", ln=1)
        pdf.cell(0, 8, f"Valor: {simbolo}{row['valor_ganancia']:,.2f}", ln=1)
        pdf.ln(20)
        pdf.cell(0, 10, "Rafael Gil Terán - Ingeniero en Recursos Naturales", ln=1, align='C')
        
        filename = f"Certificado_{row['tipo']}_{datetime.today().strftime('%Y%m%d')}.pdf"
        pdf.output(filename)
        
        with open(filename, "rb") as f:
            st.download_button("⬇️ Descargar Certificado", f, file_name=filename)

st.caption("Herramienta Profesional desarrollada por Rafael Gil Terán")