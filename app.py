import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from math import sqrt, pow

# ------------------ CONFIGURACIÓN DE LA PÁGINA ------------------
st.set_page_config(page_title="Gasoducto Trans-Andino", layout="wide")

# ESTILOS CSS PARA MANTENER TODO NEGRO Y VISIBLE
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;800&display=swap');

    /* Fondo negro total */
    .stApp, [data-testid="stSidebar"], section[data-testid="stSidebar"] > div {
        background-color: #000000 !important;
    }

    /* Texto global en blanco */
    html, body, [class*="st-"], div, label, p {
        color: #FFFFFF !important;
        font-family: 'Poppins', sans-serif !important;
    }

    /* Título Monumental */
    .titulo-principal {
        font-family: 'Arial Black', sans-serif;
        font-size: 8vw;
        font-weight: 800;
        color: #7FFFD4 !important;
        text-align: center;
        margin-top: -50px;
        margin-bottom: 0px;
        text-transform: uppercase;
        letter-spacing: 2px;
    }
    
    .subtitulo-principal {
        font-size: 20px;
        font-weight: 300;
        color: #FFFFFF !important;
        text-align: center;
        margin-top: -10px;
        margin-bottom: 40px;
    }

    /* Sidebar: Inputs negros con texto blanco */
    [data-testid="stSidebar"] input, [data-testid="stSidebar"] select, [data-testid="stSidebar"] div[role="listbox"] {
        background-color: #000000 !important;
        color: #FFFFFF !important;
        border: 1px solid #333333 !important;
    }

    /* Estilo de tarjetas de métricas */
    .metric-card {
        background-color: #111111;
        border-radius: 20px;
        padding: 25px 15px;
        text-align: center;
        border: 1px solid #2c5a9e;
    }
    .metric-label { font-size: 18px; color: #DDDDDD !important; }
    .metric-value { font-size: 36px; font-weight: 700; color: #7FFFD4 !important; }

    /* Encabezados de sección */
    .seccion-titulo {
        font-size: 28px;
        font-weight: 600;
        color: #FFFFFF;
        margin-top: 30px;
        border-left: 5px solid #7FFFD4;
        padding-left: 15px;
    }
    </style>
""", unsafe_allow_html=True)

# Títulos
st.markdown('<p class="titulo-principal">GASODUCTO TRANS-ANDINO</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitulo-principal">Gemelo digital | Simulación hidráulica & económica</p>', unsafe_allow_html=True)

# ------------------ FUNCIONES Y DATOS (TU LÓGICA ORIGINAL) ------------------
L_km = 400.0
L_miles = L_km * 0.621371
T1_K = 293.15
T1_R = T1_K * 9/5
gamma = 0.65
Z = 0.90
k = 1.28
eta = 0.85
horas_anio = 8760

pipe_data_base = {
    "12\"": {"D_ext_mm": 323.8, "t_mm": 10.31, "costo_m": 185},
    "16\"": {"D_ext_mm": 406.4, "t_mm": 12.70, "costo_m": 260},
    "20\"": {"D_ext_mm": 508.0, "t_mm": 15.09, "costo_m": 350},
    "24\"": {"D_ext_mm": 609.6, "t_mm": 17.48, "costo_m": 440},
}

steel_data = {
    "X52": {"SMYS_psi": 52000, "F": 0.72},
    "X60": {"SMYS_psi": 60000, "F": 0.72},
}

def calcular_MAOP(D_ext_in, t_in, SMYS_psi, F):
    return 2 * SMYS_psi * F * t_in / D_ext_in

def weymouth_k_loss(Q_MMscfd, L_seg_millas, D_in_pulg, gamma, T_R, Z):
    return 433.5 * (Q_MMscfd**2) * L_seg_millas * gamma * T_R * Z / (D_in_pulg**5.33)

def calcular_perfil(N, Q, diametro, grado_acero, params_economicos, pipe_data_actual):
    # (Se mantiene exactamente tu función de cálculo original)
    diam_nom = diametro
    D_ext_mm = pipe_data_actual[diam_nom]["D_ext_mm"]
    t_mm = pipe_data_actual[diam_nom]["t_mm"]
    D_int_mm = D_ext_mm - 2*t_mm
    D_int_pulg = D_int_mm / 25.4
    costo_pipe_m = pipe_data_actual[diam_nom]["costo_m"]
    SMYS_psi = steel_data[grado_acero]["SMYS_psi"]
    F = steel_data[grado_acero]["F"]
    D_ext_pulg = D_ext_mm / 25.4
    t_pulg = t_mm / 25.4
    MAOP_psi = calcular_MAOP(D_ext_pulg, t_pulg, SMYS_psi, F)
    L_seg_millas = L_miles / N
    K_seg = weymouth_k_loss(Q, L_seg_millas, D_int_pulg, gamma, T1_R, Z)
    if K_seg < 0: return None
    P_desc_psi = sqrt(500**2 + K_seg)
    supera_maop = P_desc_psi > MAOP_psi
    distancias_km, presiones_psi = [], []
    dist_actual = 0.0
    for i in range(N):
        distancias_km.extend([dist_actual, dist_actual + (L_km / N)])
        presiones_psi.extend([P_desc_psi, 500.0])
        dist_actual += (L_km / N)
    HP_total, T2_max_C, factor, P_suc = 0.0, 0.0, 0.0857, 800.0
    for i in range(N):
        if i > 0: P_suc = 500.0
        r = P_desc_psi / P_suc
        HP_est = factor * Q * P_suc * (pow(r, (k-1)/k) - 1) / eta
        HP_total += HP_est
        T2_C = (T1_K * pow(r, (k-1)/k)) - 273.15
        if T2_C > T2_max_C: T2_max_C = T2_C
    i_tasa = params_economicos["tasa_interes"] / 100.0
    CRF = i_tasa * (1+i_tasa)**20 / ((1+i_tasa)**20 - 1) if i_tasa > 0 else 1/20
    capex_pipe = (L_km * 1000) * costo_pipe_m
    capex_comp = HP_total * 1500.0
    opex_energia = (HP_total * 0.7457 * horas_anio) * params_economicos["costo_energia"]
    opex_mant = 0.05 * capex_comp
    TAC = (capex_pipe + capex_comp) * CRF + opex_energia + opex_mant
    return {
        "TAC": TAC, "HP_total": HP_total, "presion_final": presiones_psi[-1],
        "P_descarga": P_desc_psi, "MAOP": MAOP_psi, "supera_MAOP": supera_maop,
        "alerta_termica": T2_max_C > 65.0, "T2_max_C": T2_max_C,
        "distancias_km": distancias_km, "presiones_psi": presiones_psi,
        "cost_breakdown": {"CAPEX Ducto": capex_pipe, "CAPEX Compresores": capex_comp, "OPEX Energía": opex_energia, "OPEX Mant.": opex_mant},
        "capex_total": capex_pipe + capex_comp, "opex_total": opex_energia + opex_mant
    }

# ------------------ BARRA LATERAL (SIDEBAR) ------------------
st.sidebar.markdown('<p style="font-size:24px; font-weight:700; color:#7FFFD4;">⚙️ CONFIGURACIÓN</p>', unsafe_allow_html=True)

with st.sidebar.expander("💰 PARÁMETROS ECONÓMICOS", expanded=True):
    costo_energia = st.number_input("Costo energía (USD/kWh)", min_value=0.01, value=0.05, step=0.01)
    tasa_interes = st.number_input("Tasa interés (% anual)", min_value=0.0, value=8.0, step=0.5)
    factor_steel = st.number_input("Factor de acero", min_value=0.5, value=1.0, step=0.05)

with st.sidebar.expander("📏 TUBERÍA Y MATERIAL", expanded=True):
    diametro = st.selectbox("Diámetro nominal", list(pipe_data_base.keys()))
    grado_acero = st.selectbox("Grado del acero", list(steel_data.keys()))

with st.sidebar.expander("🔧 OPERACIÓN", expanded=True):
    Q_diseno = st.number_input("Flujo (MMscfd)", min_value=100, value=500, step=10)
    N_estaciones = st.slider("N° estaciones", min_value=1, max_value=6, value=2)

# Aplicar factor
pipe_data = pipe_data_base.copy()
for d in pipe_data: pipe_data[d]["costo_m"] *= factor_steel

# ------------------ PANEL PRINCIPAL ------------------
st.markdown('<div class="seccion-titulo">📊 RESULTADOS</div>', unsafe_allow_html=True)
res = calcular_perfil(N_estaciones, Q_diseno, diametro, grado_acero, {"costo_energia": costo_energia, "tasa_interes": tasa_interes}, pipe_data)

if res:
    c1, c2, c3 = st.columns(3)
    c1.markdown(f'<div class="metric-card"><div class="metric-label">💰 TAC (USD/año)</div><div class="metric-value">${res["TAC"]:,.0f}</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="metric-card"><div class="metric-label">⚙️ Potencia total</div><div class="metric-value">{res["HP_total"]:,.0f} HP</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="metric-card"><div class="metric-label">📉 Presión final</div><div class="metric-value">{res["presion_final"]:.1f} psia</div></div>', unsafe_allow_html=True)

    st.markdown('<div class="seccion-titulo">📈 PERFIL HIDRÁULICO</div>', unsafe_allow_html=True)
    fig1 = go.Figure(go.Scatter(x=res['distancias_km'], y=res['presiones_psi'], mode='lines+markers', line=dict(color='#7FFFD4', width=4)))
    fig1.update_layout(plot_bgcolor='#1E1E1E', paper_bgcolor='#000000', font=dict(color='white'))
    st.plotly_chart(fig1, use_container_width=True)

    st.markdown('<div class="seccion-titulo">⚠️ VALIDACIÓN DE SEGURIDAD</div>', unsafe_allow_html=True)
    if res['supera_MAOP']: st.error(f"🚨 MAOP Excedido: {res['P_descarga']:.1f} > {res['MAOP']:.1f} psia")
    else: st.success(f"✅ MAOP Seguro: {res['P_descarga']:.1f} psia")
    
    if res['alerta_termica']: st.error(f"🔥 Temperatura Alta: {res['T2_max_C']:.1f} °C")
    else: st.success(f"✅ Temperatura Segura: {res['T2_max_C']:.1f} °C")
