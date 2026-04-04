# app.py
# Simulación de Gasoducto Trans-Andino - Con diseño mejorado
# Optimización de Procesos - Estudiante: [Tu nombre]

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# --------------------------------------------------
# Configuración de la página (más ancha y con ícono)
# --------------------------------------------------
st.set_page_config(
    page_title="Gasoducto Trans-Andino",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --------------------------------------------------
# Estilo CSS personalizado (sencillo, solo colores y bordes)
# --------------------------------------------------
st.markdown("""
<style>
    /* Fondo general más suave */
    .stApp {
        background-color: #f5f7fa;
    }
    /* Tarjetas para las métricas */
    .metric-card {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        text-align: center;
        border-left: 5px solid #2c3e50;
    }
    /* Encabezado principal */
    .main-header {
        background: linear-gradient(90deg, #1e466e, #2c3e50);
        padding: 1rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    /* Subtítulos */
    h2, h3 {
        color: #1e466e;
    }
    /* Sidebar más elegante */
    .css-1d391kg {
        background-color: #eef2f5;
    }
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# Encabezado principal
# --------------------------------------------------
st.markdown('<div class="main-header"><h1>📦 Gasoducto Trans-Andino</h1><p>Simulación de transporte de gas natural con compresión</p></div>', unsafe_allow_html=True)

# --------------------------------------------------
# Datos de tuberías (Tabla 1)
# --------------------------------------------------
tuberias = {
    "12": {"OD_mm": 323.8, "espesor_mm": 10.31, "costo_usd_m": 185},
    "16": {"OD_mm": 406.4, "espesor_mm": 12.70, "costo_usd_m": 260},
    "20": {"OD_mm": 508.0, "espesor_mm": 15.09, "costo_usd_m": 350},
    "24": {"OD_mm": 609.6, "espesor_mm": 17.48, "costo_usd_m": 440}
}

# Datos de aceros (Tabla 2)
aceros = {
    "X52": {"SMYS_psi": 52000, "F": 0.72},
    "X60": {"SMYS_psi": 60000, "F": 0.72}
}

# --------------------------------------------------
# Parámetros fijos
# --------------------------------------------------
L_total_km = 400
P_recepcion = 800
P_min_entrega = 500
T_succ_C = 20
T_succ_R = (T_succ_C + 273.15) * 9/5
gamma = 0.65
Z = 0.90
k = 1.3
eta_comp = 0.85
horas_anuales = 8000
vida_anios = 20
R_univ = 1545
MW_aire = 28.97
MW_gas = gamma * MW_aire
R_gas = R_univ / MW_gas

# --------------------------------------------------
# Funciones (igual que antes, pero sin cambios aquí)
# --------------------------------------------------
def diametro_interno(od_mm, esp_mm):
    return (od_mm - 2*esp_mm) / 25.4

def caida_presion_weymouth(P1, Q, L_mi, D_in, gamma, T_R, Z):
    const = 433.5
    term = const * (Q**2) * (L_mi * gamma * T_R * Z) / (D_in**5.33)
    P2_cuad = P1**2 - term
    if P2_cuad <= 0.1:
        return 0.1
    return np.sqrt(P2_cuad)

def potencia_compresor(Q, P_suc, P_desc, T_suc_R, Z, R_gas, k, eta):
    if P_suc <= 0:
        return 0
    Q_scf_s = Q * 1e6 / (24 * 3600)
    P_std_lbf_ft2 = 14.7 * 144
    T_std_R = 520
    Z_std = 1.0
    rho_std = (P_std_lbf_ft2 * MW_gas) / (Z_std * R_univ * T_std_R)
    m_dot = Q_scf_s * rho_std
    n = (k-1)/k
    head = (Z * R_gas * T_suc_R) * (1/n) * ((P_desc/P_suc)**n - 1)
    HP = (m_dot * head) / (550 * eta)
    return HP

def temp_descarga(T_suc_R, P_suc, P_desc, k):
    return T_suc_R * (P_desc / P_suc)**((k-1)/k)

def maop_barlow(OD_in, espesor_in, SMYS, F):
    return 2 * SMYS * F * espesor_in / OD_in

def costo_tuberia(dn, factor):
    return tuberias[dn]["costo_usd_m"] * (L_total_km * 1000) * factor

def factor_recuperacion(tasa, n):
    if tasa == 0:
        return 1/n
    return tasa * (1+tasa)**n / ((1+tasa)**n - 1)

# --------------------------------------------------
# Sidebar (más organizada)
# --------------------------------------------------
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/000000/pipeline.png", width=80)
    st.markdown("## ⚙️ Configuración")
    
    st.markdown("### 💰 Económicos")
    costo_energia = st.number_input("Costo energía (USD/kWh)", value=0.05, step=0.01)
    factor_acero = st.number_input("Factor costo acero", value=1.0, step=0.05)
    tasa_interes = st.number_input("Tasa interés (%)", value=8.0) / 100.0
    costo_comp_por_HP = st.number_input("Costo compresor (USD/HP)", value=1200, step=100)
    
    st.markdown("### 🔩 Materiales")
    dn_sel = st.selectbox("Diámetro nominal (pulg)", options=list(tuberias.keys()))
    grado_sel = st.selectbox("Grado del acero", options=list(aceros.keys()))
    
    st.markdown("### 📈 Operación")
    Q = st.number_input("Flujo (MMscfd)", value=500, step=50)
    N = st.slider("Número de estaciones de compresión", 0, 6, 2, 1)

# --------------------------------------------------
# Cálculos de materiales
# --------------------------------------------------
od_mm = tuberias[dn_sel]["OD_mm"]
esp_mm = tuberias[dn_sel]["espesor_mm"]
od_in = od_mm / 25.4
esp_in = esp_mm / 25.4
d_int_in = diametro_interno(od_mm, esp_mm)
SMYS = aceros[grado_sel]["SMYS_psi"]
F = aceros[grado_sel]["F"]
maop = maop_barlow(od_in, esp_in, SMYS, F)

L_mi = L_total_km * 0.621371
L_seg_mi = L_mi / (N + 1)

# --------------------------------------------------
# Simulación
# --------------------------------------------------
distancias_km = [0]
presiones = [P_recepcion]
P_actual = P_recepcion
HP_total = 0
T_max_C = 0

for i in range(N + 1):
    if i < N:
        P_fin_seg = caida_presion_weymouth(P_actual, Q, L_seg_mi, d_int_in, gamma, T_succ_R, Z)
        dist_km = (i+1) * (L_total_km/(N+1))
        distancias_km.append(dist_km)
        presiones.append(P_fin_seg)
        if P_fin_seg < 1.0:
            st.error(f"⚠️ Presión demasiado baja ({P_fin_seg:.2f} psia) - Diseño inviable")
            st.stop()
        HP = potencia_compresor(Q, P_fin_seg, P_recepcion, T_succ_R, Z, R_gas, k, eta_comp)
        HP_total += HP
        T2_R = temp_descarga(T_succ_R, P_fin_seg, P_recepcion, k)
        T2_C = (T2_R - 491.67) * 5/9
        if T2_C > T_max_C:
            T_max_C = T2_C
        P_actual = P_recepcion
    else:
        P_final = caida_presion_weymouth(P_actual, Q, L_seg_mi, d_int_in, gamma, T_succ_R, Z)
        dist_km = (i+1) * (L_total_km/(N+1))
        distancias_km.append(dist_km)
        presiones.append(P_final)

# --------------------------------------------------
# Costos
# --------------------------------------------------
costo_ducto = costo_tuberia(dn_sel, factor_acero)
costo_compresores = HP_total * costo_comp_por_HP
CAPEX = costo_ducto + costo_compresores
CRF = factor_recuperacion(tasa_interes, vida_anios)
OPEX = HP_total * 0.7457 * horas_anuales * costo_energia
TAC = CAPEX * CRF + OPEX

# --------------------------------------------------
# Métricas principales (con colores)
# --------------------------------------------------
st.markdown("## 📊 Resultados clave")
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.metric("💰 TAC (USD/año)", f"${TAC:,.0f}", delta=None, delta_color="normal")
    st.markdown('</div>', unsafe_allow_html=True)
with col2:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.metric("⚙️ Potencia total", f"{HP_total:,.0f} HP", delta=None)
    st.markdown('</div>', unsafe_allow_html=True)
with col3:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.metric("📉 Presión final", f"{presiones[-1]:.1f} psia", delta=None)
    st.markdown('</div>', unsafe_allow_html=True)

# --------------------------------------------------
# Pestañas para organizar el contenido
# --------------------------------------------------
tab1, tab2, tab3 = st.tabs(["📈 Perfil hidráulico", "💰 Desglose de costos", "⚠️ Alertas y detalles"])

with tab1:
    st.subheader("Presión vs. distancia")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=distancias_km, y=presiones, mode='lines+markers', name='Presión',
                             line=dict(color='#1e466e', width=3), marker=dict(size=6, color='#2c3e50')))
    fig.add_hline(y=P_min_entrega, line_dash="dash", line_color="red", annotation_text="P mínima entrega")
    fig.add_hline(y=maop, line_dash="dash", line_color="orange", annotation_text="MAOP")
    fig.update_layout(
        xaxis_title="Distancia (km)",
        yaxis_title="Presión (psia)",
        template="plotly_white",
        hovermode="x unified"
    )
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("Composición del costo anualizado")
    costos_df = pd.DataFrame({
        "Concepto": ["CAPEX Tubería", "CAPEX Compresores", "OPEX Energía"],
        "Monto (USD/año)": [costo_ducto*CRF, costo_compresores*CRF, OPEX]
    })
    fig2 = px.bar(costos_df, x="Concepto", y="Monto (USD/año)", text="Monto (USD/año)",
                  color="Concepto", color_discrete_sequence=["#1e466e", "#2c3e50", "#e67e22"],
                  title="Costo Total Anualizado por componente")
    fig2.update_traces(texttemplate='$%{text:,.0f}', textposition='outside')
    fig2.update_layout(showlegend=False, template="plotly_white")
    st.plotly_chart(fig2, use_container_width=True)

with tab3:
    st.subheader("Validaciones de diseño")
    col_al1, col_al2 = st.columns(2)
    with col_al1:
        if P_recepcion > maop:
            st.error("❌ MAOP superado")
        else:
            st.success("✅ MAOP dentro del límite")
        if T_max_C > 65:
            st.error("❌ Temperatura máxima > 65°C")
        else:
            st.success("✅ Temperatura OK")
    with col_al2:
        if presiones[-1] < P_min_entrega:
            st.error("❌ Presión final insuficiente")
        else:
            st.success("✅ Presión de entrega OK")
    
    with st.expander("🔍 Parámetros técnicos del diseño"):
        st.write(f"**Diámetro interno:** {d_int_in:.2f} in")
        st.write(f"**Espesor de pared:** {esp_in:.3f} in")
        st.write(f"**MAOP (Barlow):** {maop:.1f} psia")
        st.write(f"**Potencia total:** {HP_total:.0f} HP → {HP_total*0.7457:.0f} kW")
        st.write(f"**CRF (tasa {tasa_interes*100:.1f}%):** {CRF:.4f}")

# Pie de página
st.markdown("---")
st.markdown("🔧 **Proyecto Optimización de Procesos** | Simulación de Gasoducto Trans-Andino")
