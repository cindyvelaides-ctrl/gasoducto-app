import streamlit as st
import numpy as np
import plotly.graph_objects as go
import pandas as pd
import math

# Configuración inicial de la página
st.set_page_config(
    page_title="Gemelo Digital: Gasoducto Trans-Andino",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# 1. DATOS TÉCNICOS Y CONSTANTES
# =========================================================
DATOS_TUBERIAS = {
    "12 pulgadas": {"D_ext_mm": 323.8, "t_mm": 10.31, "costo_m": 185},
    "16 pulgadas": {"D_ext_mm": 406.4, "t_mm": 12.70, "costo_m": 260},
    "20 pulgadas": {"D_ext_mm": 508.0, "t_mm": 15.09, "costo_m": 350},
    "24 pulgadas": {"D_ext_mm": 609.6, "t_mm": 17.48, "costo_m": 440}
}

DATOS_ACERO = {
    "X52": {"SMYS_psi": 52000, "F": 0.72},
    "X60": {"SMYS_psi": 60000, "F": 0.72}
}

# Parámetros base del caso de estudio
PIN = 800.0           # psia (Presión de descarga/recepción)
L_TOTAL_KM = 400.0    # km
P_MIN_ENTREGA = 500.0 # psia
T_SUC_K = 293.15      # K (20 C)
GAMMA = 0.65
Z = 0.90
E_HID = 0.92          # Eficiencia hidráulica (E)
K_GAS = 1.30          # Relación de calores específicos (k)
ETA_COMP = 0.85       # Eficiencia isentrópica
R_GAS = 10.7316       # psi·ft³/(lbmol·°R)
VIDA_UTIL = 20        # años
COSTO_COMP_HP = 1500  # USD/HP instalado (estimación académica estándar)
HORAS_ANIO = 8760.0

# =========================================================
# 2. FUNCIONES DE CÁLCULO
# =========================================================
def calcular_crf(tasa, n=VIDA_UTIL):
    """Factor de Recuperación de Capital"""
    if tasa == 0:
        return 1.0 / n
    return (tasa * (1 + tasa)**n) / ((1 + tasa)**n - 1)

def calcular_maop(smys, t_mm, d_ext_mm, f):
    """Ecuación de Barlow para Presión Máxima de Operación Permitida"""
    t_in = t_mm / 25.4
    d_in = d_ext_mm / 25.4
    return (2.0 * smys * t_in * f) / d_in

def calcular_caida_presion_weymouth(Q, L_km, D_in):
    """
    Ecuación de Weymouth del enunciado.
    P1^2 - P2^2 = 433.5 * (Q/E)^2 * (L * gamma * T * Z) / D^5.33
    NOTA: La constante 433.5 está calibrada para L en millas y T en Rankine.
    Se realizan las conversiones internas para mantener coherencia dimensional.
    """
    L_mi = L_km * 0.621371  # km -> millas
    T_R = T_SUC_K * 1.8     # Kelvin -> Rankine
    
    termino = 433.5 * ((Q / E_HID)**2) * (L_mi * GAMMA * T_R * Z) / (D_in**5.33)
    return termino  # Retorna (P1^2 - P2^2) en psia^2

def calcular_potencia_compresor(Q, eta, Z, k, T1_K, P_out, P_in):
    """
    Potencia por estación según ecuación del enunciado.
    HP = [ (Q * 10^6) / (24 * 3600) ] * [ Z * R * T1 / eta ] * [ k/(k-1) ] * [ (Pout/Pin)^((k-1)/k) - 1 ]
    Se añade la división por 550 para convertir ft·lbf/s a HP mecánicos.
    """
    T1_R = T1_K * 1.8
    r = P_out / P_in
    
    flujo_volumetrico = (Q * 1e6) / (24.0 * 3600.0)
    trabajo_flujo = flujo_volumetrico * (Z * R_GAS * T1_R / eta) * (k / (k - 1.0)) * (r**((k-1.0)/k) - 1.0)
    return trabajo_flujo / 550.0

def calcular_temperatura_descarga(T1_K, k, P_out, P_in):
    """T2 = T1 * (Pout/Pin)^((k-1)/k)"""
    r = P_out / P_in
    return T1_K * (r**((k - 1.0)/k))

def generar_perfil_hidraulico(Q, D_in, N_est, L_km):
    """Genera arrays de distancia y presión simulando caídas y recompresiones"""
    n_segmentos = N_est + 1
    L_seg_km = L_km / n_segmentos
    
    distancias = [0.0]
    presiones = [PIN]
    p_actual = PIN
    
    for i in range(n_segmentos):
        caida_P2 = calcular_caida_presion_weymouth(Q, L_seg_km, D_in)
        p_fin_seg = math.sqrt(max(p_actual**2 - caida_P2, 0))
        
        dist_actual = distancias[-1] + L_seg_km
        distancias.append(dist_actual)
        presiones.append(p_fin_seg)
        
        if i < n_segmentos - 1:
            # Simulación de la estación de compresión (retorno a PIN)
            distancias.append(dist_actual)
            presiones.append(PIN)
            p_actual = PIN
        else:
            p_actual = p_fin_seg
            
    return np.array(distancias), np.array(presiones), p_actual

# =========================================================
# 3. INTERFAZ STREAMLIT
# =========================================================
st.title("Gemelo Digital: Gasoducto Trans-Andino")
st.markdown("Herramienta interactiva para el dimensionamiento hidráulico, energético y económico.")

# --- A. PANEL DE CONFIGURACIÓN (SIDEBAR) ---
with st.sidebar:
    st.header("A. Panel de Configuración")
    
    st.subheader("Variables Operativas")
    Q = st.number_input("Flujo de gas Q [MMscfd]", min_value=50.0, max_value=1500.0, value=500.0, step=10.0)
    N_est = st.number_input("Número de estaciones de compresión N", min_value=1, max_value=15, value=4, step=1)
    
    st.subheader("Selección de Material")
    diam_sel = st.selectbox("Diámetro nominal", list(DATOS_TUBERIAS.keys()))
    acero_sel = st.selectbox("Grado de acero", list(DATOS_ACERO.keys()))
    
    st.subheader("Parámetros Económicos")
    costo_energia = st.number_input("Costo de energía [USD/kWh]", min_value=0.01, max_value=0.50, value=0.08, step=0.01)
    factor_acero = st.number_input("Factor multiplicador costo acero", min_value=0.5, max_value=2.0, value=1.0, step=0.1)
    tasa_interes = st.number_input("Tasa de interés anual [%]", min_value=1.0, max_value=25.0, value=8.0, step=0.5) / 100.0

# --- PROCESAMIENTO ---
tub = DATOS_TUBERIAS[diam_sel]
ace = DATOS_ACERO[acero_sel]

D_in = tub["D_ext_mm"] / 25.4
costo_tubo_m = tub["costo_m"] * factor_acero
SMYS = ace["SMYS_psi"]
F = ace["F"]

# Cálculos hidráulicos
dist, pres, P_entrega = generar_perfil_hidraulico(Q, D_in, N_est, L_TOTAL_KM)

# Cálculos de compresión (presión de succión uniforme por diseño simétrico)
caida_P2_seg = calcular_caida_presion_weymouth(Q, L_TOTAL_KM/(N_est+1), D_in)
P_suc_calc = math.sqrt(max(PIN**2 - caida_P2_seg, 0))
r_comp = PIN / P_suc_calc

T2_K = calcular_temperatura_descarga(T_SUC_K, K_GAS, PIN, P_suc_calc)
T2_C = T2_K - 273.15
HP_est = calcular_potencia_compresor(Q, ETA_COMP, Z, K_GAS, T_SUC_K, PIN, P_suc_calc)
HP_total = HP_est * N_est

# Cálculos económicos
MAOP = calcular_maop(SMYS, tub["t_mm"], tub["D_ext_mm"], F)
CRF = calcular_crf(tasa_interes)

CAPEX_ducto = L_TOTAL_KM * 1000 * costo_tubo_m
CAPEX_comp = HP_total * COSTO_COMP_HP
CAPEX_total = CAPEX_ducto + CAPEX_comp

potencia_kw = HP_total * 0.7457
OPEX_energia = potencia_kw * HORAS_ANIO * costo_energia
TAC = (CAPEX_total * CRF) + OPEX_energia

# --- B. VISUALIZACIÓN PRINCIPAL (MAIN PANEL) ---
st.divider()
st.subheader("B. Dashboard de Métricas")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Costo Total Anualizado (TAC)", f"${TAC:,.0f}")
with col2:
    st.metric("Potencia Instalada Total", f"{HP_total:,.0f} HP")
with col3:
    st.metric("Presión Final de Entrega", f"{P_entrega:.1f} psia")

st.subheader("Perfil Hidráulico")
fig_hid = go.Figure()
fig_hid.add_trace(go.Scatter(x=dist, y=pres, mode='lines+markers', name='Presión', line=dict(color='#1f4e79', width=2)))
fig_hid.add_shape(type="line", x0=0, x1=L_TOTAL_KM, y0=P_MIN_ENTREGA, y1=P_MIN_ENTREGA, line=dict(color="red", width=2, dash="dash"))
fig_hid.update_layout(
    xaxis_title="Distancia [km]", 
    yaxis_title="Presión [psia]", 
    template="simple_white", 
    hovermode="x unified",
    yaxis_range=[0, max(PIN, MAOP)*1.1]
)
st.plotly_chart(fig_hid, use_container_width=True)

st.subheader("Desglose de Costos")
df_costos = pd.DataFrame({
    "Concepto": ["CAPEX Ducto", "CAPEX Compresores", "OPEX Energía Anual"],
    "Monto USD": [CAPEX_ducto, CAPEX_comp, OPEX_energia]
})
fig_cost = go.Figure(data=[go.Pie(labels=df_costos["Concepto"], values=df_costos["Monto USD"], hole=0.4)])
fig_cost.update_layout(template="simple_white")
st.plotly_chart(fig_cost, use_container_width=True)

# --- C. SISTEMA DE VALIDACIÓN Y ALERTAS ---
st.divider()
st.subheader("C. Sistema de Validación y Alertas")
col_v1, col_v2, col_v3 = st.columns(3)

with col_v1:
    if PIN > MAOP:
        st.error(f"ALERTA: Presión de descarga ({PIN} psia) supera MAOP ({MAOP:.0f} psia). Ajustar espesor o grado de acero.")
    else:
        st.success(f"VALIDO: Presión de descarga ({PIN} psia) dentro del límite MAOP ({MAOP:.0f} psia).")

with col_v2:
    if T2_C > 65.0:
        st.error(f"ALERTA: Temperatura de descarga ({T2_C:.1f} C) supera el límite de 65 C. Requerir enfriamiento intermedio.")
    else:
        st.success(f"VALIDO: Temperatura de descarga ({T2_C:.1f} C) dentro del límite térmico.")

with col_v3:
    if P_entrega < P_MIN_ENTREGA:
        st.error(f"ALERTA: Presión de entrega ({P_entrega:.1f} psia) es inferior a {P_MIN_ENTREGA} psia. Incrementar N o diámetro.")
    else:
        st.success(f"VALIDO: Presión de entrega ({P_entrega:.1f} psia) cumple requisito mínimo.")
