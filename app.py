import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from math import sqrt, pow

# ------------------ CONFIGURACIÓN DE LA PÁGINA ------------------
st.set_page_config(page_title="Gasoducto Trans-Andino", layout="wide")

# Estilos CSS personalizados
st.markdown("""
    <style>
    /* Fuente global profesional */
    html, body, .stApp, .stMarkdown, .stText, .stNumberInput, .stSelectbox, .stSlider {
        font-family: 'Poppins', 'Segoe UI', 'Roboto', sans-serif;
    }
    
    /* Fondo negro */
    .stApp {
        background-color: #000000;
    }

    /* TÍTULO PRINCIPAL: MÁS GRANDE, CENTRADO Y AZUL ACUAMARINE */
    .titulo-principal {
        font-family: 'Arial Black', sans-serif;
        font-size: 10vw;           /* Tamaño monumental */
        font-weight: 900;
        color: #7FFFD4;           /* Azul Acuamarine */
        text-align: center;       /* Centrado */
        margin-top: -30px;
        margin-bottom: 0px;
        letter-spacing: -2px;
        text-transform: uppercase;
        line-height: 1;
        display: block;
        width: 100%;
    }
    
    /* Subtítulo: centrado y elegante */
    .subtitulo-principal {
        font-family: 'Poppins', 'Segoe UI', sans-serif;
        font-size: 24px;
        font-weight: 300;
        color: #FFFFFF;
        text-align: center;       /* Centrado */
        margin-top: 10px;
        margin-bottom: 40px;
        letter-spacing: 2px;
        text-transform: uppercase;
    }
    
    /* Encabezados de sección */
    .seccion-titulo {
        font-family: 'Poppins', 'Segoe UI', sans-serif;
        font-size: 28px;
        font-weight: 600;
        color: #FFFFFF;
        margin-top: 30px;
        margin-bottom: 20px;
        border-left: 5px solid #7FFFD4;
        padding-left: 15px;
    }
    
    /* Tarjetas de métricas */
    .metric-card {
        background-color: #111111;  
        border-radius: 20px;
        padding: 25px 15px;
        text-align: center;
        box-shadow: 0 10px 20px rgba(0,0,0,0.4);
        border: 1px solid #2c5a9e;
    }
    .metric-label {
        font-size: 18px;
        font-weight: 500;
        color: #DDDDDD;
        margin-bottom: 12px;
    }
    .metric-value {
        font-size: 36px;
        font-weight: 700;
        color: #7FFFD4;
        margin: 0;
    }
    .metric-unit {
        font-size: 18px;
        font-weight: 400;
        color: #FFFFFF;
    }
    
    /* Descripciones en sidebar */
    .descripcion {
        font-size: 13px;
        color: #FFFACD;
        margin-bottom: 8px;
        font-style: italic;
        background-color: #2E2E2E;
        padding: 5px 8px;
        border-radius: 8px;
    }
    
    .streamlit-expanderHeader {
        color: #7FFFD4;
        font-weight: 600;
    }
    </style>
""", unsafe_allow_html=True)

# Renderizado de Títulos
st.markdown('<h1 class="titulo-principal">GASODUCTO<br>TRANS-ANDINO</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitulo-principal">Gemelo digital | Simulación hidráulica & económica</p>', unsafe_allow_html=True)

# ------------------ FUNCIONES DE CÁLCULO (SIN CAMBIOS) ------------------
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

# ------------------ BARRA LATERAL ------------------
st.sidebar.markdown('<p style="font-size:24px; font-weight:700; color:#7FFFD4;">⚙️ CONFIGURACIÓN</p>', unsafe_allow_html=True)
pipe_data = pipe_data_base.copy()
with st.sidebar.expander("💰 PARÁMETROS ECONÓMICOS", expanded=True):
    costo_energia = st.number_input("USD/kWh", min_value=0.01, value=0.05, step=0.01)
    tasa_interes = st.number_input("% anual", min_value=0.0, value=8.0, step=0.5)
    factor_steel = st.number_input("Factor acero", min_value=0.5, value=1.0, step=0.05)
with st.sidebar.expander("📏 TUBERÍA Y MATERIAL", expanded=True):
    diametro = st.selectbox("Diámetro nominal", list(pipe_data.keys()))
    grado_acero = st.selectbox("Grado del acero", list(steel_data.keys()))
with st.sidebar.expander("🔧 OPERACIÓN", expanded=True):
    Q_diseno = st.number_input("Flujo (MMscfd)", min_value=100, value=500, step=10)
    N_estaciones = st.slider("N° estaciones", min_value=1, max_value=10, value=2)

for d in pipe_data: pipe_data[d]["costo_m"] = pipe_data_base[d]["costo_m"] * factor_steel

# ------------------ PANEL PRINCIPAL ------------------
st.markdown('<div class="seccion-titulo">📊 RESULTADOS</div>', unsafe_allow_html=True)
resultados = calcular_perfil(N_estaciones, Q_diseno, diametro, grado_acero, {"costo_energia": costo_energia, "tasa_interes": tasa_interes}, pipe_data)

if resultados:
    col1, col2, col3 = st.columns(3)
    col1.markdown(f'<div class="metric-card"><div class="metric-label">💰 TAC (USD/año)</div><div class="metric-value">${resultados["TAC"]:,.0f}</div></div>', unsafe_allow_html=True)
    col2.markdown(f'<div class="metric-card"><div class="metric-label">⚙️ Potencia total</div><div class="metric-value">{resultados["HP_total"]:,.0f} HP</div></div>', unsafe_allow_html=True)
    col3.markdown(f'<div class="metric-card"><div class="metric-label">📉 Presión final</div><div class="metric-value">{resultados["presion_final"]:.1f} psia</div></div>', unsafe_allow_html=True)
    
    st.markdown('<div class="seccion-titulo">📈 PERFIL HIDRÁULICO</div>', unsafe_allow_html=True)
    fig1 = go.Figure(go.Scatter(x=resultados['distancias_km'], y=resultados['presiones_psi'], mode='lines+markers', line=dict(color='#7FFFD4', width=4)))
    fig1.update_layout(plot_bgcolor='#1E1E1E', paper_bgcolor='#000000', font=dict(color='white'))
    st.plotly_chart(fig1, use_container_width=True)
