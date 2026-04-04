import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# ==========================================================
# 1. CONFIGURACIÓN DE PÁGINA Y ESTILO CSS (FONDO NEGRO)
# ==========================================================
st.set_page_config(
    page_title="Gasoducto Trans-Andino",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    /* Fondo general oscuro y texto base claro */
    .stApp { background-color: #0d1117; color: #c9d1d9; }
    
    /* Títulos y encabezados en blanco */
    h1, h2, h3, h4 { color: #ffffff !important; font-weight: 500; }
    
    /* Sidebar a la derecha y fondo oscuro */
    section[data-testid="stSidebar"] { 
        background-color: #161b22; 
        border-left: 1px solid #30363d;
        order: 2; 
    }
    .main > div { flex-direction: row-reverse; }
    
    /* Inputs y selectores adaptados al tema oscuro */
    .stNumberInput > div > div > input, 
    .stSelectbox > div > div > select,
    .stSlider > div > div > div { 
        background-color: #0d1117; 
        color: #ffffff; 
        border-color: #30363d; 
    }
    
    /* Tarjetas de métricas */
    .metric-box { 
        background-color: #161b22; 
        padding: 1.2rem; 
        border-radius: 8px; 
        border: 1px solid #30363d; 
        text-align: center; 
    }
    
    /* Cajas de validación (sin emojis, profesionales) */
    .valid-ok { 
        background-color: #0d2818; 
        color: #3fb950; 
        padding: 0.8rem; 
        border-radius: 6px; 
        border-left: 4px solid #3fb950; 
        margin: 6px 0; 
    }
    .valid-alert { 
        background-color: #2d1214; 
        color: #f85149; 
        padding: 0.8rem; 
        border-radius: 6px; 
        border-left: 4px solid #f85149; 
        margin: 6px 0; 
    }
    
    /* Divisores y textos secundarios */
    hr { border-color: #30363d; margin: 1rem 0; }
    .stCaption { color: #8b949e; }
</style>
""", unsafe_allow_html=True)

# ==========================================================
# 2. BASE DE DATOS TÉCNICA
# ==========================================================
TUBERIAS = {
    "12": {"OD_mm": 323.8, "t_mm": 10.31, "costo_m": 185},
    "16": {"OD_mm": 406.4, "t_mm": 12.70, "costo_m": 260},
    "20": {"OD_mm": 508.0, "t_mm": 15.09, "costo_m": 350},
    "24": {"OD_mm": 609.6, "t_mm": 17.48, "costo_m": 440}
}

ACEROS = {
    "X52": {"SMYS_psi": 52000, "F": 0.72},
    "X60": {"SMYS_psi": 60000, "F": 0.72}
}

# Parámetros fijos del caso base
L_KM = 400.0
P_IN = 800.0
P_MIN_ENTREGA = 500.0
T_SUC_C = 20.0
T_SUC_R = (T_SUC_C + 273.15) * 1.8  # Kelvin a Rankine
GAMMA = 0.65
Z = 0.90
K_GAS = 1.30
ETA_COMP = 0.85
E_HID = 0.92          # Eficiencia hidráulica estándar
R_GAS = 10.7316       # psi·ft³/(lbmol·°R)
HORAS_ANIO = 8000.0
VIDA_ANIOS = 20

# ==========================================================
# 3. FUNCIONES DE CÁLCULO
# ==========================================================
def diametro_interno(od_mm, t_mm):
    """Calcula el diámetro interno en pulgadas"""
    return (od_mm - 2 * t_mm) / 25.4

def caida_presion_weymouth(P1, Q, L_km, D_in, gamma, T_R, Z, E_hid):
    """
    Ecuación de Weymouth del enunciado.
    P1^2 - P2^2 = 433.5 * (Q/E)^2 * L * gamma * T * Z / D^5.33
    Nota: La constante 433.5 está calibrada para L en millas y T en Rankine.
    Se convierte internamente para mantener coherencia dimensional.
    """
    L_mi = L_km * 0.621371  # km -> millas
    termino = 433.5 * ((Q / E_hid)**2) * (L_mi * gamma * T_R * Z) / (D_in**5.33)
    P2_cuad = P1**2 - termino
    return np.sqrt(max(P2_cuad, 1.0))  # Evita raíces negadas por fricción extrema

def potencia_compresor(Q, P_suc, P_desc, T_R, Z, k, eta):
    """
    Potencia al freno (HP) según fórmula del enunciado.
    Estructura exacta del PDF con conversión a HP (1 HP = 550 ft·lbf/s)
    """
    r = P_desc / P_suc
    Q_ft3_s = (Q * 1e6) / (24.0 * 3600.0)  # MMscfd -> ft³/s
    
    # Cálculo directo de la ecuación solicitada
    HP = Q_ft3_s * (Z * R_GAS * T_R / eta) * (k / (k - 1.0)) * (r**((k - 1.0)/k) - 1.0) / 550.0
    return HP

def temp_descarga(T1_R, P_suc, P_desc, k):
    """Temperatura de descarga isentrópica en Rankine"""
    return T1_R * (P_desc / P_suc)**((k - 1.0)/k)

def maop_barlow(OD_in, t_in, SMYS, F):
    """Presión máxima admisible por ecuación de Barlow"""
    return (2.0 * SMYS * F * t_in) / OD_in

def crf(tasa, n):
    """Factor de Recuperación de Capital"""
    if tasa == 0: return 1.0 / n
    return (tasa * (1 + tasa)**n) / ((1 + tasa)**n - 1)

# ==========================================================
# 4. INTERFAZ: SIDEBAR (CONFIGURACIÓN)
# ==========================================================
with st.sidebar:
    st.markdown("## A. Panel de Configuración")
    st.divider()
    
    st.markdown("### Parámetros Económicos")
    costo_energia = st.number_input("Costo de energía (USD/kWh)", min_value=0.01, max_value=0.50, value=0.08, step=0.01)
    factor_acero = st.number_input("Factor multiplicador costo acero", min_value=0.5, max_value=2.0, value=1.0, step=0.1)
    tasa_interes = st.number_input("Tasa de interés anual (%)", min_value=1.0, max_value=25.0, value=8.0, step=0.5) / 100.0
    costo_comp_HP = st.number_input("Costo compresor (USD/HP)", min_value=500, max_value=5000, value=1500, step=100)
    
    st.markdown("### Selección de Material")
    dn_sel = st.selectbox("Diámetro nominal (pulg)", options=list(TUBERIAS.keys()))
    acero_sel = st.selectbox("Grado del acero", options=list(ACEROS.keys()))
    
    st.markdown("### Variables Operativas")
    Q = st.number_input("Flujo de gas Q (MMscfd)", min_value=50.0, max_value=1500.0, value=500.0, step=50.0)
    N = st.slider("N° estaciones de compresión (N)", min_value=1, max_value=8, value=3, step=1)

# ==========================================================
# 5. PROCESAMIENTO Y SIMULACIÓN
# ==========================================================
tub = TUBERIAS[dn_sel]
ace = ACEROS[acero_sel]

OD_in = tub["OD_mm"] / 25.4
t_in = tub["t_mm"] / 25.4
D_in = diametro_interno(tub["OD_mm"], tub["t_mm"])
MAOP = maop_barlow(OD_in, t_in, ace["SMYS_psi"], ace["F"])

L_seg_km = L_KM / (N + 1)
distancias = [0.0]
presiones = [P_IN]
P_actual = P_IN
HP_total = 0.0
T_max_C = 0.0
factible = True

for i in range(N + 1):
    # Caída de presión en el segmento actual
    P_fin = caida_presion_weymouth(P_actual, Q, L_seg_km, D_in, GAMMA, T_SUC_R, Z, E_HID)
    dist_km = (i + 1) * L_seg_km
    
    if P_fin < 10.0:  # Límite de seguridad física
        st.markdown('<div class="valid-alert">Presión colapsada en tramo. Diseño inviable.</div>', unsafe_allow_html=True)
        factible = False
        break
        
    distancias.append(dist_km)
    presiones.append(P_fin)
    
    # Si no es el último tramo, simula la estación de compresión
    if i < N:
        HP_est = potencia_compresor(Q, P_fin, P_IN, T_SUC_R, Z, K_GAS, ETA_COMP)
        HP_total += HP_est
        
        T2_R = temp_descarga(T_SUC_R, P_fin, P_IN, K_GAS)
        T2_C = (T2_R - 491.67) * 5.0 / 9.0
        if T2_C > T_max_C: T_max_C = T2_C
        
        # Punto de recomposición (salto vertical en el gráfico)
        distancias.append(dist_km)
        presiones.append(P_IN)
        P_actual = P_IN
    else:
        P_ENTREGA = P_fin

if not factible:
    st.stop()

# Cálculos económicos
CAPEX_ducto = L_KM * 1000 * tub["costo_m"] * factor_acero
CAPEX_comp = HP_total * costo_comp_HP
CAPEX_total = CAPEX_ducto + CAPEX_comp
CRF_VAL = crf(tasa_interes, VIDA_ANIOS)
OPEX = (HP_total * 0.7457) * HORAS_ANIO * costo_energia
TAC = (CAPEX_total * CRF_VAL) + OPEX

# ==========================================================
# 6. VISUALIZACIÓN PRINCIPAL (MAIN PANEL)
# ==========================================================
st.title("Gemelo Digital: Gasoducto Trans-Andino")
st.caption("Simulación hidráulica, energética y económica de transporte de gas natural")

st.divider()
st.subheader("B. Dashboard de Métricas")
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(f'<div class="metric-box"><h3>TAC Anualizado</h3><p style="font-size:1.4rem; margin:0;">${TAC:,.0f}</p></div>', unsafe_allow_html=True)
with col2:
    st.markdown(f'<div class="metric-box"><h3>Potencia Instalada</h3><p style="font-size:1.4rem; margin:0;">{HP_total:,.0f} HP</p></div>', unsafe_allow_html=True)
with col3:
    st.markdown(f'<div class="metric-box"><h3>Presión de Entrega</h3><p style="font-size:1.4rem; margin:0;">{P_ENTREGA:.1f} psia</p></div>', unsafe_allow_html=True)

# Gráfico 1: Perfil Hidráulico
st.subheader("Perfil Hidráulico: Presión vs Distancia")
fig_hid = go.Figure()
fig_hid.add_trace(go.Scatter(x=distancias, y=presiones, mode='lines+markers', name='Presión', 
                             line=dict(color='#58a6ff', width=2.5), marker=dict(size=5, color='#ffffff')))
fig_hid.add_hline(y=P_MIN_ENTREGA, line_dash="dash", line_color="#f85149", annotation_text=f"Min. Entrega ({P_MIN_ENTREGA} psia)")
fig_hid.add_hline(y=MAOP, line_dash="dash", line_color="#d29922", annotation_text=f"MAOP ({MAOP:.0f} psia)")
fig_hid.update_layout(
    xaxis_title="Distancia [km]", yaxis_title="Presión [psia]",
    template="plotly_dark", height=450,
    paper_bgcolor="#0d1117", plot_bgcolor="#0d1117",
    font=dict(color="#c9d1d9"), margin=dict(l=0, r=0, t=20, b=0)
)
st.plotly_chart(fig_hid, use_container_width=True)

# Gráfico 2: Desglose de Costos
st.subheader("Desglose del Costo Total Anualizado")
df_costos = pd.DataFrame({
    "Concepto": ["CAPEX Tubería", "CAPEX Compresores", "OPEX Energía"],
    "Monto [USD/año]": [CAPEX_ducto*CRF_VAL, CAPEX_comp*CRF_VAL, OPEX]
})
fig_cost = px.bar(df_costos, x="Concepto", y="Monto [USD/año]", text_auto=True,
                  color="Concepto", color_discrete_sequence=["#58a6ff", "#3fb950", "#d29922"])
fig_cost.update_layout(
    template="plotly_dark", height=400, showlegend=False,
    paper_bgcolor="#0d1117", plot_bgcolor="#0d1117",
    font=dict(color="#c9d1d9"), margin=dict(l=0, r=0, t=20, b=0)
)
fig_cost.update_traces(texttemplate='$%{y:,.0f}', textposition='outside')
st.plotly_chart(fig_cost, use_container_width=True)

# ==========================================================
# 7. SISTEMA DE VALIDACIÓN Y ALERTAS
# ==========================================================
st.divider()
st.subheader("C. Validaciones de Seguridad y Operación")
col_v1, col_v2, col_v3 = st.columns(3)

with col_v1:
    if P_IN > MAOP:
        st.markdown('<div class="valid-alert">MAOP Excedido: Presión de descarga supera límite de Barlow.</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="valid-ok">MAOK Aprobado: {P_IN} psia ≤ {MAOP:.0f} psia</div>', unsafe_allow_html=True)

with col_v2:
    if T_max_C > 65.0:
        st.markdown(f'<div class="valid-alert">Límite Térmico: T_desc {T_max_C:.1f} °C > 65 °C</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="valid-ok">Temperatura OK: Máx {T_max_C:.1f} °C ≤ 65 °C</div>', unsafe_allow_html=True)

with col_v3:
    if P_ENTREGA < P_MIN_ENTREGA:
        st.markdown(f'<div class="valid-alert">Entrega Insuficiente: {P_ENTREGA:.1f} psia < {P_MIN_ENTREGA} psia</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="valid-ok">Entrega Cumplida: {P_ENTREGA:.1f} psia ≥ {P_MIN_ENTREGA} psia</div>', unsafe_allow_html=True)
