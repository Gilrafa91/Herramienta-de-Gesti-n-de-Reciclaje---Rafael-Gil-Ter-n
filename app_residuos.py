import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
from fpdf import FPDF
import sqlite3

st.set_page_config(page_title="Gestión de Reciclaje - Rafael Gil", layout="wide")

st.title("♻️ Gestión de Reciclaje y Valorización")
st.subheader("Rafael Gil Terán - Ingeniero en Recursos Naturales")
st.caption("Sistema Profesional de Trazabilidad, Valorización y Certificados")

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

# Filtros
st.header("🔎 Filtros")
col_f1, col_f2 = st.columns(2)
fecha_inicio = col_f1.date_input("Desde", datetime.today().replace(day=1))
fecha_fin = col_f2.date_input("Hasta", datetime.today())

df = pd.read_sql_query("SELECT * FROM residuos ORDER BY fecha DESC", conn)
if not df.empty:
    df['fecha'] = pd.to_datetime(df['fecha'])
    df_filtrado = df[(df['fecha'] >= pd.to_datetime(fecha_inicio)) & (df['fecha'] <= pd.to_datetime(fecha_fin))]
else:
    df_filtrado = pd.DataFrame()

# ==================== DASHBOARD ====================
st.header("📊 Dashboard General")

if not df_filtrado.empty:
    total = df_filtrado['cantidad'].sum()
    ganancia_total = df_filtrado['valor_ganancia'].sum()
    reciclado = df_filtrado[df_filtrado['valorizacion'].isin(["Reciclaje", "Compost"])]['cantidad'].sum()
    porc_general = (reciclado / total * 100) if total > 0 else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Gestionado", f"{total:,.1f} ton")
    col2.metric("Valor Estimado", f"${ganancia_total:,.2f}")
    col3.metric("Tasa de Reciclaje", f"{porc_general:.1f}%")

    # Gráfico Circular
    fig_pie = px.pie(df_filtrado, names='valorizacion', values='cantidad', title="Reciclaje vs Disposición Final")
    st.plotly_chart(fig_pie, use_container_width=True)

    # Gráfico de Barras Mensual
    st.subheader("📈 Cantidad por Mes")
    df_filtrado['Mes'] = df_filtrado['fecha'].dt.strftime('%Y-%m')
    mensual = df_filtrado.groupby('Mes')['cantidad'].sum().reset_index()
    fig_bar = px.bar(mensual, x='Mes', y='cantidad', title="Cantidad Total por Mes", color='cantidad', color_continuous_scale='Blues')
    st.plotly_chart(fig_bar, use_container_width=True)

    # Por Material
    st.subheader("Valorización por Material")
    resumen = df_filtrado.groupby('tipo').agg(
        Total=('cantidad', 'sum'),
        Reciclado=('cantidad', lambda x: x[df_filtrado.loc[x.index, 'valorizacion'].isin(["Reciclaje","Compost"])].sum()),
        Ganancia=('valor_ganancia', 'sum')
    ).reset_index()
    resumen['% Reciclaje'] = (resumen['Reciclado'] / resumen['Total'] * 100).round(1)
    st.dataframe(resumen, use_container_width=True)

# ==================== CERTIFICADO PDF COMPLETO ====================
st.header("🎖️ Certificados de Reciclaje")

if not df_filtrado.empty:
    registro = st.selectbox("Seleccionar registro para certificar", 
                           options=df_filtrado.index,
                           format_func=lambda x: f"{df_filtrado.loc[x,'fecha'].date()} | {df_filtrado.loc[x,'tipo']} - {df_filtrado.loc[x,'cantidad']} {df_filtrado.loc[x,'unidad']}")
    
    if st.button("📜 Generar Certificado PDF Completo", type="primary"):
        row = df_filtrado.loc[registro]
        
        pdf = FPDF(orientation='P', unit='mm', format='A4')
        pdf.add_page()
        
        # Cabecera
        pdf.set_font("Arial", 'B', 22)
        pdf.cell(0, 20, "CERTIFICADO DE RECICLAJE", ln=1, align='C')
        
        pdf.set_font("Arial", size=12)
        pdf.cell(0, 10, f"Certificado N° REC-{int(row['id']):04d}", ln=1, align='C')
        pdf.cell(0, 10, f"Fecha de Emisión: {datetime.today().strftime('%Y-%m-%d')}", ln=1, align='C')
        pdf.ln(10)
        
        # Datos
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, "Datos de la Operación", ln=1)
        pdf.set_font("Arial", size=12)
        pdf.cell(0, 8, f"Cliente / Origen: {row['origen']}", ln=1)
        pdf.cell(0, 8, f"Material Reciclado: {row['tipo']}", ln=1)
        pdf.cell(0, 8, f"Cantidad: {row['cantidad']} {row['unidad']}", ln=1)
        pdf.cell(0, 8, f"Tipo de Valorización: {row['valorizacion']}", ln=1)
        pdf.cell(0, 8, f"Valor Estimado: ${row['valor_ganancia']:,.2f}", ln=1)
        pdf.ln(15)
        
        # Mensaje final
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "Este documento certifica que el material ha sido gestionado", ln=1, align='C')
        pdf.cell(0, 10, "responsablemente según principios de Economía Circular.", ln=1, align='C')
        pdf.ln(10)
        pdf.cell(0, 10, "Rafael Gil Terán", ln=1, align='C')
        pdf.cell(0, 10, "Ingeniero en Recursos Naturales", ln=1, align='C')
        
        filename = f"Certificado_REC_{row['tipo']}_{datetime.today().strftime('%Y%m%d')}.pdf"
        pdf.output(filename)
        
        with open(filename, "rb") as f:
            st.download_button("⬇️ Descargar Certificado PDF", f, file_name=filename, mime="application/pdf")
        st.success("✅ Certificado generado correctamente!")

st.caption("Herramienta Profesional - Rafael Gil Terán")
