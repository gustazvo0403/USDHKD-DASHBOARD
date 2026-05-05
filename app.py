import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np

st.set_page_config(page_title="USDHKD 結構性產品分析", layout="wide")

# --- 狀態初始化 ---
if 'initialized' not in st.session_state:
    st.session_state.issuer_input = "華泰國際"
    st.session_state.term_input = 12
    st.session_state.strike_input = 7.7500
    st.session_state.fixing_input = 7.8370
    st.session_state.curr_input = "USD"
    st.session_state.amt_input = 1000000
    
    st.session_state.versions = [1, 2]
    st.session_state.name_1 = "Version 1 (高槓桿型)"
    st.session_state.pr_1 = 700.0
    st.session_state.base_1 = 0.0
    st.session_state.name_2 = "Version 2 (穩健保底型)"
    st.session_state.pr_2 = 265.0
    st.session_state.base_2 = 2.0
    
    st.session_state.version_counter = 2
    st.session_state.initialized = True

# --- 一鍵重置 / 徹底清空邏輯 ---
def reset_all():
    st.session_state.issuer_input = None
    st.session_state.term_input = None
    st.session_state.strike_input = None
    st.session_state.amt_input = None
    st.session_state.curr_input = None
    st.session_state.fixing_input = 7.8370 
    
    keys_to_del = [k for k in st.session_state.keys() if k.startswith("name_") or k.startswith("pr_") or k.startswith("base_")]
    for k in keys_to_del:
        del st.session_state[k]
    
    st.session_state.versions = [1]
    st.session_state.name_1 = None
    st.session_state.pr_1 = None
    st.session_state.base_1 = None
    st.session_state.version_counter = 1

if st.sidebar.button("🔄 一鍵重置 (徹底清空)", on_click=reset_all, use_container_width=True):
    pass

# --- 左側面板：自定義參數、門檻與版本 ---
st.sidebar.header("📝 基本信息設置")
st.sidebar.text_input("發行機構", key="issuer_input", placeholder="例如: 華泰國際")
st.sidebar.number_input("產品期限 (個月)", step=1, key="term_input", placeholder="例如: 12")
st.sidebar.number_input("行使價 (Strike)", format="%.4f", step=0.01, key="strike_input", placeholder="例如: 7.7500")
st.sidebar.slider("模擬期末匯率 (Fixing)", min_value=7.7400, max_value=7.8600, step=0.0010, format="%.4f", key="fixing_input")

st.sidebar.markdown("---")
st.sidebar.header("💰 投資入門門檻設置")
st.sidebar.selectbox("計價幣別", ["USD", "HKD", "CNY", "EUR", "GBP"], index=None, placeholder="選擇幣別", key="curr_input")
st.sidebar.number_input("輸入金額", step=100000, key="amt_input", placeholder="例如: 1000000")

st.sidebar.markdown("---")
st.sidebar.header("⚙️ 產品版本設置 (可動態增減)")

for vid in st.session_state.versions:
    name_key = f"name_{vid}"
    pr_key = f"pr_{vid}"
    base_key = f"base_{vid}"
    
    v_name = st.session_state.get(name_key)
    expander_title = f"⚙️ 設置: {v_name}" if v_name else f"⚙️ 設置: 尚未命名"
    
    with st.sidebar.expander(expander_title, expanded=True):
        st.text_input("版本名稱", key=name_key, placeholder="例如: Version 1")
        st.number_input("參與率 (PR) %", step=10.0, key=pr_key, placeholder="例如: 700.0")
        st.number_input("保底息 % (年化)", step=1.0, key=base_key, placeholder="例如: 2.0")

col1, col2 = st.sidebar.columns(2)
with col1:
    if st.button("➕ 新增版本"):
        st.session_state.version_counter += 1
        new_id = st.session_state.version_counter
        st.session_state.versions.append(new_id)
        st.session_state[f"name_{new_id}"] = None
        st.session_state[f"pr_{new_id}"] = None
        st.session_state[f"base_{new_id}"] = None
        st.rerun()
with col2:
    if st.button("🗑️ 移除版本") and len(st.session_state.versions) > 1:
        vid_to_remove = st.session_state.versions.pop()
        st.rerun()

# --- 防止因空值計算崩潰的保護邏輯 ---
issuer = st.session_state.issuer_input if st.session_state.issuer_input else "未指定機構"
term_months = st.session_state.term_input if st.session_state.term_input else 12
strike = st.session_state.strike_input if st.session_state.strike_input else 7.7500
spot_fixing = st.session_state.fixing_input
currency = st.session_state.curr_input if st.session_state.curr_input else "USD"
threshold_amount = st.session_state.amt_input if st.session_state.amt_input else 0

active_versions = []
for vid in st.session_state.versions:
    n = st.session_state.get(f"name_{vid}")
    p = st.session_state.get(f"pr_{vid}")
    b = st.session_state.get(f"base_{vid}")
    
    active_versions.append({
        "name": n if n else f"自定義版本 {vid}",
        "pr": (p / 100.0) if p is not None else 0.0,
        "base": (b / 100.0) if b is not None else 0.0
    })

# --- 核心運算邏輯 (修正：引入產品期限將保底息年化轉為期間絕對息) ---
def calc_return(fixing, base_annual, pr, strike, t_months):
    effective_fixing = min(fixing, 7.8500)
    # 期間保底息 = 年化保底息 * (期限/12)
    period_base = base_annual * (t_months / 12.0)
    return 1 + period_base + pr * max(1 - strike/effective_fixing, 0)

# --- 主畫面：標題與即時看板 ---
st.title("📈 USD/HKD聯匯結構性產品投資收益模擬器")
st.markdown(f"**發行機構**：{issuer} &nbsp;|&nbsp; **產品期限**：{term_months} 個月")

st.caption("*(註：以下預期年化回報區間基於香港聯繫匯率制在 7.7500 至 7.8500 之間不被打破之假設進行計算)*")
cols = st.columns(len(active_versions))
for col, v in zip(cols, active_versions):
    min_ret = calc_return(7.7500, v['base'], v['pr'], strike, term_months)
    max_ret = calc_return(7.8500, v['base'], v['pr'], strike, term_months)
    min_ann = (min_ret - 1) * (12 / term_months)
    max_ann = (max_ret - 1) * (12 / term_months)
    
    custom_metric_card = f"""
    <div style="border: 1px solid #e6e6e6; border-radius: 8px; padding: 20px; background-color: #ffffff; box-shadow: 0 2px 4px rgba(0,0,0,0.02);">
        <p style="font-size: 14px; color: #666; margin: 0 0 5px 0;">{v['name']}</p>
        <p style="font-size: 32px; font-weight: bold; color: #111; margin: 0 0 12px 0;">參與率 (PR): {v['pr']*100:.0f}%</p>
        <div style="background-color: #e6f4ea; color: #137333; padding: 6px 12px; border-radius: 4px; display: inline-block; font-size: 15px; font-weight: 600;">
            📈 年化區間: {min_ann:.2%} ~ {max_ann:.2%}
        </div>
    </div>
    """
    col.markdown(custom_metric_card, unsafe_allow_html=True)

st.write("") 

# --- 三色情境收益試算卡片 ---
st.markdown("### 💼 投資情境與絕對收益試算")
st.info(f"💡 以下絕對收益預估基於投資本金 **{currency} {threshold_amount:,.0f}** 進行計算：")

tabs = st.tabs([v['name'] for v in active_versions])

for i, tab in enumerate(tabs):
    v = active_versions[i]
    with tab:
        col_red, col_yellow, col_green = st.columns(3)
        
        bot_ret = calc_return(7.7500, v['base'], v['pr'], strike, term_months)
        bot_ann = (bot_ret - 1) * (12 / term_months)
        bot_amt = threshold_amount * bot_ret
        bot_profit = threshold_amount * (bot_ret - 1)
        
        with col_red:
            st.markdown(f"""
            <div style="background-color: #fce8e6; border-left: 5px solid #d93025; padding: 15px; border-radius: 5px; height: 100%;">
                <h4 style="color: #d93025; margin-top: 0;">🟥 觸底收益</h4>
                <p style="margin: 5px 0; font-size: 14px;">期末匯率 ≤ {strike:.4f}</p>
                <h3 style="margin: 15px 0;">{currency} {bot_amt:,.0f}</h3>
                <p style="margin: 5px 0; color: #555;">淨利潤: <strong>{currency} {bot_profit:,.0f}</strong></p>
                <p style="margin: 5px 0; color: #555;">年化回報: <strong>{bot_ann:.2%}</strong></p>
            </div>
            """, unsafe_allow_html=True)
            
        sim_ret = calc_return(spot_fixing, v['base'], v['pr'], strike, term_months)
        sim_ann = (sim_ret - 1) * (12 / term_months)
        sim_amt = threshold_amount * sim_ret
        sim_profit = threshold_amount * (sim_ret - 1)
        
        with col_yellow:
            st.markdown(f"""
            <div style="background-color: #fef7e0; border-left: 5px solid #f9ab00; padding: 15px; border-radius: 5px; height: 100%;">
                <h4 style="color: #ea8600; margin-top: 0;">🟨 浮動收益</h4>
                <p style="margin: 5px 0; font-size: 14px;">模擬匯率 = {spot_fixing:.4f}</p>
                <h3 style="margin: 15px 0;">{currency} {sim_amt:,.0f}</h3>
                <p style="margin: 5px 0; color: #555;">淨利潤: <strong>{currency} {sim_profit:,.0f}</strong></p>
                <p style="margin: 5px 0; color: #555;">年化回報: <strong>{sim_ann:.2%}</strong></p>
            </div>
            """, unsafe_allow_html=True)

        top_ret = calc_return(7.8500, v['base'], v['pr'], strike, term_months)
        top_ann = (top_ret - 1) * (12 / term_months)
        top_amt = threshold_amount * top_ret
        top_profit = threshold_amount * (top_ret - 1)
        
        with col_green:
            st.markdown(f"""
            <div style="background-color: #e6f4ea; border-left: 5px solid #1e8e3e; padding: 15px; border-radius: 5px; height: 100%;">
                <h4 style="color: #1e8e3e; margin-top: 0;">🟩 封頂收益</h4>
                <p style="margin: 5px 0; font-size: 14px;">期末匯率 ≥ 7.8500</p>
                <h3 style="margin: 15px 0;">{currency} {top_amt:,.0f}</h3>
                <p style="margin: 5px 0; color: #555;">淨利潤: <strong>{currency} {top_profit:,.0f}</strong></p>
                <p style="margin: 5px 0; color: #555;">年化回報: <strong>{top_ann:.2%}</strong></p>
            </div>
            """, unsafe_allow_html=True)

# --- 新增：底層計算公式區塊 ---
st.markdown("""
<div style="background-color: #f8f9fa; padding: 15px 20px; border-radius: 8px; border-left: 4px solid #1f4e78; margin-top: 20px; margin-bottom: 20px;">
    <p style="margin: 0 0 8px 0; font-size: 15px; font-weight: 600; color: #1f4e78;">📐 產品到期贖回公式 (Redemption at Maturity)：</p>
    <p style="margin: 0; font-family: monospace; font-size: 14px; color: #333;">
        <b>到期總回報</b> = 100% (本金) + (年化保底息 × 產品期限/12) + 參與率(PR) × Max( 1 - 行使價 / USDHKD期末匯率 , 0 )
    </p>
</div>
""", unsafe_allow_html=True)


# --- Plotly 互動圖表 ---
rates = np.linspace(7.7400, 7.8600, 160)
fig = go.Figure()
colors = ['#0070C0', '#E26B0A', '#2CA02C', '#D62728', '#9467BD']

for i, v in enumerate(active_versions):
    curve = [calc_return(r, v['base'], v['pr'], strike, term_months) for r in rates]
    color = colors[i % len(colors)]
    fig.add_trace(go.Scatter(
        x=rates, y=curve, mode='lines', name=v['name'], 
        line=dict(color=color, width=3),
        hovertemplate="期末匯率: %{x:.4f}<br>總回報: %{y:.2%}<extra></extra>"
    ))
    
    # 底部保護線現在也將時間權重納入計算
    floor_val = 1 + v['base'] * (term_months / 12.0)
    fig.add_annotation(x=7.7450, y=floor_val, text=f"底部保護 ({v['name']})", showarrow=False, font=dict(color=color, size=11), yshift=10)

fig.add_vline(x=7.8500, line_dash="dash", line_color="red")
fig.add_annotation(x=7.8500, y=1.08, text="弱方兌換保證 (7.8500上限)", textangle=-90, font=dict(color="red"))

fig.add_vline(x=spot_fixing, line_dash="dot", line_color="gray", annotation_text=f"模擬期末匯率: {spot_fixing:.4f}")

fig.update_layout(
    title='收益結構動態對比圖',
    xaxis_title='期末匯率 (Fixing Rate)', yaxis_title='到期總回報',
    xaxis_tickformat='.4f', yaxis_tickformat='.1%', 
    xaxis_range=[7.7400, 7.8600], 
    hovermode="x unified", template="plotly_white", height=450
)
st.plotly_chart(fig, use_container_width=True)

# --- 底部數據表格 ---
st.subheader("📊 主要匯率點收益試算表")
key_rates = np.linspace(7.7500, 7.8500, 11) 
table_data = {"預期期末匯率 (Fixing)": [f"{r:.4f}" for r in key_rates]}

for v in active_versions:
    ann_rets = []
    for r in key_rates:
        tr = calc_return(r, v['base'], v['pr'], strike, term_months)
        ar = (tr - 1) * (12 / term_months)
        ann_rets.append(f"{ar:.2%}")
    table_data[f"{v['name']} (預期年化回報)"] = ann_rets

df = pd.DataFrame(table_data)
st.dataframe(df, use_container_width=True)

# --- 頁尾合規提示聲明 ---
st.markdown("---")
st.markdown("""
<div style="color: #666; font-size: 0.85em; line-height: 1.6;">
<b>【重要提示】</b>：<br>
本產品非存款產品，不納入銀行存款保障範疇。本内容所載資料僅供參考之用，文件內任何資訊及分析並不構成對投資產品未來表現的任何保證。本文件所收錄之任何資訊、預測或意見的準確性、正確性或完整性並不保證，亦不會對因依賴有關資訊、預測或意見而引致的損失負任何責任。投資涉及風險，並受市場波動及投資風險所影響。如對本文內容的含意或所引致的影響有任何疑問，請徵詢獨立專業人士的意見。
</div>
""", unsafe_allow_html=True)
