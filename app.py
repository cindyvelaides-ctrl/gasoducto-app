import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# ============================================================
# 1. CONFIGURACIÓN Y ESTILO
# ============================================================
st.set_page_config(page_title="Gasoducto Trans-Andino", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    .stApp { background-color: #0a0c10; }
    .main > div { flex-direction: row-reverse; }
    section[data-testid="stSidebar"] { order: 2; background-color: #14161c; border-left: 1px solid #2c3e50; }
    .stMarkdown, .stText, label, .stMetric label, .stMetric value { color: #ffffff !important; }
    .main-title { font-family: 'Arial Black', sans-serif; font-size: 2.6rem; text-align: center; color: #00aaff; text-transform: uppercase; margin-bottom: 0.2rem; }
    .subtitle { text-align: center; color: #aaaaaa; font-size: 1rem; margin-top: 0; }
    .metric-card { background-color: #1a1c24; padding: 1rem; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.5); text-align: center; border-top: 3px solid #00aaff; }
    .help-text { font-size: 0.75rem; color: #88aacc !important; margin-top: -6px; margin-bottom: 10px; font-style: italic; }
    .alert-box { padding: 0.8rem; border-radius: 6px; margin: 0.5rem 0; font-weight: bold; }
    .rec-box { background-color: #1a222a; border-left: 4px solid #ffaa00; padding: 1rem; border-radius: 6px; margin: 1rem 0; color: #fff; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">⚡ GASODUCTO TRANS-ANDINO ⚡</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Gemelo Digital | Simulación Hidráulica & Económica</div>', unsafe_allow_html=True)
st.markdown("---")

# ============================================================
# 2. CONSTANTES Y BASE DE DATOS (Exactas al PDF)
# ============================================================
L_TOTAL_KM = 400.0
P_RECEPCION = 800.0      # psia
P_MIN_ENTREGA = 500.0    # psia
T_SUC_C = 20.0
T_SUC_R = (T_SUC_C + 273.15) * 1.8  # Rankine
GAMMA = 0.65
Z = 0.90
K = 1.30
ETA_COMP = 0.85
HORAS_ANUALES = 8000
VIDA_PROYECTO = 20
R_UNIV = 1545.4          # ft·lbf/(lbmol·°R)
P_BASE = 14.7            # psia
T_BASE_R = 520.0         # °R
MW_AIRE = 28.97
MW_GAS = GAMMA * MW_AIRE
CONST_WEYMOUTH = 433.5   # Unidades: Q[MMscfd], L[mi], D[in], T[°R], P[psia]
E_HID = 1.0

TUBERIAS = {
    "12 pulgadas": {"D_ext_mm": 323.8, "t_mm": 10.31},
    "16 pulgadas": {"D_ext_mm": 406.4, "t_mm": 12.70},
    "20 pulgadas": {"D_ext_mm": 508.0, "t_mm": 15.09},
    "24 pulgadas": {"D_ext_mm": 609.6, "t_mm": 17.48}
}
ACEROS = {"X52": {"SMYS_psi": 52000, "F": 0.72}, "X60": {"SMYS_psi": 60000, "F": 0.72}}

# ============================================================
# 3. FUNCIONES DE CÁLCULO
# ============================================================
def crf(tasa, n=VIDA_PROYECTO):
    return 1.0/n if tasa == 0 else tasa*(1+tasa)**n / ((1+tasa)**n - 1)

def maop_barlow(SMYS, t_mm, D_ext_mm, F):
    return 2.0 * SMYS * (t_mm/25.4) * F / (D_ext_mm/25.4)

def potencia_compresor(Q, P_suc, P_desc, T1_R, Z_val, k, MW, eta):
    """Potencia requerida [HP] basada en flujo másico y trabajo adiabático"""
    if P_suc <= 0: return 0.0
    r_p = P_desc / P_suc
    # Densidad a condiciones estándar
    rho_std = (P_BASE * 144 * MW) / (R_UNIV * T_BASE_R)
    Q_scf_s = Q * 1e6 / (24 * 3600)
    m_dot = Q_scf_s * rho_std
    
    # Trabajo específico
    n_exp = (k - 1) / k
    H_p = (Z_val * R_UNIV * T1_R / MW) * (1 / n_exp) * (r_p**n_exp - 1)
    return (m_dot * H_p) / (550 * eta)

def temp_descarga(T1_R, P_suc, P_desc, k):
    return T1_R * (P_desc / P_suc)**((k-1)/k)

def simular_perfil_continuo(Q, D_in, N_est):
    """Genera perfil hidráulico PARABÓLICO por tramo y calcula HP/T_max"""
    L_total_mi = L_TOTAL_KM * 0.621371
    L_seg_mi = L_total_mi / (N_est + 1)
    L_seg_km = L_TOTAL_KM / (N_est + 1)
    
    distancias, presiones = [], []
    HP_total, T_max_C = 0.0, 0.0
    P_actual = P_RECEPCION
    pts = 50  # Resolución de la curva
    
    # Constante hidráulica independiente de la posición
    K_w = CONST_WEYMOUTH * (Q / E_HID)**2 * (GAMMA * T_SUC_R * Z) / (D_in**5.33)

    for i in range(N_est + 1):
        x_local_mi = np.linspace(0, L_seg_mi, pts)
        x_local_km = np.linspace(0, L_seg_km, pts)
        x_abs_km = i * L_seg_km + x_local_km
        
        P_cuad = P_actual**2 - K_w * x_local_mi
        if np.any(P_cuad <= 0):
            return None, None, None, None, None, False
            
        P_vals = np.sqrt(P_cuad)
        distancias.extend(x_abs_km)
        presiones.extend(P_vals)

        if i < N_est:
            P_fin = P_vals[-1]
            HP_total += potencia_compresor(Q, P_fin, P_RECEPCION, T_SUC_R, Z, K, MW_GAS, ETA_COMP)
            T_max_C = max(T_max_C, (temp_descarga(T_SUC_R, P_fin, P_RECEPCION, K) - 491.67)*5/9)
            P_actual = P_RECEPCION

    return distancias, presiones, HP_total, T_max_C, presiones[-1], True

def optimizar_configuracion(Q, costo_acero, tasa, costo_hp):
    """Búsqueda exhaustiva de la configuración de mínimo TAC"""
    best = {"TAC": float('inf'), "D": None, "N": None}
    for dn, data in TUBERIAS.items():
        d_in = (data["D_ext_mm"] - 2*data["t_mm"]) / 25.4
        for n in range(0, 7):
            _, _, hp, t_max, p_fin, ok = simular_perfil_continuo(Q, d_in, n)
            if not ok or p_fin < P_MIN_ENTREGA or t_max > 65:
                continue
            ca = costo_acero * L_TOTAL_KM * 1000
            cc = hp * costo_hp
            tac = (ca + cc) * crf(tasa) + hp * 0.7457 * HORAS_ANUALES * st.session_state.energia_cost
            if tac < best["TAC"]:
                best = {"TAC": tac, "D": dn, "N": n, "HP": hp, "P_fin": p_fin}
    return best if best["D"] is not None else None

# ============================================================
# 4. INTERFAZ: SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown("## ⚙️ Configuración")
    st.markdown("---")
    st.markdown("### 💰 Económicos")
    st.session_state.energia_cost = st.number_input("Costo de energía (USD/kWh)", 0.01, 0.50, 0.05, 0.01)
    st.markdown('<div class="help-text">Afecta directamente el OPEX anual</div>', unsafe_allow_html=True)
    costo_acero = st.number_input("Costo del acero (USD/m)", 100.0, 1000.0, 350.0, 10.0)
    st.markdown('<div class="help-text">Precio unitario de tubería instalada</div>', unsafe_allow_html=True)
    tasa = st.number_input("Tasa de interés (%)", 1.0, 20.0, 8.0) / 100.0
    costo_hp = st.number_input("Costo compresor (USD/HP)", 800, 2000, 1200, 100)

    st.markdown("### 🛠️ Materiales")
    diametro_sel = st.selectbox("Diámetro comercial", list(TUBERIAS.keys()))
    acero_sel = st.selectbox("Grado del acero", list(ACEROS.keys()))

    st.markdown("### 🌡️ Operación")
    Q = st.number_input("Flujo de gas Q (MMscfd)", 100.0, 1500.0, 500.0, 50.0)
    N = st.slider("Estaciones de compresión (N)", 0, 6, 2, 1)
    st.markdown('<div class="help-text">Más estaciones = menor HP por compresor</div>', unsafe_allow_html=True)

    if st.button("🔍 Encontrar Configuración Óptima", type="primary"):
        st.session_state.run_opt = True
    else:
        st.session_state.run_opt = False

# ============================================================
# 5. CÁLCULOS PRINCIPALES
# ============================================================
d_ext = TUBERIAS[diametro_sel]["D_ext_mm"]
t_wall = TUBERIAS[diametro_sel]["t_mm"]
D_in = (d_ext - 2*t_wall) / 25.4
SMYS = ACEROS[acero_sel]["SMYS_psi"]
F = ACEROS[acero_sel]["F"]
MAOP = maop_barlow(SMYS, t_wall, d_ext, F)

dist, pres, HP, T_max, P_final, factible = simular_perfil_continuo(Q, D_in, N)

if not factible:
    st.error("🚫 Diseño inviable: La caída de presión excede la capacidad del tramo. Aumente D o N.")
    st.stop()

# Cálculo económico
costo_ducto = costo_acero * L_TOTAL_KM * 1000
costo_comp = HP * costo_hp
CAPEX = costo_ducto + costo_comp
OPEX = HP * 0.7457 * HORAS_ANUALES * st.session_state.energia_cost
TAC = CAPEX * crf(tasa) + OPEX

# Optimizador
opt_res = None
if st.session_state.get("run_opt", False):
    with st.spinner("Evaluando 28 combinaciones factibles..."):
        opt_res = optimizar_configuracion(Q, costo_acero, tasa, costo_hp)
    st.session_state.run_opt = False

# ============================================================
# 6. INTERFAZ: PANEL PRINCIPAL
# ============================================================
st.markdown("## 📊 Métricas Clave")
c1, c2, c3 = st.columns(3)
with c1:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.metric("TAC Total", f"${TAC:,.0f} /año")
    st.markdown('</div>', unsafe_allow_html=True)
with c2:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.metric("Potencia Instalada", f"{HP:,.0f} HP")
    st.markdown('</div>', unsafe_allow_html=True)
with c3:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.metric("Presión de Entrega", f"{P_final:.1f} psia")
    st.markdown('</div>', unsafe_allow_html=True)

if opt_res:
    st.success(f"✅ **Óptimo encontrado:** {opt_res['D']} | N={opt_res['N']} | TAC=${opt_res['TAC']:,.0f}")

# Perfil Hidráulico
st.markdown("## 📉 Perfil de Presión vs Distancia")
fig = go.Figure()
fig.add_trace(go.Scatter(x=dist, y=pres, mode='lines', name='Presión hidráulica', line=dict(color='#00aaff', width=3, shape='spline')))
fig.add_hline(y=P_MIN_ENTREGA, line_dash="dash", line_color="#ff5555", annotation_text="Mín. Entrega (500 psia)")
fig.add_hline(y=MAOP, line_dash="dot", line_color="#ffaa00", annotation_text=f"MAOP ({MAOP:.0f} psia)")
fig.update_layout(xaxis_title="Distancia (km)", yaxis_title="Presión (psia)", template="plotly_dark", height=400, margin=dict(l=0,r=0,t=20,b=0), font=dict(color="#fff"))
st.plotly_chart(fig, use_container_width=True)

# Desglose de Costos
st.markdown("## 💰 Desglose del Costo Anualizado")
df_c = pd.DataFrame({
    "Concepto": ["CAPEX Tubería", "CAPEX Compresores", "OPEX Energía"],
    "USD/año": [costo_ducto*crf(tasa), costo_comp*crf(tasa), OPEX]
})
fig_c = px.bar(df_c, x="Concepto", y="USD/año", text="USD/año", color="Concepto", color_discrete_sequence=["#00aaff", "#ffaa00", "#44cc44"])
fig_c.update_traces(texttemplate='$%{text:,.0f}', textposition='outside')
fig_c.update_layout(template="plotly_dark", height=350, font=dict(color="#fff"), paper_bgcolor="#0a0c10", plot_bgcolor="#0a0c10", showlegend=False, yaxis_title="USD/año")
st.plotly_chart(fig_c, use_container_width=True)

# Validaciones
st.markdown("## ✅ Sistema de Validación y Alertas")
v1, v2 = st.columns(2)
with v1:
    if P_RECEPCION > MAOP:
        st.markdown('<div class="alert-box" style="background:#331111; color:#ff6666;">🚫 MAOP superado</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="alert-box" style="background:#113311; color:#66ff66;">✅ MAOK OK: {:.0f} psia ≤ {:.0f} psia</div>'.format(P_RECEPCION, MAOP), unsafe_allow_html=True)
    if T_max > 65:
        st.markdown('<div class="alert-box" style="background:#331111; color:#ff6666;">🌡️ Temperatura alta: {:.1f}°C > 65°C</div>'.format(T_max), unsafe_allow_html=True)
    else:
        st.markdown('<div class="alert-box" style="background:#113311; color:#66ff66;">✅ Temp OK: {:.1f}°C ≤ 65°C</div>'.format(T_max), unsafe_allow_html=True)
with v2:
    if P_final < P_MIN_ENTREGA:
        st.markdown('<div class="alert-box" style="background:#331111; color:#ff6666;">⚠️ Presión insuficiente: {:.1f} < 500 psia</div>'.format(P_final), unsafe_allow_html=True)
    else:
        st.markdown('<div class="alert-box" style="background:#113311; color:#66ff66;">✅ Entrega OK: {:.1f} ≥ 500 psia</div>'.format(P_final), unsafe_allow_html=True)

# Recomendaciones dinámicas
recs = []
if P_final < P_MIN_ENTREGA: recs.append("Aumente el diámetro o el número de estaciones para reducir la caída por fricción.")
if T_max > 65: recs.append("Reduzca la relación de compresión por tramo o considere enfriamiento intermedio.")
if P_RECEPCION > MAOP: recs.append("Cambie a acero X60 o aumente el espesor para elevar el MAOP.")
if recs:
    st.markdown('<div class="rec-box"><strong>💡 Recomendaciones:</strong><br>• ' + '<br>• '.join(recs) + '</div>', unsafe_allow_html=True)

# Detalles
with st.expander("📐 Detalles Técnicos y Unidades"):
    st.write(f"**Diámetro interno:** `{D_in:.3f} in` | **Espesor:** `{t_wall/25.4:.3f} in`")
    st.write(f"**MAOP (Barlow):** `{MAOP:.0f} psia` | **Peso molecular gas:** `{MW_GAS:.2f} lb/lbmol`")
    st.write(f"**Ecuación Weymouth:** `433.5` (Q:MMscfd, L:mi, D:in, T:°R, P:psia)")
    st.write(f"**Conversión potencia:** `1 HP = 0.7457 kW` | `R = 1545.4 ft·lbf/lbmol·°R`")
    st.write(f"**CRF:** `i(1+i)^n / [(1+i)^n - 1]` | `n={VIDA_PROYECTO} años`")

st.markdown("---")
st.markdown("<p style='text-align:center; color:#555;'>Proyecto Optimización de Procesos | Gasoducto Trans-Andino | 2026</p>", unsafe_allow_html=True)
