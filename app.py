# app.py
# Gasoducto Trans-Andino - Versión final con constante 433.5 y rayo en título
# Optimización de Procesos

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# ------------------------------------------------------------
# Configuración de la página
# ------------------------------------------------------------
st.set_page_config(
    page_title="Gasoducto Trans-Andino",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------------------------------------------------
# Estilo: fondo negro, texto blanco, ayudas en azul claro
# ------------------------------------------------------------
st.markdown("""
<style>
    .stApp { background-color: #0a0c10; }
    .main > div { flex-direction: row-reverse; }
    section[data-testid="stSidebar"] {
        order: 2;
        background-color: #14161c;
        border-left: 1px solid #2c3e50;
    }
    .stMarkdown, .stText, .stNumberInput label, .stSelectbox label, 
    .stSlider label, .stMetric label, .stMetric value {
        color: #ffffff !important;
    }
    .main-title {
        font-family: 'Arial Black', 'Impact', sans-serif;
        font-size: 3rem;
        text-align: center;
        color: #00aaff;
        text-transform: uppercase;
        letter-spacing: 2px;
        margin-bottom: 0rem;
    }
    .subtitle {
        text-align: center;
        color: #cccccc;
        font-size: 1rem;
        margin-top: 0rem;
    }
    .metric-card {
        background-color: #1e1e2a;
        padding: 1rem;
        border-radius: 12px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.5);
        text-align: center;
        border-top: 4px solid #00aaff;
    }
    .metric-card label, .metric-card div { color: #ffffff !important; }
    h1, h2, h3 { color: #00aaff !important; font-weight: 500; }
    hr { border-color: #2c3e50; }
    .streamlit-expanderHeader { color: #00aaff !important; }
    .help-text {
        font-size: 0.8rem;
        color: #bbddff !important;
        margin-top: -10px;
        margin-bottom: 15px;
        font-style: italic;
    }
    .recommendation-box {
        background-color: #1e2a2a;
        border-left: 4px solid #ffaa00;
        padding: 0.8rem;
        border-radius: 8px;
        margin: 1rem 0;
        color: #ffffff;
    }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------
# Título con rayo (⚡)
# ------------------------------------------------------------
st.markdown('<div class="main-title">⚡ GASODUCTO TRANS-ANDINO ⚡</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Simulación hidráulica y económica | Optimización de Procesos</div>', unsafe_allow_html=True)
st.markdown("---")

# ------------------------------------------------------------
# 1. Base de datos técnica (Tablas del enunciado)
# ------------------------------------------------------------
TUBERIAS = {
    "12 pulgadas": {"D_ext_mm": 323.8, "t_mm": 10.31, "costo_base": 185},
    "16 pulgadas": {"D_ext_mm": 406.4, "t_mm": 12.70, "costo_base": 260},
    "20 pulgadas": {"D_ext_mm": 508.0, "t_mm": 15.09, "costo_base": 350},
    "24 pulgadas": {"D_ext_mm": 609.6, "t_mm": 17.48, "costo_base": 440}
}

ACEROS = {
    "X52": {"SMYS_psi": 52000, "F": 0.72},
    "X60": {"SMYS_psi": 60000, "F": 0.72}
}

# ------------------------------------------------------------
# 2. Parámetros fijos (según enunciado)
# ------------------------------------------------------------
P_RECEPCION = 800.0
P_MIN_ENTREGA = 500.0
L_TOTAL_KM = 400.0
T_SUC_C = 20
T_SUC_K = 273.15 + T_SUC_C
T_SUC_R = T_SUC_K * 9/5
GAMMA = 0.65
Z = 0.90
K = 1.30
ETA_COMP = 0.85
HORAS_ANUALES = 8000
VIDA_PROYECTO = 20
R_UNIV = 1545.4
P_BASE = 14.7
T_BASE_R = 520
MW_AIRE = 28.97
MW_GAS = GAMMA * MW_AIRE

CONST_WEYMOUTH = 433.5
E_HID = 1.0

# ------------------------------------------------------------
# 3. Funciones de cálculo
# ------------------------------------------------------------
def crf(tasa, n=VIDA_PROYECTO):
    if tasa == 0:
        return 1.0 / n
    return tasa * (1 + tasa)**n / ((1 + tasa)**n - 1)

def maop_barlow(SMYS_psi, t_mm, D_ext_mm, F):
    t_in = t_mm / 25.4
    D_in = D_ext_mm / 25.4
    return 2.0 * SMYS_psi * t_in * F / D_in

def caida_presion_weymouth(P1, Q, L_mi, D_in):
    term = CONST_WEYMOUTH * (Q / E_HID)**2 * (L_mi * GAMMA * T_SUC_R * Z) / (D_in**5.33)
    P2_cuad = P1**2 - term
    if P2_cuad <= 0.1:
        return 0.1
    return np.sqrt(P2_cuad)

def potencia_compresor(Q, P_suc, P_desc, T_suc_R, Z, k, MW, eta):
    r_p = P_desc / P_suc
    n = (k - 1) / k
    H_p = (Z * R_UNIV * T_suc_R / MW) * (1 / n) * (r_p**n - 1)
    Q_scf_s = Q * 1e6 / (24 * 3600)
    rho_std = (P_BASE * 144 * MW) / (R_UNIV * T_BASE_R)
    m_dot = Q_scf_s * rho_std
    BHP = (m_dot * H_p) / (550 * eta)
    return BHP

def temp_descarga(T_suc_R, P_suc, P_desc, k):
    return T_suc_R * (P_desc / P_suc)**((k-1)/k)

def costo_tuberia(dn_key, factor_acero):
    costo_m = TUBERIAS[dn_key]["costo_base"] * factor_acero
    return costo_m * (L_TOTAL_KM * 1000)

# ------------------------------------------------------------
# 4. Simulación del perfil de presión
# ------------------------------------------------------------
def simular_perfil(Q, D_in, N_est):
    L_seg_mi = (L_TOTAL_KM * 0.621371) / (N_est + 1)
    distancias = [0.0]
    presiones = [P_RECEPCION]
    P_actual = P_RECEPCION
    HP_total = 0.0
    T_max_C = 0.0
    factible = True

    for i in range(N_est + 1):
        if i < N_est:
            P_fin_seg = caida_presion_weymouth(P_actual, Q, L_seg_mi, D_in)
            dist_km = (i + 1) * (L_TOTAL_KM / (N_est + 1))
            distancias.append(dist_km)
            presiones.append(P_fin_seg)

            if P_fin_seg < 1.0:
                factible = False
                break

            HP = potencia_compresor(Q, P_fin_seg, P_RECEPCION, T_SUC_R, Z, K, MW_GAS, ETA_COMP)
            HP_total += HP

            T2_R = temp_descarga(T_SUC_R, P_fin_seg, P_RECEPCION, K)
            T2_C = (T2_R - 491.67) * 5/9
            if T2_C > T_max_C:
                T_max_C = T2_C

            P_actual = P_RECEPCION
        else:
            P_final = caida_presion_weymouth(P_actual, Q, L_seg_mi, D_in)
            dist_km = (i + 1) * (L_TOTAL_KM / (N_est + 1))
            distancias.append(dist_km)
            presiones.append(P_final)

    return distancias, presiones, HP_total, T_max_C, presiones[-1], factible

# ------------------------------------------------------------
# 5. Barra lateral (configuración) con mini descripciones
# ------------------------------------------------------------
with st.sidebar:
    st.markdown("## Configuración")
    st.markdown("---")

    st.markdown("### Económicos")
    costo_energia = st.number_input("Costo energía (USD/kWh)", min_value=0.01, max_value=0.50, value=0.05, step=0.01)
    st.markdown('<div class="help-text">Influye en el costo anual de operación (OPEX). A mayor costo, más caro operar.</div>', unsafe_allow_html=True)

    factor_acero = st.number_input("Factor costo acero (x)", min_value=0.5, max_value=2.0, value=1.0, step=0.05)
    st.markdown('<div class="help-text">Multiplicador del costo base de la tubería (1.0 = precio estándar).</div>', unsafe_allow_html=True)

    tasa_interes = st.number_input("Tasa interés (%)", min_value=1.0, max_value=20.0, value=8.0) / 100.0
    st.markdown('<div class="help-text">Usada para calcular el factor de recuperación de capital (CRF). A mayor tasa, mayor TAC.</div>', unsafe_allow_html=True)

    costo_comp_por_HP = st.number_input("Costo compresor (USD/HP)", min_value=800, max_value=2000, value=1200, step=100)
    st.markdown('<div class="help-text">Costo de inversión por cada HP de potencia instalada.</div>', unsafe_allow_html=True)

    st.markdown("### Materiales")
    diametro_sel = st.selectbox("Diámetro nominal", list(TUBERIAS.keys()))
    st.markdown('<div class="help-text">Diámetro exterior de la tubería. A mayor diámetro, menor caída de presión pero mayor costo.</div>', unsafe_allow_html=True)

    acero_sel = st.selectbox("Grado del acero", list(ACEROS.keys()))
    st.markdown('<div class="help-text">Resistencia del acero. Afecta la presión máxima admisible (MAOP).</div>', unsafe_allow_html=True)

    st.markdown("### Operación")
    Q_input = st.number_input("Flujo (MMscfd)", min_value=100.0, max_value=1500.0, value=500.0, step=50.0)
    st.markdown('<div class="help-text">Cantidad de gas transportado por día. A mayor flujo, mayor caída de presión y potencia.</div>', unsafe_allow_html=True)

    N_est = st.slider("Número de estaciones de compresión", min_value=0, max_value=6, value=2, step=1)
    st.markdown('<div class="help-text">Cantidad de compresores a lo largo del gasoducto. Más estaciones = mayor inversión pero menor potencia total y menor temperatura.</div>', unsafe_allow_html=True)

# ------------------------------------------------------------
# 6. Cálculos con parámetros seleccionados
# ------------------------------------------------------------
dat_tubo = TUBERIAS[diametro_sel]
dat_ac = ACEROS[acero_sel]
D_ext_mm = dat_tubo["D_ext_mm"]
t_mm = dat_tubo["t_mm"]
D_in = (D_ext_mm - 2*t_mm) / 25.4
SMYS = dat_ac["SMYS_psi"]
F = dat_ac["F"]
MAOP = maop_barlow(SMYS, t_mm, D_ext_mm, F)

distancias, presiones, HP_total, T_max_C, P_final, factible = simular_perfil(Q_input, D_in, N_est)

if not factible:
    st.error("Diseño inviable: la presión cae a valores extremadamente bajos. Aumente el diámetro o reduzca el flujo.")
    st.stop()

costo_ducto = costo_tuberia(diametro_sel, factor_acero)
costo_compresores = HP_total * costo_comp_por_HP
CAPEX = costo_ducto + costo_compresores
CRF_val = crf(tasa_interes)
OPEX = HP_total * 0.7457 * HORAS_ANUALES * costo_energia
TAC = CAPEX * CRF_val + OPEX

# ------------------------------------------------------------
# 7. Métricas principales
# ------------------------------------------------------------
st.markdown("## Resultados clave")
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.metric("TAC (USD/año)", f"${TAC:,.0f}")
    st.markdown('</div>', unsafe_allow_html=True)
with col2:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.metric("Potencia total instalada", f"{HP_total:,.0f} HP")
    st.markdown('</div>', unsafe_allow_html=True)
with col3:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.metric("Presión final de entrega", f"{P_final:.1f} psia")
    st.markdown('</div>', unsafe_allow_html=True)

# ------------------------------------------------------------
# 8. Perfil hidráulico
# ------------------------------------------------------------
st.markdown("## Perfil de presión")
fig_pres = go.Figure()
fig_pres.add_trace(go.Scatter(
    x=distancias, y=presiones,
    mode='lines+markers',
    name='Presión',
    line=dict(color='#00aaff', width=3),
    marker=dict(size=6, color='#ffffff')
))
fig_pres.add_hline(y=P_MIN_ENTREGA, line_dash="dash", line_color="#ff5555", annotation_text="Presión mínima de entrega (500 psia)")
fig_pres.add_hline(y=MAOP, line_dash="dash", line_color="#ffaa00", annotation_text=f"MAOP = {MAOP:.0f} psia")
fig_pres.update_layout(
    xaxis_title="Distancia (km)",
    yaxis_title="Presión (psia)",
    template="plotly_dark",
    height=450,
    margin=dict(l=0, r=0, t=30, b=0),
    font=dict(color="#ffffff")
)
st.plotly_chart(fig_pres, use_container_width=True)

# ------------------------------------------------------------
# 9. Desglose de costos
# ------------------------------------------------------------
st.markdown("## Desglose del costo anualizado")
costos_df = pd.DataFrame({
    "Concepto": ["CAPEX Tubería", "CAPEX Compresores", "OPEX Energía"],
    "Monto (USD/año)": [costo_ducto * CRF_val, costo_compresores * CRF_val, OPEX]
})
fig_cost = px.bar(
    costos_df, x="Concepto", y="Monto (USD/año)",
    text="Monto (USD/año)",
    color="Concepto",
    color_discrete_sequence=["#00aaff", "#ffaa00", "#44cc44"],
    title="Costo Total Anualizado (TAC)"
)
fig_cost.update_traces(texttemplate='$%{text:,.0f}', textposition='outside')
fig_cost.update_layout(
    template="plotly_dark",
    height=400,
    font=dict(color="#ffffff"),
    paper_bgcolor="#0a0c10",
    plot_bgcolor="#0a0c10"
)
st.plotly_chart(fig_cost, use_container_width=True)

# ------------------------------------------------------------
# 10. Validaciones y recomendaciones
# ------------------------------------------------------------
st.markdown("## Validaciones de diseño")
col_v1, col_v2 = st.columns(2)
with col_v1:
    if P_RECEPCION > MAOP:
        st.error("MAOP superado: la presión de descarga excede el límite de Barlow.")
    else:
        st.success(f"MAOP OK: {P_RECEPCION} psia ≤ {MAOP:.0f} psia")
    if T_max_C > 65:
        st.error(f"Temperatura máxima de descarga: {T_max_C:.1f} °C > 65 °C")
    else:
        st.success(f"Temperatura OK: máxima {T_max_C:.1f} °C ≤ 65 °C")
with col_v2:
    if P_final < P_MIN_ENTREGA:
        st.error(f"Presión final insuficiente: {P_final:.1f} psia < {P_MIN_ENTREGA} psia")
    else:
        st.success(f"Presión de entrega OK: {P_final:.1f} psia ≥ {P_MIN_ENTREGA} psia")

recomendaciones = []
if P_final < P_MIN_ENTREGA:
    recomendaciones.append("- Aumente el diámetro nominal (por ejemplo, de 20 a 24 pulgadas).")
    recomendaciones.append("- Incremente el número de estaciones de compresión (actualmente N = {})".format(N_est))
    recomendaciones.append("- Reduzca el flujo de gas si es posible (actualmente {:.0f} MMscfd).".format(Q_input))
if T_max_C > 65:
    recomendaciones.append("- Aumente el número de estaciones para reducir la relación de compresión por etapa.")
    recomendaciones.append("- Considere enfriadores intermedios si la temperatura sigue siendo alta.")
if P_RECEPCION > MAOP:
    recomendaciones.append("- Cambie a un grado de acero superior (X60 en lugar de X52) o aumente el espesor de pared.")

if recomendaciones:
    st.markdown('<div class="recommendation-box"><strong>Recomendaciones para cumplir las especificaciones:</strong><br>' + "<br>".join(recomendaciones) + '</div>', unsafe_allow_html=True)

# ------------------------------------------------------------
# 11. Detalles técnicos
# ------------------------------------------------------------
with st.expander("Detalles técnicos del diseño"):
    st.write(f"**Diámetro interno:** {D_in:.2f} in")
    st.write(f"**Espesor de pared:** {t_mm/25.4:.3f} in")
    st.write(f"**MAOP (Barlow):** {MAOP:.0f} psia")
    st.write(f"**Potencia total:** {HP_total:.0f} HP → {HP_total*0.7457:.0f} kW")
    st.write(f"**CRF (tasa {tasa_interes*100:.1f}%):** {CRF_val:.4f}")
    st.write(f"**Peso molecular del gas:** {MW_GAS:.2f} lb/lbmol")
    st.write(f"**Constante de Weymouth usada:** {CONST_WEYMOUTH} (según enunciado)")

st.markdown("---")
st.markdown("<p style='text-align: center; color: #888;'>Proyecto Optimización de Procesos | Simulación de Gasoducto Trans-Andino</p>", unsafe_allow_html=True)
