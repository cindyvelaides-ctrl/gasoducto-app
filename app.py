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
# 1. DATOS TÉCNICOS Y CONSTANTES (Base de datos del proyecto)
# =========================================================
DATOS_TUBERIAS = {
    "12 pulgadas": {"D_ext_mm": 323.8, "t_mm": 10.31, "costo_base": 185},
    "16 pulgadas": {"D_ext_mm": 406.4, "t_mm": 12.70, "costo_base": 260},
    "20 pulgadas": {"D_ext_mm": 508.0, "t_mm": 15.09, "costo_base": 350},
    "24 pulgadas": {"D_ext_mm": 609.6, "t_mm": 17.48, "costo_base": 440}
}

DATOS_ACERO = {
    "X52": {"SMYS_psi": 52000, "F": 0.72},
    "X60": {"SMYS_psi": 60000, "F": 0.72}
}

# Parámetros base del caso de estudio
P_IN = 800.0          # psia
L_TOTAL = 400.0       # km
P_MIN_ENTREGA = 500.0 # psia
T_SUC = 293.15        # K (20 °C)
GAMMA = 0.65
Z = 0.90
E_HID = 0.92          # Eficiencia hidráulica estándar
K_GAS = 1.30          # Relación de calores específicos
ETA_COMP = 0.85       # Eficiencia isentrópica del compresor
R_GAS = 10.7316       # psi·ft³/(lbmol·°R)
VIDA_UTIL = 20        # años para CRF

# =========================================================
# 2. FUNCIONES DE CÁLCULO
# =========================================================
def calcular_crf(tasa, n=VIDA_UTIL):
    """Calcula el Factor de Recuperación de Capital (CRF)"""
    if tasa == 0:
        return 1.0 / n
    return (tasa * (1 + tasa)**n) / ((1 + tasa)**n - 1)

def calcular_maop(smys, t_mm, d_ext_mm, f):
    """Ecuación de Barlow para MAOP (Presión Máxima de Operación Permitida)"""
    t_in = t_mm / 25.4
    d_in = d_ext_mm / 25.4
    return (2.0 * smys * t_in * f) / d_in

def calcular_caida_presion(Q, L_seg, D_in):
    """Caída de presión por segmento usando Weymouth"""
    # Ecuación proporcionada: P1^2 - P2^2 = 433.5 * (Q/E)^2 * L * γ * T * Z / D^5.33
    numerador = 433.5 * ((Q / E_HID)**2) * L_seg * GAMMA * T_SUC * Z
    denominador = D_in**5.33
    return numerador / denominador

def calcular_potencia_compresor(Q, eta, Z, k, T1_K, r):
    """
    Potencia del compresor por estación.
    Nota: Se ajustó ligeramente la estructura del enunciado para mantener coherencia 
    dimensional estándar en sistemas de gas natural.
    """
    T1_R = T1_K * 1.8  # Conversión a Rankine
    base = (Q * 1e6) / (24.0 * 3600.0)
    # Termodinámica de compresión adiabática
    factor = (k / (k - 1.0)) * Z * R_GAS * T1_R / eta
    compresion = (r**((k - 1.0)/k)) - 1.0
    hp = (base * factor * compresion) / 550.0  # Conversión lbf·ft/s -> HP
    return hp

def calcular_temperatura_descarga(T1_K, k, r):
    """T2 = T1 * (P_out / P_in)^((k-1)/k)"""
    return T1_K * (r**((k - 1.0)/k))

def generar_perfil_hidraulico(Q, D_in, N_estaciones, L_km):
    """Genera arrays de distancia y presión para el gráfico"""
    n_segmentos = N_estaciones + 1
    L_seg = L_km / n_segmentos
    
    distancias = []
    presiones = []
    dist_actual = 0.0
    p_actual = P_IN  # Inicio en presión de recepción/descarga
    
    # Punto inicial
    distancias.append(0.0)
    presiones.append(p_actual)
    
    for i in range(n_segmentos):
        # Caída en el segmento
        delta_P2 = calcular_caida_presion(Q, L_seg, D_in)
        p_final_seg = math.sqrt(max(p_actual**2 - delta_P2, 0))
        
        # Guardar punto final del segmento
        dist_actual += L_seg
        distancias.append(dist_actual)
        presiones.append(p_final_seg)
        
        # Si hay más segmentos, simular recompresión (salto de presión)
        if i < n_segmentos - 1:
            distancias.append(dist_actual)
            presiones.append(P_IN) # Se asume que los compresores restauran a P_IN
            p_actual = P_IN
        else:
            p_actual = p_final_seg
            
    return np.array(distancias), np.array(presiones), p_actual

# =========================================================
# 3. INTERFAZ STREAMLIT
# =========================================================
st.title("Gemelo Digital: Optimización Gasoducto Trans-Andino")
st.markdown("Herramienta interactiva para el dimensionamiento hidráulico, energético y económico de transporte de gas natural a larga distancia.")

# --- A. PANEL DE CONFIGURACIÓN (SIDEBAR) ---
with st.sidebar:
    st.header("Configuración de Diseño")
    
    st.subheader("Parámetros Operativos")
    Q_input = st.number_input("Flujo de Gas (Q) [MMscfd]", min_value=100.0, max_value=1500.0, value=500.0, step=10.0)
    N_est = st.number_input("N° Estaciones de Compresión (N)", min_value=1, max_value=10, value=3, step=1)
    
    st.subheader("Selección de Material")
    diametro_sel = st.selectbox("Diámetro Nominal", list(DATOS_TUBERIAS.keys()))
    acero_sel = st.selectbox("Grado de Acero", list(DATOS_ACERO.keys()))
    
    st.subheader("Parámetros Económicos")
    costo_energia = st.number_input("Costo de Energía [USD/kWh]", min_value=0.01, max_value=0.50, value=0.10, step=0.01, format="%.3f")
    factor_acero = st.number_input("Factor de Costo del Acero (multiplicador)", min_value=0.5, max_value=2.0, value=1.0, step=0.1)
    tasa_interes = st.number_input("Tasa de Interés Anual [%]", min_value=1.0, max_value=20.0, value=8.0, step=0.5) / 100.0

# --- PROCESAMIENTO DE DATOS ---
dat_tubo = DATOS_TUBERIAS[diametro_sel]
dat_ac = DATOS_ACERO[acero_sel]

D_in = dat_tubo["D_ext_mm"] / 25.4
t_in = dat_tubo["t_mm"] / 25.4
costo_tubo_m = dat_tubo["costo_base"] * factor_acero
SMYS = dat_ac["SMYS_psi"]
F = dat_ac["F"]

# Cálculos principales
dist, pres, P_entrega = generar_perfil_hidraulico(Q_input, D_in, N_est, L_TOTAL)
ratio_compresion = P_IN / P_entrega if P_entrega > 0 else 1.0 # Aproximación inversa para sizing
# Para cálculo de HP usamos la relación real de descarga/succión. 
# En este modelo simplificado, asumimos que el compresor eleva de P_min_seg a P_IN.
# Calculamos la presión mínima antes de compresión para obtener el ratio real:
P_min_seg = pres[-1] if N_est > 1 else pres[-1]
r_comp = P_IN / max(P_min_seg, 1.0)

hp_estacion = calcular_potencia_compresor(Q_input, ETA_COMP, Z, K_GAS, T_SUC, r_comp)
hp_total = hp_estacion * N_est

t2 = calcular_temperatura_descarga(T_SUC, K_GAS, r_comp)
t2_c = t2 - 273.15

maop = calcular_maop(SMYS, dat_tubo["t_mm"], dat_tubo["D_ext_mm"], F)

crf = calcular_crf(tasa_interes)
l_m = L_TOTAL * 1000.0
capex_tuberia = l_m * costo_tubo_m
capex_compresores = hp_total * 1500.0  # Estimación estándar ~1500 USD/HP instalado
capex_total = capex_tuberia + capex_compresores

potencia_kw = hp_total * 0.7457
horas_anio = 24.0 * 365.0
opex_energia = potencia_kw * horas_anio * costo_energia

tac = (capex_total * crf) + opex_energia

# --- B. VISUALIZACIÓN PRINCIPAL ---
st.divider()
st.subheader("Resultados de la Configuración Actual")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="Costo Total Anualizado (TAC)", value=f"${tac:,.2f}")
with col2:
    st.metric(label="Potencia Instalada Total", value=f"{hp_total:,.0f} HP")
with col3:
    st.metric(label="Presión Final de Entrega", value=f"{P_entrega:.1f} psia")

# Gráfico 1: Perfil Hidráulico
st.subheader("Perfil Hidráulico: Presión vs Distancia")
fig_hid = go.Figure()
fig_hid.add_trace(go.Scatter(
    x=dist, y=pres, 
    mode='lines+markers', 
    name='Presión [psia]',
    line=dict(color='#1f4e79', width=3),
    marker=dict(size=6)
))
fig_hid.update_layout(
    xaxis_title="Distancia [km]",
    yaxis_title="Presión [psia]",
    yaxis=dict(range=[0, max(P_IN, maop) * 1.1]),
    hovermode="x unified",
    template="simple_white"
)
st.plotly_chart(fig_hid, use_container_width=True)

# Gráfico 2: Desglose de Costos
st.subheader("Desglose Económico")
df_costos = pd.DataFrame({
    "Componente": ["CAPEX Tubería", "CAPEX Compresores", "OPEX Energía Anual"],
    "Valor USD": [capex_tuberia, capex_compresores, opex_energia]
})
fig_costo = go.Figure()
fig_costo.add_trace(go.Pie(
    labels=df_costos["Componente"],
    values=df_costos["Valor USD"],
    hole=0.4,
    marker_colors=['#1f4e79', '#4472c4', '#ed7d31']
))
fig_costo.update_layout(template="simple_white")
st.plotly_chart(fig_costo, use_container_width=True)

# --- C. SISTEMA DE VALIDACIÓN Y ALERTAS ---
st.divider()
st.subheader("Validaciones de Seguridad y Operación")

col_v1, col_v2, col_v3 = st.columns(3)

with col_v1:
    if P_IN > maop:
        st.error(f"⛔ MAOP Excedido: P_desc ({P_IN:.0f} psia) > MAOP ({maop:.0f} psia). Reducir presión o aumentar espesor.")
    else:
        st.success(f"✅ MAOK Aprobado: P_desc ({P_IN:.0f} psia) ≤ MAOP ({maop:.0f} psia).")

with col_v2:
    if t2_c > 65.0:
        st.error(f"⛔ Límite Térmico: T_desc ({t2_c:.1f} °C) > 65 °C. Requiere enfriamiento o menor ratio.")
    else:
        st.success(f"✅ Temperatura Aprobada: T_desc ({t2_c:.1f} °C) ≤ 65 °C.")

with col_v3:
    if P_entrega < P_MIN_ENTREGA:
        st.error(f"⛔ Incumplimiento: P_entrega ({P_entrega:.1f} psia) < {P_MIN_ENTREGA} psia. Aumentar N o diámetro.")
    else:
        st.success(f"✅ Entrega Cumplida: P_final ({P_entrega:.1f} psia) ≥ {P_MIN_ENTREGA} psia.")
