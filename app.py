import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np

st.set_page_config(page_title="USDHKD 結構性產品分析", layout="wide")

# --- 新增：一鍵重置 / 清空設定功能 ---
if st.sidebar.button("🔄 一鍵重置 (恢復預設)", use_container_width=True):
    # 清空所有暫存的修改與記憶，並重新加載頁面
    st.session_state.clear()
    st.rerun()

# --- 初始化動態 Version 記憶 ---
if 'versions' not in st.session_state:
    st.session_state.versions = [
        {"id": 1, "name": "Version 1 (高槓桿型)", "pr": 7.0, "base": 0.0},
        {"id": 2, "name": "Version 2 (穩健保底型)", "pr": 2.65, "base": 0.02}
    ]
if 'version_counter' not in st.session_state:
    st.session_state.version_counter = 2

# --- 左側面板：自定義參數、門檻與版本 ---
st.sidebar.header("📝 基本信息設置")
issuer = st.sidebar.text_input("發行機構", value="華泰國際", key="issuer_input")
term_months = st.sidebar.number_input("產品期限 (個月)", value=12, min_value=1, step=1, key="term_input")
strike = st.sidebar.number_input("行使價 (Strike)", value=7.7500, format="%.4f", step=0.01, key="strike_input")
spot_fixing = st.sidebar.slider("模擬期末匯率 (Fixing)", min_value=7.7000, max_value=7.8600, value=7.8370, step=0.0010, format="%.4f", key="fixing_input")

st.sidebar.markdown("---")
st.sidebar.header("💰 投資入門門檻設置")
currency = st.sidebar.selectbox("計價幣別", ["USD", "HKD", "CNY", "EUR", "GBP"], index=0, key="curr_input")
threshold_amount = st.sidebar.number_input("輸入金額", value=1000000, step=100000, format="%d", key="amt_input")

st.sidebar.markdown("---")
st.sidebar.header("⚙️ 產品版本設置 (可動態增減)")

for i, v in enumerate(st.session_state.versions):
    with st.sidebar.expander(f"⚙️ 設置: {v['name']}", expanded=True):
        v['name'] = st.text_input(f"版本名稱", value=v['name'], key=f"name_{v['id']}")
        v['pr'] = st.number_input(f"參與率 (PR) %", value=v['pr']*100, step=10.0, key=f"pr_{v['id']}") / 100
        v['base'] = st.number_input(f"保底息 %", value=v['base']*100, step=1.0, key=f"base_{v['id']}") / 100

col1, col2 = st.sidebar.columns(2)
with col1:
    if st.button("➕ 新增版本"):
        st.session_state.version_counter += 1
        st.session_state.versions.append({
            "id": st.session_state.version_counter,
            "name": f"自定義版本 {st.session_state.version_counter}",
            "pr": 3.0, "base": 0.01
        })
        st.rerun()
with col2:
    if st.button("🗑️ 移除版本") and len(st.session_state.versions) > 1:
        st.session_state.versions.pop()
        st.rerun()

# --- 核心運算邏輯 (增加 7.8500 封頂機制) ---
def calc_return(fixing, base, pr, strike):
    effective_fixing = min(fixing, 7.8500)
    return 1 + base + pr * max(1 - strike/effective_fixing, 0)

# --- 主畫面：標題與即時看板 ---
st.title("📈 USDHKD 結構性產品：收益互動分析儀表板")
st.markdown(f"**發行機構**：{issuer} &nbsp;|&nbsp; **產品期限**：{term_months} 個月")

st.caption("*(註：以下預期年化回報區間基於香港聯繫匯率制在 7.7500 至 7.8500 之間不被打破之假設進行計算)*")
cols = st.columns(len(st.session_state.versions))
for col, v in zip(cols, st.session_state.versions):
    min_ret = calc_return(7.7500, v['base'], v['pr'], strike)
    max_ret = calc_return(7.8500, v['base'], v['pr'], strike)
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

# --- 新增：三色情境收益試算卡片 ---
st.markdown("### 💼 投資情境與絕對收益試算")
st.info(f"💡 以下絕對收益預估基於投資本金 **{currency} {threshold_amount:,.0f}** 進行計算：")

tabs = st.tabs([v['name'] for v in st.session_state.versions])

for i, tab in enumerate(tabs):
    v = st.session_state.versions[i]
    with tab:
        col_red, col_yellow, col_green = st.columns(3)
        
        bot_ret = calc_return(7.7500, v['base'], v['pr'], strike)
        bot_ann = (bot_ret - 1) * (12 / term_months)
        bot_amt = threshold_amount * bot_ret
        bot_profit = threshold_amount * (bot_ret - 1)
        
        with col_red:
            st.markdown(f"""
            <div style="background-color: #fce8e6; border-left: 5px solid #d93025; padding: 15px; border-radius: 5px; height: 100%;">
                <h4 style="color: #d93025; margin-top: 0;">🟥 觸底收益 (匯率不漲)</h4>
                <p style="margin: 5px 0; font-size: 14px;">期末匯率 ≤ {strike:.4f}</p>
                <h3 style="margin: 15px 0;">{currency} {bot_amt:,.0f}</h3>
                <p style="margin: 5px 0; color: #555;">淨利潤: <strong>{currency} {bot_profit:,.0f}</strong></p>
                <p style="margin: 5px 0; color: #555;">年化回報: <strong>{bot_ann:.2%}</strong></p>
            </div>
            """, unsafe_allow_html=True)
            
        top_ret = calc_return(7.8500, v['base'], v['pr'], strike)
        top_ann = (top_ret - 1) * (12 / term_months)
        
        with col_yellow:
            st.markdown(f"""
            <div style="background-color: #fef7e0; border-left: 5px solid #f9ab00; padding: 15px; border-radius: 5px; height: 100%;">
                <h4 style="color: #ea8600; margin-top: 0;">🟨 浮動增長區間</h4>
                <p style="margin: 5px 0; font-size: 14px;">{strike:.4f} < 匯率 < 7.8500</p>
                <h3 style="margin: 15px 0;">掛鉤匯率浮動</h3>
                <p style="margin: 5px 0; color: #555;">參與率放大: <strong>{v['pr']*100:.0f}%</strong></p>
                <p style="margin: 5px 0; color: #555;">年化區間: <strong>{bot_ann:.2%} ~ {top_ann:.2%}</strong></p>
            </div>
            """, unsafe_allow_html=True)

        top_amt = threshold_amount * top_ret
        top_profit = threshold_amount * (top_ret - 1)
        
        with col_green:
            st.markdown(f"""
            <div style="background-color: #e6f4ea; border-left: 5px solid #1e8e3e; padding: 15px; border-radius: 5px; height: 100%;">
                <h4 style="color: #1e8e3e; margin-top: 0;">🟩 觸頂封頂收益</h4>
                <p style="margin: 5px 0; font-size: 14px;">期末匯率 ≥ 7.8500</p>
                <h3 style="margin: 15px 0;">{currency} {top_amt:,.0f}</h3>
                <p style="margin: 5px 0; color: #555;">淨利潤: <strong>{currency} {top_profit:,.0f}</strong></p>
                <p style="margin: 5px 0; color: #555;">年化回報: <strong>{top_ann:.2%}</strong></p>
            </div>
            """, unsafe_allow_html=True)

st.markdown("---")

# --- Plotly 互動圖表 ---
rates = np.linspace(7.7000, 7.8600, 160)
fig = go.Figure()
colors = ['#0070C0', '#E26B0A', '#2CA02C', '#D62728', '#9467BD']

for i, v in enumerate(st.session_state.versions):
    curve = [calc_return(r, v['base'], v['pr'], strike) for r in rates]
    color = colors[i % len(colors)]
    fig.add_trace(go.Scatter(
        x=rates, y=curve, mode='lines', name=v['name'], 
        line=dict(color=color, width=3),
        hovertemplate="期末匯率: %{x:.4f}<br>總回報: %{y:.2%}<extra></extra>"
    ))
    
    floor_val = 1 + v['base']
    fig.add_annotation(x=7.7200, y=floor_val, text=f"底部保護 ({v['name']})", showarrow=False, font=dict(color=color, size=11), yshift=10)

fig.add_vline(x=7.8500, line_dash="dash", line_color="red")
fig.add_annotation(x=7.8500, y=1.08, text="弱方兌換保證 (7.8500上限)", textangle=-90, font=dict(color="red"))

fig.add_vline(x=spot_fixing, line_dash="dot", line_color="gray", annotation_text=f"模擬期末匯率: {spot_fixing:.4f}")

fig.update_layout(
    title='收益結構動態對比圖',
    xaxis_title='期末匯率 (Fixing Rate)', yaxis_title='到期總回報',
    xaxis_tickformat='.4f', yaxis_tickformat='.1%', 
    hovermode="x unified", template="plotly_white", height=450
)
st.plotly_chart(fig, use_container_width=True)

# --- 底部數據表格 ---
st.subheader("📊 主要匯率點收益試算表")
key_rates = np.linspace(7.7500, 7.8500, 11) 
table_data = {"預期期末匯率 (Fixing)": [f"{r:.4f}" for r in key_rates]}

for v in st.session_state.versions:
    ann_rets = []
    for r in key_rates:
        tr = calc_return(r, v['base'], v['pr'], strike)
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
