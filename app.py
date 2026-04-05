import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from math import sqrt, pow

# ------------------ CONFIGURACIÓN DE LA PÁGINA ------------------
st.set_page_config(page_title="Gasoducto Trans-Andino", layout="wide")

# ESTILOS CSS AVANZADOS: FONDO NEGRO TOTAL Y SOBREESCRITURA DE SIDEBAR
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;800&display=swap');

    /* 1. FONDO NEGRO TOTAL (App y Sidebar) */
    .stApp, [data-testid="stSidebar"], section[data-testid="stSidebar"] > div {
        background-color: #000000 !important;
    }

    /* 2. TEXTOS GLOBALES EN BLANCO */
    html, body, [class*="st-"], div, label, p {
        color: #FFFFFF !important;
        font-family: 'Poppins', sans-serif !important;
    }

    /* 3. TÍTULO MONUMENTAL (vw para escala dinámica) */
    .titulo-principal {
        font-size: 8vw; 
        font-weight: 800;
        text-align: center;
        color: #7FFFD4 !important;
        margin-top: -50px;
        margin-bottom: 0px;
        text-transform: uppercase;
        letter-spacing: -2px;
        line-height: 1;
    }
    
    .subtitulo-principal {
        font-size: 1.2rem;
        font-weight: 300;
        color: #888888 !important;
        text-align: center;
        margin-bottom: 40px;
        letter-spacing: 5px;
        text-transform: uppercase;
    }

    /* 4. SIDEBAR: INPUTS NEGROS CON LETRA BLANCA */
    /* Cuadros de número y selección */
    [data-testid="stSidebar"] input, [data-testid="stSidebar"] select, [data-testid="stSidebar"] div[role="listbox"] {
        background-color: #000000 !important;
        color: #FFFFFF !important;
        border: 1px solid #333333 !important;
    }
    
    /* Etiquetas de los inputs en la sidebar */
    [data-testid="stSidebar"] label p {
        color: #7FFFD4 !important; /* Color aguamarina para los nombres de parámetros */
        font-weight: 600 !important;
    }

    /* 5. TARJETAS DE MÉTRICAS */
    .metric-card {
        background-color: #0A0A0A;
        border: 1px solid #1A1A1A;
        border-radius: 15px;
        padding: 25px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(127, 255, 212, 0.05);
    }
    .metric-label {
        font-size: 14px;
        color: #888888 !important;
        text-transform: uppercase;
        margin-bottom: 10px;
    }
    .metric-value {
        font-size: 38px;
        font-weight: 700;
        color: #7FFFD4 !important;
    }

    /* Títulos de sección con borde */
    .seccion-titulo {
        font-size: 24px;
        font-weight: 600;
        margin-top: 30px;
        border-left: 5px solid #7FFFD4;
        padding-left: 15px;
    }
    </style>
""", unsafe_allow_html=True)

# Títulos de la Interfaz
st.markdown('<h1 class="titulo-principal">GASODUCTO <br> TRANS-ANDINO</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitulo-principal">Gemelo Digital | Optimización & Simulación</p>', unsafe_allow_html=True)

# ------------------ DATOS Y CONSTANTES ------------------
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

# ------------------ SIDEBAR (CONFIGURACIÓN) ------------------
st.sidebar.markdown('<p style="font-size:22px; font-weight:800; color:#7FFFD4; text-align:center;">CONFIGURACIÓN</p>', unsafe_allow_html=True)

with st.sidebar.expander("💰 PARÁMETROS ECONÓMICOS", expanded=True):
    costo_energia = st.number_input("Costo energético (USD/kWh)", min_value=0.001, value=0.080, step=0.005, format="%.3f")
    tasa_interes = st.number_input("Tasa de interés (% anual)", min_value=0.0, max_value=50.0, value=10.0, step=0.5)
    factor_acero = st.number_input("Factor de acero (Adimensional)", min_value=0.1, value=0.70, step=0.05)

with st.sidebar.expander("📏 TUBERÍA Y MATERIAL", expanded=True):
    diametro_sel = st.selectbox("Diámetro nominal (pulg)", list(pipe_data_base.keys()), index=3)
    grado_sel = st.selectbox("Grado de acero", list(steel_data.keys()), index=1)

with st.sidebar.expander("🔧 OPERACIONES", expanded=True):
    Q_mmscfd = st.number_input("Flujo de gas (MMscfd)", min_value=10, value=500, step=10)
    # Rango coherente para 400km: 1 a 5 estaciones
    N_estaciones = st.slider("Número de estaciones (N)", min_value=1, max_value=5, value=1)

# ------------------ LÓGICA DE CÁLCULO ------------------
def calcular_simulacion():
    # Propiedades
    L_total_km = 400.0
    T1_K = 293.15 
    gamma = 0.65
    Z = 0.90
    k_gas = 1.28
    eficiencia = 0.85
    
    # Dimensiones
    D_ext_p = pipe_data_base[diametro_sel]["D_ext_mm"] / 25.4
    t_p = pipe_data_base[diametro_sel]["t_mm"] / 25.4
    D_int_p = D_ext_p - 2 * t_p
    
    # MAOP
    MAOP = (2 * steel_data[grado_sel]["SMYS_psi"] * t_p * steel_data[grado_sel]["F"]) / D_ext_p
    
    # Hidráulica (Weymouth por tramo)
    L_tramo_millas = (L_total_km * 0.621371) / N_estaciones
    T_R = T1_K * 1.8
    K_W = 433.5 * pow(Q_mmscfd, 2) * L_tramo_millas * gamma * T_R * Z / pow(D_int_p, 5.33)
    
    P_entrega_req = 500.0
    P_descarga = sqrt(pow(P_entrega_req, 2) + K_W)
    
    # Potencia y Temperatura
    P_suc_base = 800.0 if N_estaciones == 1 else 500.0 # Aproximación operativa
    r = P_descarga / P_suc_base
    potencia_est = (Q_mmscfd * 1e6 / (24*3600*eficiencia)) * (Z * 10.73 * T1_K / (k_gas - 1)) * (pow(r, (k_gas-1)/k_gas) - 1)
    HP_total = potencia_est * N_estaciones
    T2_C = (T1_K * pow(r, (k_gas-1)/k_gas)) - 273.15
    
    # Costos
    costo_base_m = pipe_data_base[diametro_sel]["costo_m"] * factor_acero
    capex_ducto = L_total_km * 1000 * costo_base_m
    capex_comp = HP_total * 1500.0 
    CAPEX_total = capex_ducto + capex_comp
    
    i = tasa_interes / 100
    CRF = (i * pow(1+i, 20)) / (pow(1+i, 20) - 1) if i > 0 else 1/20
    opex_e = HP_total * 0.7457 * 8760 * costo_energia
    opex_m = CAPEX_total * 0.02
    TAC = (CAPEX_total * CRF) + opex_e + opex_m
    
    return {
        "TAC": TAC, "HP": HP_total, "P_desc": P_descarga, "MAOP": MAOP, 
        "T2": T2_C, "D_int": D_int_p, "CAPEX": CAPEX_total, "OPEX": opex_e + opex_m
    }

res = calcular_simulacion()

# ------------------ PANEL PRINCIPAL ------------------
st.markdown('<div class="seccion-titulo">📊 RESULTADOS CLAVE</div>', unsafe_allow_html=True)
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(f'<div class="metric-card"><div class="metric-label">💰 TAC (USD/AÑO)</div><div class="metric-value">${res["TAC"]:,.0f}</div></div>', unsafe_allow_html=True)
with col2:
    st.markdown(f'<div class="metric-card"><div class="metric-label">⚙️ POTENCIA TOTAL</div><div class="metric-value">{res["HP"]:,.0f} HP</div></div>', unsafe_allow_html=True)
with col3:
    st.markdown(f'<div class="metric-card"><div class="metric-label">📉 PRESIÓN FINAL</div><div class="metric-value">500.0 psia</div></div>', unsafe_allow_html=True)

# Gráfico
st.markdown('<div class="seccion-titulo">📈 PERFIL DE PRESIÓN</div>', unsafe_allow_html=True)
d_step = 400.0 / N_estaciones
x_vals, y_vals = [], []
for n in range(N_estaciones):
    x_vals.extend([n*d_step, (n+1)*d_step])
    y_vals.extend([res["P_desc"], 500.0])

fig = go.Figure()
fig.add_trace(go.Scatter(x=x_vals, y=y_vals, mode='lines+markers', line=dict(color='#7FFFD4', width=4)))
fig.update_layout(
    plot_bgcolor='black', paper_bgcolor='black', 
    xaxis=dict(title="Distancia (km)", gridcolor='#222'),
    yaxis=dict(title="Presión (psia)", gridcolor='#222'),
    margin=dict(l=10, r=10, t=10, b=10),
    height=400
)
st.plotly_chart(fig, use_container_width=True)

# Alertas
st.markdown('<div class="seccion-titulo">⚠️ VALIDACIÓN DE SEGURIDAD</div>', unsafe_allow_html=True)
if res["P_desc"] > res["MAOP"]:
    st.error(f"🚨 ALERTA MAOP: Presión descarga ({res['P_desc']:.1f} psi) supera límite ({res['MAOP']:.1f} psi)")
else:
    st.success(f"✅ MAOP Seguro: {res['P_desc']:.1f} < {res['MAOP']:.1f} psi")

if res["T2"] > 65.0:
    st.error(f"🔥 ALERTA TÉRMICA: {res['T2']:.1f}°C supera el límite de 65°C")
else:
    st.success(f"✅ Temperatura controlada: {res['T2']:.1f}°C")

with st.expander("🔍 VER DETALLES TÉCNICOS"):
    st.write(f"Diámetro Interno: {res['D_int']:.2f} pulg")
    st.write(f"CAPEX Estimado: ${res['CAPEX']:,.0f}")
    st.write(f"OPEX Estimado: ${res['OPEX']:,.0f}")
