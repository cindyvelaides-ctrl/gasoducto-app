import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from math import sqrt, pow

# ------------------ CONFIGURACIÓN DE LA PÁGINA ------------------
st.set_page_config(page_title="Gasoducto Trans-Andino", layout="wide")

# Estilos CSS para un look "Engineering Dark Mode" profesional
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;800&display=swap');

    /* Fondo negro absoluto en toda la app y sidebar */
    .stApp, [data-testid="stSidebar"], .stSidebar {
        background-color: #000000 !important;
    }

    /* Fuente global blanca */
    html, body, [class*="st-"], div, label {
        font-family: 'Poppins', sans-serif !important;
        color: #FFFFFF !important;
    }

    /* TÍTULO PRINCIPAL MONUMENTAL Y CENTRADO */
    .titulo-principal {
        font-size: 5.5vw;
        font-weight: 800;
        text-align: center;
        background: linear-gradient(90deg, #7FFFD4, #45B39D);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-top: -40px;
        margin-bottom: 0px;
        text-transform: uppercase;
        letter-spacing: -2px;
    }
    
    .subtitulo-principal {
        font-size: 1.1rem;
        font-weight: 300;
        color: #888888 !important;
        text-align: center;
        margin-bottom: 40px;
        letter-spacing: 5px;
        text-transform: uppercase;
    }

    /* Encabezados de sección */
    .seccion-titulo {
        font-size: 24px;
        font-weight: 600;
        margin-top: 30px;
        margin-bottom: 20px;
        border-left: 5px solid #7FFFD4;
        padding-left: 15px;
    }

    /* Tarjetas de métricas */
    .metric-card {
        background-color: #111111;
        border: 1px solid #222222;
        border-radius: 15px;
        padding: 25px;
        text-align: center;
    }
    .metric-label {
        font-size: 14px;
        color: #888888 !important;
        text-transform: uppercase;
    }
    .metric-value {
        font-size: 36px;
        font-weight: 700;
        color: #7FFFD4 !important;
    }

    /* Ajustes para la Sidebar y Expanders */
    .streamlit-expanderHeader {
        background-color: #111111 !important;
        color: #7FFFD4 !important;
        border-radius: 8px !important;
    }
    .descripcion {
        font-size: 12px;
        color: #7FFFD4 !important;
        opacity: 0.8;
        margin-bottom: 10px;
        font-style: italic;
    }
    </style>
""", unsafe_allow_html=True)

# Títulos Principales
st.markdown('<h1 class="titulo-principal">Gasoducto Trans-Andino</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitulo-principal">Gemelo Digital | Optimización de Procesos</p>', unsafe_allow_html=True)

# ------------------ DATOS TÉCNICOS (TABLAS DEL PROYECTO) ------------------
# Datos de tuberías API 5L Sch 40 [cite: 22, 23]
pipe_data_base = {
    "12\"": {"D_ext_mm": 323.8, "t_mm": 10.31, "costo_m": 185},
    "16\"": {"D_ext_mm": 406.4, "t_mm": 12.70, "costo_m": 260},
    "20\"": {"D_ext_mm": 508.0, "t_mm": 15.09, "costo_m": 350},
    "24\"": {"D_ext_mm": 609.6, "t_mm": 17.48, "costo_m": 440},
}

# Grados de acero [cite: 24, 25]
steel_data = {
    "X52": {"SMYS_psi": 52000, "F": 0.72},
    "X60": {"SMYS_psi": 60000, "F": 0.72},
}

# Constantes del gas [cite: 18, 19, 20]
L_total_km = 400.0
T1_K = 293.15  # 20°C
gamma = 0.65
Z = 0.90
k_gas = 1.28
eficiencia_comp = 0.85

# ------------------ BARRA LATERAL (SIDEBAR) ------------------
st.sidebar.markdown('<p style="font-size:22px; font-weight:700; color:#7FFFD4; text-align:center;">⚙️ CONFIGURACIÓN</p>', unsafe_allow_html=True)

with st.sidebar.expander("💰 PARÁMETROS ECONÓMICOS", expanded=True):
    costo_energia = st.number_input("Costo energético (USD/kWh)", min_value=0.01, value=0.08, step=0.01, format="%.3f")
    tasa_interes = st.number_input("Tasa de interés (% anual)", min_value=0.0, max_value=30.0, value=10.0, step=0.5)
    factor_acero = st.number_input("Factor de acero (Mercado)", min_value=0.1, value=0.70, step=0.05)

with st.sidebar.expander("📏 TUBERÍA Y MATERIAL", expanded=True):
    diametro_nom = st.selectbox("Diámetro nominal (pulg)", list(pipe_data_base.keys()), index=3)
    grado_acero = st.selectbox("Grado del acero", list(steel_data.keys()), index=1)

with st.sidebar.expander("🔧 OPERACIONES", expanded=True):
    Q_mmscfd = st.number_input("Flujo de gas (MMscfd)", min_value=10, value=500, step=10)
    N_estaciones = st.slider("Número de estaciones (N)", min_value=1, max_value=6, value=1)

# ------------------ LÓGICA DE CÁLCULO ------------------
def ejecutar_simulacion():
    # 1. Dimensionamiento
    D_ext_pulg = pipe_data_base[diametro_nom]["D_ext_mm"] / 25.4
    t_pulg = pipe_data_base[diametro_nom]["t_mm"] / 25.4
    D_int_pulg = D_ext_pulg - 2 * t_pulg
    
    # MAOP (Límite de Barlow) [cite: 46]
    SMYS = steel_data[grado_acero]["SMYS_psi"]
    F_diseno = steel_data[grado_acero]["F"]
    MAOP = (2 * SMYS * t_pulg * F_diseno) / D_ext_pulg
    
    # 2. Hidráulica (Weymouth) [cite: 27, 28]
    L_seg_millas = (L_total_km * 0.621371) / N_estaciones
    T_R = T1_K * 1.8 # Rankine
    # K de Weymouth simplificado para el tramo
    K_weymouth = 433.5 * pow(Q_mmscfd/1.0, 2) * L_seg_millas * gamma * T_R * Z / pow(D_int_pulg, 5.33)
    
    P_entrega_min = 500.0
    P_descarga = sqrt(pow(P_entrega_min, 2) + K_weymouth)
    
    # 3. Potencia y Temperatura [cite: 30, 31]
    P_succion_inicial = 800.0
    # Relación de compresión r = P_out / P_in
    r = P_descarga / P_succion_inicial
    
    # Ecuación de potencia HP
    potencia_estacion = (Q_mmscfd * 1e6 / (24*3600*eficiencia_comp)) * (Z * 10.73 * T1_K / (k_gas - 1)) * (pow(r, (k_gas-1)/k_gas) - 1)
    HP_total = potencia_estacion * N_estaciones
    T2_C = (T1_K * pow(r, (k_gas-1)/k_gas)) - 273.15
    
    # 4. Economía (TAC) [cite: 32, 33]
    capex_ducto = L_total_km * 1000 * pipe_data_base[diametro_nom]["costo_m"] * factor_acero
    capex_comp = HP_total * 1500.0 # Estimado 1500 USD/HP
    CAPEX_total = capex_ducto + capex_comp
    
    i = tasa_interes / 100
    n_anios = 20
    CRF = (i * pow(1+i, n_anios)) / (pow(1+i, n_anios) - 1) if i > 0 else 1/n_anios
    
    opex_energia = HP_total * 0.7457 * 8760 * costo_energia # HP a kWh anual
    opex_mant = CAPEX_total * 0.02
    OPEX_total = opex_energia + opex_mant
    
    TAC = (CAPEX_total * CRF) + OPEX_total
    
    return {
        "TAC": TAC, "HP": HP_total, "P_final": P_entrega_min, "P_desc": P_descarga,
        "MAOP": MAOP, "T2": T2_C, "CAPEX": CAPEX_total, "OPEX": OPEX_total, "CRF": CRF,
        "D_int": D_int_pulg
    }

res = ejecutar_simulacion()

# ------------------ VISUALIZACIÓN PRINCIPAL ------------------
st.markdown('<div class="seccion-titulo">📊 RESULTADOS CLAVE</div>', unsafe_allow_html=True)
c1, c2, c3 = st.columns(3)
with c1:
    st.markdown(f'<div class="metric-card"><div class="metric-label">💰 TAC (USD/AÑO)</div><div class="metric-value">${res["TAC"]:,.0f}</div></div>', unsafe_allow_html=True)
with c2:
    st.markdown(f'<div class="metric-card"><div class="metric-label">⚙️ POTENCIA TOTAL</div><div class="metric-value">{res["HP"]:,.0f} <span style="font-size:16px">HP</span></div></div>', unsafe_allow_html=True)
with c3:
    st.markdown(f'<div class="metric-card"><div class="metric-label">📉 PRESIÓN FINAL</div><div class="metric-value">{res["P_final"]:.1f} <span style="font-size:16px">psia</span></div></div>', unsafe_allow_html=True)

# Perfil Hidráulico Dinámico [cite: 42, 43]
st.markdown('<div class="seccion-titulo">📈 PERFIL HIDRÁULICO</div>', unsafe_allow_html=True)
dist = []
pres = []
d_step = L_total_km / N_estaciones
for n in range(N_estaciones):
    dist.extend([n*d_step, (n+1)*d_step])
    pres.extend([res["P_desc"], 500.0])

fig = go.Figure()
fig.add_trace(go.Scatter(x=dist, y=pres, mode='lines+markers', line=dict(color='#7FFFD4', width=3)))
fig.update_layout(plot_bgcolor='black', paper_bgcolor='black', font_color='white', margin=dict(l=20, r=20, t=20, b=20))
st.plotly_chart(fig, use_container_width=True)

# Alertas de Seguridad [cite: 45, 46, 47, 48]
st.markdown('<div class="seccion-titulo">⚠️ VALIDACIÓN DE SEGURIDAD</div>', unsafe_allow_html=True)
if res["P_desc"] > res["MAOP"]:
    st.error(f"🚨 EXCESO DE PRESIÓN: {res['P_desc']:.1f} > MAOP {res['MAOP']:.1f} psia")
else:
    st.success(f"✅ Presión Segura: {res['P_desc']:.1f} < {res['MAOP']:.1f} psia (MAOP)")

if res["T2"] > 65.0:
    st.error(f"🔥 ALERTA TÉRMICA: {res['T2']:.1f}°C > 65°C")
else:
    st.success(f"✅ Temperatura Controlada: {res['T2']:.1f}°C")

with st.expander("🔍 DETALLES TÉCNICOS"):
    st.write(f"**Diámetro Interno:** {res['D_int']:.2f} pulg")
    st.write(f"**CAPEX Total:** ${res['CAPEX']:,.0f}")
    st.write(f"**OPEX Total:** ${res['OPEX']:,.0f}")
    st.write(f"**Factor CRF:** {res['CRF']:.4f}")
