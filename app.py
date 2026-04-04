# app.py
# Gasoducto Trans-Andino - Versión Final Optimizada
# Cumple: Enunciado PDF, coherencia de unidades, perfil continuo y optimizador automático.

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# ------------------------------------------------------------
# CONFIGURACIÓN DE LA PÁGINA
# ------------------------------------------------------------
st.set_page_config(
    page_title="Gasoducto Trans-Andino",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------------------------------------------------
# ESTILO VISUAL (Dark Theme profesional)
# ------------------------------------------------------------
st.markdown("""
<style>
    .stApp { background-color: #0a0c10; }
    .main > div { flex-direction: row-reverse; }
    section[data-testid="stSidebar"] {
        order: 2; background-color: #14161c; border-left: 1px solid #2c3e50;
    }
    .stMarkdown, .stText, .stNumberInput label, .stSelectbox label, 
    .stSlider label, .stMetric label, .stMetric value { color: #ffffff !important; }
    .main-title {
        font-family: 'Arial Black', sans-serif; font-size: 2.8rem; text-align: center;
        color: #00aaff; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 0.2rem;
    }
    .subtitle { text-align: center; color: #cccccc; font-size: 1rem; margin-top: 0; }
    .metric-card {
        background-color: #1e1e2a; padding: 1rem; border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.6); text-align: center; border-top: 4px solid #00aaff;
    }
    h1, h2, h3 { color: #00aaff !important; font-weight: 600; }
    hr { border-color: #2c3e50; }
    .help-text { font-size: 0.75rem; color: #88aacc !important; margin-top: -8px; margin-bottom: 12px; font-style: italic; }
    .recommendation-box {
        background-color: #1a222a; border-left: 4px solid #ffaa00; padding: 1rem;
        border-radius: 8px; margin: 1rem 0; color: #ffffff;
    }
    .alert-success { color: #44cc44 !important; font-weight: bold; }
    .alert-error { color: #ff5555 !important; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------
# TÍTULO
# ------------------------------------------------------------
st.markdown('<div class="main-title">⚡ GASODUCTO TRANS-ANDINO ⚡</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Gemelo Digital | Optimización de Procesos | Semestre 3-2025</div>', unsafe_allow_html=True)
st.markdown("---")

# ------------------------------------------------------------
# 1. BASE DE DATOS TÉCNICA (Exacta al PDF)
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
# 2. PARÁMETROS FÍSICOS Y CONSTANTES (Unidades explícitas)
# ------------------------------------------------------------
L_TOTAL_KM = 400.0
P_RECEPCION = 800.0      # psia
P_MIN_ENTREGA = 500.0    # psia
T_SUC_C = 20.0
T_SUC_R = (T_SUC_C + 273.15) * 9/5  # Rankine
GAMMA = 0.65
Z = 0.90
K = 1.30
ETA_COMP = 0.85
HORAS_ANUALES = 8000
VIDA_PROYECTO = 20
R_UNIV = 1545.4          # ft·lbf/(lbmol·R)
P_BASE = 14.7            # psia
T_BASE_R = 520.0         # Rankine (60°F)
MW_AIRE = 28.97
MW_GAS = GAMMA * MW_AIRE
CONST_WEYMOUTH = 433.5   # Válida para: Q[MMscfd], L[mi], D[in], T[R], P[psia]
E_HID = 1.0

# ------------------------------------------------------------
# 3. FUNCIONES DE CÁLCULO
# ------------------------------------------------------------
def crf(tasa, n=VIDA_PROYECTO):
    """Factor de recuperación de capital. Retorna 1/n si tasa=0"""
    return 1.0 / n if tasa == 0 else tasa * (1 + tasa)**n / ((1 + tasa)**n - 1)

def maop_barlow(SMYS_psi, t_mm, D_ext_mm, F):
    """Presión máxima admisible (Barlow). Unidades: psi, mm -> in"""
    t_in = t_mm / 25.4
    D_in = D_ext_mm / 25.4
    return 2.0 * SMYS_psi * t_in * F / D_in

def caida_presion_weymouth(P1, Q, L_mi, D_in):
    """
    Calcula P2 con Weymouth. 
    Retorna None si físicamente imposible (P2^2 <= 0)
    """
    term = CONST_WEYMOUTH * (Q / E_HID)**2 * (L_mi * GAMMA * T_SUC_R * Z) / (D_in**5.33)
    P2_cuad = P1**2 - term
    return np.sqrt(P2_cuad) if P2_cuad > 0 else None

def potencia_compresor(Q, P_suc, P_desc, T_suc_R, Z_val, k, MW, eta):
    """
    Potencia requerida en HP. Fórmula termodinámica estándar:
    HP = (m_dot * H_p) / (550 * eta)
    """
    if P_suc <= 0: return 0.0
    r_p = P_desc / P_suc
    n = (k - 1) / k
    # Trabajo específico por unidad de masa (ft·lbf/lb)
    H_p = (Z_val * R_UNIV * T_suc_R / MW) * (1 / n) * (r_p**n - 1)
    # Flujo másico (lb/s)
    Q_scf_s = Q * 1e6 / (24 * 3600)
    rho_std = (P_BASE * 144 * MW) / (R_UNIV * T_BASE_R)
    m_dot = Q_scf_s * rho_std
    # Conversión ft·lbf/s -> HP
    return (m_dot * H_p) / (550 * eta)

def temp_descarga(T_suc_R, P_suc, P_desc, k):
    """Temperatura de descarga por compresión adiabática"""
    return T_suc_R * (P_desc / P_suc)**((k-1)/k)

# ------------------------------------------------------------
# 4. SIMULACIÓN CON PERFIL CONTINUO
# ------------------------------------------------------------
def simular_perfil_continuo(Q, D_in, N_est):
    """Genera perfil hidráulico continuo y calcula HP/T_max"""
    L_seg_mi = (L_TOTAL_KM * 0.621371) / (N_est + 1)
    L_seg_km = L_TOTAL_KM / (N_est + 1)
    distancias, presiones = [], []
    HP_total, T_max_C = 0.0, 0.0
    P_actual = P_RECEPCION
    puntos_por_tramo = 60  # Curva suave

    for i in range(N_est + 1):
        x_km = np.linspace(i * L_seg_km, (i + 1) * L_seg_km, puntos_por_tramo)
        x_mi = np.linspace(i * L_seg_mi, (i + 1) * L_seg_mi, puntos_por_tramo)
        
        # Weymouth inversa: P(x)^2 = P1^2 - term * L(x)
        term = CONST_WEYMOUTH * (Q / E_HID)**2 * (GAMMA * T_SUC_R * Z) / (D_in**5.33)
        P2_cuad = P_actual**2 - term * x_mi
        
        if np.any(P2_cuad <= 0):
            return None, None, None, None, None, False
            
        P_vals = np.sqrt(P2_cuad)
        distancias.extend(x_km)
        presiones.extend(P_vals)

        if i < N_est:
            P_fin = P_vals[-1]
            HP = potencia_compresor(Q, P_fin, P_RECEPCION, T_SUC_R, Z, K, MW_GAS, ETA_COMP)
            HP_total += HP
            T2_R = temp_descarga(T_SUC_R, P_fin, P_RECEPCION, K)
            T_max_C = max(T_max_C, (T2_R - 491.67) * 5/9)
            P_actual = P_RECEPCION

    return distancias, presiones, HP_total, T_max_C, presiones[-1], True

# ------------------------------------------------------------
# 5. BARRA LATERAL (Alineada 100% al PDF)
# ------------------------------------------------------------
with st.sidebar:
    st.markdown("## ⚙️ Parámetros de diseño")
    st.markdown("---")

    st.markdown("### 📊 Económicos")
    costo_energia = st.number_input("Costo de energía (USD/kWh)", 0.01, 0.50, 0.05, 0.01)
    st.markdown('<div class="help-text">Impacto directo en OPEX anual</div>', unsafe_allow_html=True)
    
    costo_acero_usd_m = st.number_input("Costo del acero (USD/m)", 100.0, 1000.0, 350.0, 10.0)
    st.markdown('<div class="help-text">Precio unitario de tubería. Influye en CAPEX del ducto</div>', unsafe_allow_html=True)
    
    tasa_interes = st.number_input("Tasa de interés (%)", 1.0, 20.0, 8.0) / 100.0
    st.markdown('<div class="help-text">Para cálculo del CRF (anualización)</div>', unsafe_allow_html=True)
    
    costo_comp_por_HP = st.number_input("Costo compresor (USD/HP)", 800, 2000, 1200, 100)
    st.markdown('<div class="help-text">Inversión en equipos de compresión</div>', unsafe_allow_html=True)

    st.markdown("### 🛠️ Materiales")
    diametro_sel = st.selectbox("Diámetro comercial", list(TUBERIAS.keys()))
    acero_sel = st.selectbox("Grado del acero", list(ACEROS.keys()))

    st.markdown("### 🌡️ Operación")
    Q_input = st.number_input("Flujo de gas Q (MMscfd)", 100.0, 1500.0, 500.0, 50.0)
    N_est = st.slider("Estaciones de compresión (N)", 0, 6, 2, 1)
    st.markdown('<div class="help-text">A mayor N, menor caída por tramo y menor HP/station</div>', unsafe_allow_html=True)

    if st.button("🔍 Optimizar Configuración (Mínimo TAC)", type="primary"):
        st.session_state.run_optimizer = True
    else:
        st.session_state.run_optimizer = False

# ------------------------------------------------------------
# 6. CÁLCULOS PRINCIPALES
# ------------------------------------------------------------
dat_tubo = TUBERIAS[diametro_sel]
dat_ac = ACEROS[acero_sel]
D_ext_mm = dat_tubo["D_ext_mm"]
t_mm = dat_tubo["t_mm"]
D_in = (D_ext_mm - 2*t_mm) / 25.4
MAOP = maop_barlow(dat_ac["SMYS_psi"], t_mm, D_ext_mm, dat_ac["F"])

# Simulación hidráulica
distancias, presiones, HP_total, T_max_C, P_final, factible = simular_perfil_continuo(Q_input, D_in, N_est)

if not factible:
    st.error("❌ Diseño inviable: La caída de presión por fricción supera la presión disponible. Aumente el diámetro o el número de estaciones.")
    st.stop()

# Cálculos económicos
costo_ducto = costo_acero_usd_m * (L_TOTAL_KM * 1000)
costo_compresores = HP_total * costo_comp_por_HP
CAPEX = costo_ducto + costo_compresores
CRF_val = crf(tasa_interes)
OPEX = HP_total * 0.7457 * HORAS_ANUALES * costo_energia
TAC = CAPEX * CRF_val + OPEX

# ------------------------------------------------------------
# OPTIMIZADOR AUTOMÁTICO (Cumple objetivo del PDF)
# ------------------------------------------------------------
if st.session_state.run_optimizer:
    best_tac = float('inf')
    best_config = {}
    for dn_key in TUBERIAS.keys():
        d_in_opt = (TUBERIAS[dn_key]["D_ext_mm"] - 2*TUBERIAS[dn_key]["t_mm"]) / 25.4
        for n_opt in range(0, 7):
            _, _, hp_o, t_o, pf_o, ok = simular_perfil_continuo(Q_input, d_in_opt, n_opt)
            if not ok or pf_o < P_MIN_ENTREGA or t_o > 65:
                continue
            cd = costo_acero_usd_m * L_TOTAL_KM * 1000
            cc = hp_o * costo_comp_por_HP
            tac_val = (cd + cc) * crf(tasa_interes) + hp_o * 0.7457 * HORAS_ANUALES * costo_energia
            if tac_val < best_tac:
                best_tac = tac_val
                best_config = {"D": dn_key, "N": n_opt, "TAC": tac_val, "HP": hp_o}
    
    if best_config:
        st.success(f"✅ Configuración Óptima: Diámetro **{best_config['D']}**, **N={best_config['N']}** estaciones")
        st.info(f"💰 TAC Mínimo: `${best_config['TAC']:,.0f}/año` | Potencia: `{best_config['HP']:,.0f} HP`")
        # Actualizar selección visualmente (opcional, requiere session_state más complejo)
    else:
        st.warning("No se encontró configuración factible con los parámetros económicos actuales.")

# ------------------------------------------------------------
# 7. VISUALIZACIÓN PRINCIPAL (Dashboard)
# ------------------------------------------------------------
st.markdown("## 📈 Resultados Clave")
c1, c2, c3 = st.columns(3)
with c1:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.metric("TAC (USD/año)", f"${TAC:,.0f}")
    st.markdown('</div>', unsafe_allow_html=True)
with c2:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.metric("Potencia Instalada", f"{HP_total:,.0f} HP")
    st.markdown('</div>', unsafe_allow_html=True)
with c3:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.metric("Presión Final", f"{P_final:.1f} psia")
    st.markdown('</div>', unsafe_allow_html=True)

# Perfil Hidráulico Continuo
st.markdown("## 📉 Perfil de Presión vs Distancia")
fig_p = go.Figure()
fig_p.add_trace(go.Scatter(x=distancias, y=presiones, mode='lines', name='Presión hidráulica', line=dict(color='#00aaff', width=3)))
fig_p.add_hline(y=P_MIN_ENTREGA, line_dash="dash", line_color="#ff5555", annotation_text="Mín Entrega (500 psia)")
fig_p.add_hline(y=MAOP, line_dash="dash", line_color="#ffaa00", annotation_text=f"MAOP ({MAOP:.0f} psia)")
fig_p.update_layout(xaxis_title="Distancia (km)", yaxis_title="Presión (psia)", template="plotly_dark", height=420, margin=dict(l=0,r=0,t=20,b=0), font=dict(color="#ffffff"))
st.plotly_chart(fig_p, use_container_width=True)

# Desglose de Costos
st.markdown("## 💰 Desglose del Costo Anualizado (TAC)")
df_cost = pd.DataFrame({
    "Concepto": ["CAPEX Tubería", "CAPEX Compresores", "OPEX Energía"],
    "Monto (USD/año)": [costo_ducto * CRF_val, costo_compresores * CRF_val, OPEX]
})
fig_c = px.bar(df_cost, x="Concepto", y="Monto (USD/año)", text="Monto (USD/año)", 
               color="Concepto", color_discrete_sequence=["#00aaff", "#ffaa00", "#44cc44"], title="")
fig_c.update_traces(texttemplate='$%{text:,.0f}', textposition='outside')
fig_c.update_layout(template="plotly_dark", height=380, font=dict(color="#ffffff"), paper_bgcolor="#0a0c10", plot_bgcolor="#0a0c10", yaxis=dict(title="USD/año"))
st.plotly_chart(fig_c, use_container_width=True)

# ------------------------------------------------------------
# 8. VALIDACIONES Y RECOMENDACIONES
# ------------------------------------------------------------
st.markdown("## ✅ Validaciones de Seguridad")
v1, v2 = st.columns(2)
with v1:
    if P_RECEPCION > MAOP:
        st.error(f"⛔ MAOP superado: {P_RECEPCION} > {MAOP:.0f} psia")
    else:
        st.success(f"✅ MAOK OK: {P_RECEPCION} ≤ {MAOP:.0f} psia")
    
    if T_max_C > 65:
        st.error(f"⛔ Temperatura excede límite: {T_max_C:.1f}°C > 65°C")
    else:
        st.success(f"✅ Temperatura OK: {T_max_C:.1f}°C ≤ 65°C")
with v2:
    if P_final < P_MIN_ENTREGA:
        st.error(f"⛔ Presión final insuficiente: {P_final:.1f} < {P_MIN_ENTREGA} psia")
    else:
        st.success(f"✅ Entrega OK: {P_final:.1f} ≥ {P_MIN_ENTREGA} psia")

# Recomendaciones dinámicas
recs = []
if P_final < P_MIN_ENTREGA:
    recs.append("🔹 Aumente el diámetro o el número de estaciones para reducir la caída por fricción.")
if T_max_C > 65:
    recs.append("🔹 Reduzca N estaciones por tramo o considere enfriamiento intermedio.")
if P_RECEPCION > MAOP:
    recs.append("🔹 Cambie a acero X60 o aumente espesor para elevar MAOP.")
if recs:
    st.markdown('<div class="recommendation-box"><strong>💡 Recomendaciones:</strong><br>' + "<br>".join(recs) + '</div>', unsafe_allow_html=True)

# Detalles técnicos
with st.expander("📐 Detalles Técnicos y Conversión de Unidades"):
    st.write(f"**Diámetro interno:** `{D_in:.3f} in` | **Espesor:** `{t_mm/25.4:.3f} in`")
    st.write(f"**MAOP (Barlow):** `{MAOP:.0f} psia` | **Peso molecular gas:** `{MW_GAS:.2f} lb/lbmol`")
    st.write(f"**Constante Weymouth:** `433.5` (Q: MMscfd, L: millas, D: pulgadas, T: °R, P: psia)")
    st.write(f"**Conversión potencia:** `1 HP = 0.7457 kW` | `1 psi = 144 lb/ft²`")
    st.write(f"**Fórmula CRF:** `i(1+i)^n / [(1+i)^n - 1]` | `n={VIDA_PROYECTO} años`")

st.markdown("---")
st.markdown("<p style='text-align:center; color:#666;'>Proyecto Optimización de Procesos | Gemelo Digital Gasoducto Trans-Andino | 2026</p>", unsafe_allow_html=True)
