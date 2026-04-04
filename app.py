# app.py
# Gemelo Digital: Gasoducto Trans-Andino (versión corregida y dark mode)
# Optimización de Procesos - Estudiante: [Tu nombre]

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import math

# --------------------------------------------------
# Configuración de la página (tema oscuro por defecto)
# --------------------------------------------------
st.set_page_config(
    page_title="Gasoducto Trans-Andino",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --------------------------------------------------
# ESTILO PERSONALIZADO: FONDO NEGRO, LETRAS BLANCAS, BARRA LATERAL DERECHA
# --------------------------------------------------
st.markdown("""
<style>
    /* Fondo general negro */
    .stApp {
        background-color: #0e1117;
    }
    /* Fondo del sidebar también oscuro pero ligeramente distinto */
    section[data-testid="stSidebar"] {
        background-color: #1a1c23;
        border-left: 1px solid #2c3e50;
    }
    /* Letras en general blancas */
    .stMarkdown, .stText, .stNumberInput label, .stSelectbox label, .stSlider label, .stMetric label {
        color: #ffffff !important;
    }
    /* Títulos principales */
    h1, h2, h3 {
        color: #00aaff !important;  /* Azul eléctrico llamativo */
        font-weight: 600;
    }
    /* Tarjetas de métricas con fondo gris oscuro y borde azul */
    .metric-card {
        background-color: #1e1e2e;
        padding: 1rem;
        border-radius: 12px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.3);
        text-align: center;
        border-top: 4px solid #00aaff;
    }
    /* Texto dentro de las tarjetas */
    .metric-card p, .metric-card label {
        color: #ffffff !important;
    }
    /* Botones y otros elementos */
    .stButton button {
        background-color: #00aaff;
        color: #0e1117;
        border-radius: 8px;
    }
    hr {
        margin: 0.8rem 0;
        border-color: #2c3e50;
    }
    /* Ajustar la barra lateral a la derecha (ya lo teníamos) */
    .main > div {
        flex-direction: row-reverse;
    }
    section[data-testid="stSidebar"] {
        order: 2;
    }
    /* Estilo de los expander */
    .streamlit-expanderHeader {
        color: #00aaff !important;
    }
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# Título principal con color llamativo (azul eléctrico)
# --------------------------------------------------
st.markdown("<h1 style='text-align: center; color: #00aaff;'>⚡ Gasoducto Trans‑Andino</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #cccccc;'>Simulación hidráulica y económica | Optimización de Procesos</p>", unsafe_allow_html=True)
st.markdown("---")

# --------------------------------------------------
# 1. BASE DE DATOS TÉCNICA (Tablas del enunciado)
# --------------------------------------------------
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

# --------------------------------------------------
# 2. PARÁMETROS FIJOS (caso de estudio)
# --------------------------------------------------
P_RECEPCION = 800.0         # psia
P_MIN_ENTREGA = 500.0       # psia
L_TOTAL_KM = 400.0          # km
T_SUC_C = 20                # °C
T_SUC_K = 293.15            # K
T_SUC_R = T_SUC_K * 1.8     # Rankine
GAMMA = 0.65                # gravedad específica
Z = 0.90
K = 1.30                    # relación de calores específicos (gas natural)
ETA_COMP = 0.85             # eficiencia politrópica
E_HID = 1.0                 # eficiencia hidráulica (1.0 para tubería nueva)
HORAS_ANUALES = 8000        # horas de operación al año
VIDA_PROYECTO = 20          # años
R_UNIV = 1545.4             # ft·lbf/(lbmol·R)
P_BASE = 14.7               # psia
T_BASE_R = 520              # Rankine (60°F)
MW_AIRE = 28.97
MW_GAS = GAMMA * MW_AIRE    # lb/lbmol

# --------------------------------------------------
# 3. FUNCIONES DE CÁLCULO (corregidas)
# --------------------------------------------------
def crf(tasa, n=VIDA_PROYECTO):
    """Factor de recuperación de capital (CRF)"""
    if tasa == 0:
        return 1.0 / n
    return (tasa * (1 + tasa)**n) / ((1 + tasa)**n - 1)

def maop_barlow(SMYS_psi, t_mm, D_ext_mm, F):
    """Presión máxima admisible (psia) - Barlow"""
    t_in = t_mm / 25.4
    D_in = D_ext_mm / 25.4
    return 2.0 * SMYS_psi * t_in * F / D_in

def caida_presion_weymouth(P1, Q, L_mi, D_in):
    """
    Retorna P2 (psia) después de un segmento.
    Usa la ecuación de Weymouth con eficiencia hidráulica E_HID = 1.0.
    """
    const = 433.5
    term = const * (Q / E_HID)**2 * (L_mi * GAMMA * T_SUC_R * Z) / (D_in**5.33)
    P2_cuad = P1**2 - term
    if P2_cuad <= 0.1:
        return 0.1
    return np.sqrt(P2_cuad)

def potencia_compresor(Q_MMscfd, P_suc_psia, P_desc_psia, T_suc_R, Z, k, MW, eta):
    """
    Potencia al freno (BHP) por compresor.
    Fórmula estándar con head politrópico.
    """
    r_p = P_desc_psia / P_suc_psia
    n = (k - 1) / k
    # Head politrópico (ft·lbf/lbm)
    H_p = (Z * R_UNIV * T_suc_R / MW) * (1 / n) * (r_p**n - 1)
    # Flujo másico (lb/s)
    Q_scf_s = Q_MMscfd * 1e6 / (24 * 3600)
    # Densidad en condiciones estándar (14.7 psia, 60°F)
    rho_std = (P_BASE * 144 * MW) / (R_UNIV * T_BASE_R)   # lb/scf
    m_dot = Q_scf_s * rho_std   # lb/s
    # Potencia
    BHP = (m_dot * H_p) / (550 * eta)
    return BHP

def temp_descarga(T_suc_R, P_suc, P_desc, k):
    """Temperatura de descarga en Rankine"""
    return T_suc_R * (P_desc / P_suc)**((k-1)/k)

def costo_tuberia(dn_key, factor_acero):
    """Costo total del ducto en USD"""
    costo_m = TUBERIAS[dn_key]["costo_base"] * factor_acero
    return costo_m * (L_TOTAL_KM * 1000)

# --------------------------------------------------
# 4. SIMULACIÓN DEL PERFIL DE PRESIÓN (con compresores)
# --------------------------------------------------
def simular_perfil(Q, D_in, N_est):
    """
    Retorna:
    - distancias_km (lista)
    - presiones_psia (lista)
    - potencia_total_HP
    - temperatura_max_C
    - presion_final_psia
    - factible (bool)
    """
    L_seg_mi = (L_TOTAL_KM * 0.621371) / (N_est + 1)
    distancias = [0.0]
    presiones = [P_RECEPCION]
    P_actual = P_RECEPCION
    HP_total = 0.0
    T_max_C = 0.0
    factible = True
    
    for i in range(N_est + 1):
        if i < N_est:
            # Caída de presión en el segmento
            P_fin_seg = caida_presion_weymouth(P_actual, Q, L_seg_mi, D_in)
            dist_km = (i+1) * (L_TOTAL_KM / (N_est + 1))
            distancias.append(dist_km)
            presiones.append(P_fin_seg)
            
            if P_fin_seg < 1.0:
                factible = False
                break
            
            # Potencia del compresor (eleva de P_fin_seg a P_RECEPCION)
            HP = potencia_compresor(Q, P_fin_seg, P_RECEPCION, T_SUC_R, Z, K, MW_GAS, ETA_COMP)
            HP_total += HP
            
            # Temperatura de descarga
            T2_R = temp_descarga(T_SUC_R, P_fin_seg, P_RECEPCION, K)
            T2_C = (T2_R - 491.67) * 5/9
            if T2_C > T_max_C:
                T_max_C = T2_C
            
            P_actual = P_RECEPCION
        else:
            # Último segmento (sin compresor al final)
            P_final = caida_presion_weymouth(P_actual, Q, L_seg_mi, D_in)
            dist_km = (i+1) * (L_TOTAL_KM / (N_est + 1))
            distancias.append(dist_km)
            presiones.append(P_final)
    
    return distancias, presiones, HP_total, T_max_C, presiones[-1], factible

# --------------------------------------------------
# 5. INTERFAZ DE USUARIO (SIDEBAR A LA DERECHA)
# --------------------------------------------------
with st.sidebar:
    st.markdown("## ⚙️ Configuración")
    st.markdown("---")
    
    st.markdown("### Económicos")
    costo_energia = st.number_input("Costo energía (USD/kWh)", min_value=0.01, max_value=0.50, value=0.05, step=0.01)
    factor_acero = st.number_input("Factor costo acero (x)", min_value=0.5, max_value=2.0, value=1.0, step=0.05)
    tasa_interes = st.number_input("Tasa interés (%)", min_value=1.0, max_value=20.0, value=8.0) / 100.0
    costo_comp_por_HP = st.number_input("Costo compresor (USD/HP)", min_value=800, max_value=2000, value=1200, step=100)
    
    st.markdown("### Materiales")
    diametro_sel = st.selectbox("Diámetro nominal", list(TUBERIAS.keys()))
    acero_sel = st.selectbox("Grado del acero", list(ACEROS.keys()))
    
    st.markdown("### Operación")
    Q_input = st.number_input("Flujo (MMscfd)", min_value=100.0, max_value=1500.0, value=500.0, step=50.0)
    N_est = st.slider("Número de estaciones de compresión", min_value=0, max_value=6, value=2, step=1)

# --------------------------------------------------
# 6. CÁLCULOS CON LOS PARÁMETROS SELECCIONADOS
# --------------------------------------------------
# Datos del material
dat_tubo = TUBERIAS[diametro_sel]
dat_ac = ACEROS[acero_sel]
D_ext_mm = dat_tubo["D_ext_mm"]
t_mm = dat_tubo["t_mm"]
D_in = (D_ext_mm - 2*t_mm) / 25.4   # pulgadas
SMYS = dat_ac["SMYS_psi"]
F = dat_ac["F"]

# MAOP
MAOP = maop_barlow(SMYS, t_mm, D_ext_mm, F)

# Simulación
distancias, presiones, HP_total, T_max_C, P_final, factible = simular_perfil(Q_input, D_in, N_est)

if not factible:
    st.error("Diseño inviable: la presión cae a valores extremadamente bajos. Aumente el diámetro o reduzca el flujo.")
    st.stop()

# Costos
costo_tuberia_total = costo_tuberia(diametro_sel, factor_acero)
costo_compresores_total = HP_total * costo_comp_por_HP
CAPEX = costo_tuberia_total + costo_compresores_total
CRF_val = crf(tasa_interes)
OPEX = HP_total * 0.7457 * HORAS_ANUALES * costo_energia   # HP a kW
TAC = CAPEX * CRF_val + OPEX

# --------------------------------------------------
# 7. MÉTRICAS PRINCIPALES (tarjetas)
# --------------------------------------------------
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

# --------------------------------------------------
# 8. PERFIL HIDRÁULICO (gráfico oscuro)
# --------------------------------------------------
st.markdown("## Perfil de presión")
fig = go.Figure()
fig.add_trace(go.Scatter(
    x=distancias, y=presiones,
    mode='lines+markers',
    name='Presión',
    line=dict(color='#00aaff', width=3),
    marker=dict(size=6, color='#ffaa00')
))
fig.add_hline(y=P_MIN_ENTREGA, line_dash="dash", line_color="#ff5555", annotation_text="P mínima entrega (500 psia)")
fig.add_hline(y=MAOP, line_dash="dash", line_color="#ffaa00", annotation_text=f"MAOP = {MAOP:.0f} psia")
fig.update_layout(
    xaxis_title="Distancia (km)",
    yaxis_title="Presión (psia)",
    template="plotly_dark",
    height=450,
    margin=dict(l=0, r=0, t=30, b=0),
    font=dict(color="#ffffff")
)
st.plotly_chart(fig, use_container_width=True)

# --------------------------------------------------
# 9. DESGLOSE DE COSTOS (gráfico de barras oscuro)
# --------------------------------------------------
st.markdown("## Desglose del costo anualizado")
costos_df = pd.DataFrame({
    "Concepto": ["CAPEX Tubería", "CAPEX Compresores", "OPEX Energía"],
    "Monto (USD/año)": [costo_tuberia_total * CRF_val, costo_compresores_total * CRF_val, OPEX]
})
fig2 = px.bar(
    costos_df, x="Concepto", y="Monto (USD/año)",
    text="Monto (USD/año)",
    color="Concepto",
    color_discrete_sequence=["#00aaff", "#ffaa00", "#44cc44"],
    title="Costo Total Anualizado (TAC)"
)
fig2.update_traces(texttemplate='$%{text:,.0f}', textposition='outside')
fig2.update_layout(
    template="plotly_dark",
    height=400,
    font=dict(color="#ffffff"),
    paper_bgcolor="#0e1117",
    plot_bgcolor="#0e1117"
)
st.plotly_chart(fig2, use_container_width=True)

# --------------------------------------------------
# 10. VALIDACIONES (alertas)
# --------------------------------------------------
st.markdown("## Validaciones de diseño")
col_al1, col_al2 = st.columns(2)
with col_al1:
    if P_RECEPCION > MAOP:
        st.error(f"MAOP superado: {P_RECEPCION} psia > {MAOP:.0f} psia")
    else:
        st.success(f"MAOP OK: {P_RECEPCION} psia ≤ {MAOP:.0f} psia")
    
    if T_max_C > 65:
        st.error(f"Temperatura máxima de descarga: {T_max_C:.1f} °C > 65 °C")
    else:
        st.success(f"Temperatura OK: máxima {T_max_C:.1f} °C ≤ 65 °C")

with col_al2:
    if P_final < P_MIN_ENTREGA:
        st.error(f"Presión final insuficiente: {P_final:.1f} psia < {P_MIN_ENTREGA} psia")
    else:
        st.success(f"Presión de entrega OK: {P_final:.1f} psia ≥ {P_MIN_ENTREGA} psia")

# --------------------------------------------------
# 11. DETALLES TÉCNICOS (expander)
# --------------------------------------------------
with st.expander("Detalles técnicos del diseño"):
    st.write(f"**Diámetro interno:** {D_in:.2f} in")
    st.write(f"**Espesor de pared:** {t_mm/25.4:.3f} in")
    st.write(f"**MAOP (Barlow):** {MAOP:.0f} psia")
    st.write(f"**Potencia total:** {HP_total:.0f} HP → {HP_total*0.7457:.0f} kW")
    st.write(f"**CRF (tasa {tasa_interes*100:.1f}%):** {CRF_val:.4f}")
    st.write(f"**Peso molecular del gas:** {MW_GAS:.2f} lb/lbmol")

# Pie de página
st.markdown("---")
st.markdown("<p style='text-align: center; color: #888;'>Proyecto Optimización de Procesos | Simulación de Gasoducto Trans‑Andino</p>", unsafe_allow_html=True)
