import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from math import sqrt, pow

# ------------------ CONFIGURACIÓN DE LA PÁGINA ------------------
st.set_page_config(page_title="Gasoducto Trans-Andino", layout="wide")

# Estilos CSS personalizados para homogeneidad
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

    /* Título principal: MÁS GRANDE, CENTRADO Y ACUAMARINE */
    .titulo-principal {
        font-family: 'Arial Black', sans-serif;
        font-size: 8vw;           /* Tamaño imponente relativo al ancho */
        font-weight: 900;
        color: #7FFFD4;           /* Acuamarine */
        text-align: center;       /* Centrado */
        margin-top: -40px;
        margin-bottom: 0px;
        letter-spacing: -2px;
        text-transform: uppercase;
        line-height: 1.1;
        text-shadow: 3px 3px 10px rgba(127, 255, 212, 0.2);
    }
    
    /* Subtítulo: centrado */
    .subtitulo-principal {
        font-family: 'Poppins', 'Segoe UI', sans-serif;
        font-size: 22px;
        font-weight: 300;
        color: #FFFFFF;
        text-align: center;
        margin-top: 0px;
        margin-bottom: 40px;
        letter-spacing: 2px;
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
        transition: transform 0.2s;
    }
    .metric-card:hover {
        transform: translateY(-5px);
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
        font-weight: 600;
        font-size: 18px;
        color: #7FFFD4;
    }
    </style>
""", unsafe_allow_html=True)

# Títulos con emojis de tubería y gas
st.markdown('<p class="titulo-principal">🛢️ GASODUCTO <br> TRANS-ANDINO ⛽</p>', unsafe_allow_html=True)
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
    
    if K_seg < 0:
        return None
    P_desc_psi = sqrt(500**2 + K_seg)
    supera_maop = P_desc_psi > MAOP_psi
    
    distancias_km = []
    presiones_psi = []
    dist_actual = 0.0
    for i in range(N):
        distancias_km.append(dist_actual)
        presiones_psi.append(P_desc_psi)
        dist_seg_km = L_km / N
        distancias_km.append(dist_actual + dist_seg_km)
        presiones_psi.append(500.0)
        dist_actual += dist_seg_km
    
    HP_total = 0.0
    T2_max_C = 0.0
    factor = 0.0857
    P_suc = 800.0
    r = P_desc_psi / P_suc
    HP_est = factor * Q * P_suc * (pow(r, (k-1)/k) - 1) / eta
    HP_total += HP_est
    T2_K = T1_K * pow(r, (k-1)/k)
    T2_C = T2_K - 273.15
    T2_max_C = T2_C
    
    for _ in range(1, N):
        P_suc = 500.0
        r = P_desc_psi / P_suc
        HP_est = factor * Q * P_suc * (pow(r, (k-1)/k) - 1) / eta
        HP_total += HP_est
        T2_K = T1_K * pow(r, (k-1)/k)
        T2_C = T2_K - 273.15
        if T2_C > T2_max_C:
            T2_max_C = T2_C
    
    alerta_termica = T2_max_C > 65.0
    presion_final_psi = presiones_psi[-1]
    alerta_entrega = presion_final_psi < 500.0
    
    longitud_m = L_km * 1000
    capex_pipe = longitud_m * costo_pipe_m
    capex_comp = HP_total * 1500.0
    
    i = params_economicos["tasa_interes"] / 100.0
    n = 20
    if i > 0:
        CRF = i * (1+i)**n / ((1+i)**n - 1)
    else:
        CRF = 1/n
    
    energia_anual_kWh = HP_total * 0.7457 * horas_anio
    opex_energia = energia_anual_kWh * params_economicos["costo_energia"]
    opex_mant = 0.05 * capex_comp
    OPEX_total = opex_energia + opex_mant
    CAPEX_total = capex_pipe + capex_comp
    TAC = CAPEX_total * CRF + OPEX_total
    
    cost_breakdown = {
        "CAPEX Ducto": capex_pipe,
        "CAPEX Compresores": capex_comp,
        "OPEX Energía": opex_energia,
        "OPEX Mantenimiento": opex_mant,
    }
    
    return {
        "TAC": TAC,
        "HP_total": HP_total,
        "presion_final": presion_final_psi,
        "P_descarga": P_desc_psi,
        "MAOP": MAOP_psi,
        "supera_MAOP": supera_maop,
        "alerta_termica": alerta_termica,
        "alerta_entrega": alerta_entrega,
        "T2_max_C": T2_max_C,
        "distancias_km": distancias_km,
        "presiones_psi": presiones_psi,
        "cost_breakdown": cost_breakdown,
        "capex_total": CAPEX_total,
        "opex_total": OPEX_total,
    }

# ------------------ BARRA LATERAL (SIN CAMBIOS) ------------------
st.sidebar.markdown('<p style="font-size:24px; font-weight:700; color:#7FFFD4; margin-bottom:15px;">⚙️ CONFIGURACIÓN</p>', unsafe_allow_html=True)
pipe_data = pipe_data_base.copy()

with st.sidebar.expander("💰 PARÁMETROS ECONÓMICOS", expanded=True):
    st.markdown('<div class="descripcion">💡 Mayor costo energía → mayor OPEX.</div>', unsafe_allow_html=True)
    costo_energia = st.number_input("USD/kWh", min_value=0.01, max_value=1.0, value=0.05, step=0.01, format="%.3f", key="energia")
    tasa_interes = st.number_input("% anual", min_value=0.0, max_value=30.0, value=8.0, step=0.5, key="interes")
    factor_steel = st.number_input("Factor acero", min_value=0.5, max_value=2.0, value=1.0, step=0.05, key="acero")

with st.sidebar.expander("📏 TUBERÍA Y MATERIAL", expanded=True):
    diametro = st.selectbox("Diámetro nominal", list(pipe_data.keys()), key="diam")
    grado_acero = st.selectbox("Grado del acero", list(steel_data.keys()), key="grado")

with st.sidebar.expander("🔧 OPERACIÓN", expanded=True):
    Q_diseno = st.number_input("Flujo (MMscfd)", min_value=100, max_value=1500, value=500, step=10, key="flujo")
    N_estaciones = st.slider("N° estaciones", min_value=1, max_value=10, value=2, step=1, key="estaciones")

for diam in pipe_data:
    pipe_data[diam]["costo_m"] = pipe_data_base[diam]["costo_m"] * factor_steel

# ------------------ PANEL PRINCIPAL (SIN CAMBIOS) ------------------
st.markdown('<div class="seccion-titulo">📊 RESULTADOS</div>', unsafe_allow_html=True)
resultados = calcular_perfil(N_estaciones, Q_diseno, diametro, grado_acero, {"costo_energia": costo_energia, "tasa_interes": tasa_interes}, pipe_data)

if resultados:
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f'<div class="metric-card"><div class="metric-label">💰 TAC (USD/año)</div><div class="metric-value">${resultados["TAC"]:,.0f}</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-card"><div class="metric-label">⚙️ Potencia total</div><div class="metric-value">{resultados["HP_total"]:,.0f} <span class="metric-unit">HP</span></div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="metric-card"><div class="metric-label">📉 Presión final</div><div class="metric-value">{resultados["presion_final"]:.1f} <span class="metric-unit">psia</span></div></div>', unsafe_allow_html=True)
    
    st.markdown('<div class="seccion-titulo">📈 PERFIL HIDRÁULICO</div>', unsafe_allow_html=True)
    fig1 = go.Figure(go.Scatter(x=resultados['distancias_km'], y=resultados['presiones_psi'], mode='lines+markers', line=dict(color='#7FFFD4', width=4), marker=dict(size=8, color='#FFD700')))
    fig1.update_layout(plot_bgcolor='#1E1E1E', paper_bgcolor='#000000', font=dict(color='white'), hovermode='x')
    st.plotly_chart(fig1, use_container_width=True)
else:
    st.error("No se pudo calcular con los parámetros actuales.")
