import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
import sqlite3

st.set_page_config(page_title="Gestión de Reciclaje - Rafael Gil", layout="wide")

st.title("♻️ Gestión de Reciclaje y Valorización")
st.subheader("Rafael Gil Terán - Ingeniero en Recursos Naturales")
st.caption("Sistema Profesional")

# Base de datos
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
        
        origen = st.text_input("Cliente / Origen", "Ej: Empresa XYZ")
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
            st.success("✅ Registro guardado!")

# Dashboard
st.header("📊 Dashboard General")
df = pd.read_sql_query("SELECT * FROM residuos ORDER BY fecha DESC", conn)

if not df.empty:
    total = df['cantidad'].sum()
    ganancia_total = df['valor_ganancia'].sum()
    reciclado = df[df['valorizacion'].isin(["Reciclaje", "Compost"])]['cantidad'].sum()
    porc = (reciclado / total * 100) if total > 0 else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Gestionado", f"{total:,.1f} ton")
    col2.metric("Valor Estimado", f"${ganancia_total:,.2f}")
    col3.metric("Tasa de Reciclaje", f"{porc:.1f}%")

    fig = px.pie(df, names='valorizacion', values='cantidad', title="Reciclaje vs Disposición Final")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Valorización por Material")
    resumen = df.groupby('tipo').agg(
        Total=('cantidad', 'sum'),
        Reciclado=('cantidad', lambda x: x[df.loc[x.index, 'valorizacion'].isin(["Reciclaje","Compost"])].sum()),
        Ganancia=('valor_ganancia', 'sum')
    ).reset_index()
    resumen['% Reciclaje'] = (resumen['Reciclado'] / resumen['Total'] * 100).round(1)
    st.dataframe(resumen, use_container_width=True)

st.caption("Herramienta Profesional - Rafael Gil Terán")
