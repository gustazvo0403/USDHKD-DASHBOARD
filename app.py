import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np

st.set_page_config(page_title="USDHKD 結構性產品分析", layout="wide")

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
issuer = st.sidebar.text_input("發行機構", value="華泰國際")
term_months = st.sidebar.number_input("產品期限 (個月)", value=12, min_value=1, step=1)
strike = st.sidebar.number_input("行使價 (Strike)", value=7.7500, format="%.4f", step=0.01)
spot_fixing = st.sidebar.slider("模擬期末匯率 (Fixing)", min_value=7.7000, max_value=7.8600, value=7.8370, step=0.0010, format="%.4f")

# 將門檻設置移動到左側
st.sidebar.markdown("---")
st.sidebar.header("💰 投資入門門檻設置")
currency = st.sidebar.selectbox("計價幣別", ["USD", "HKD", "CNY", "EUR", "GBP"], index=0)
threshold_amount = st.sidebar.number_input("輸入金額", value=1000000, step=100000, format="%d")

st.sidebar.markdown("---")
st.sidebar.header("⚙️ 產品版本設置 (可動態增減)")

# 渲染動態版本設定區
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

# --- 主畫面：標題與即時看板 ---
st.title("📈 USDHKD 結構性產品：收益互動分析儀表板")
st.markdown(f"**發行機構**：{issuer} &nbsp;|&nbsp; **產品期限**：{term_months} 個月")

def calc_return(fixing, base, pr, strike):
    return 1 + base + pr * max(1 - strike/fixing, 0)

# 動態生成頂部指標卡片 (客製化 HTML 渲染淺綠色底色)
st.caption("*(註：以下預期年化回報區間基於香港聯繫匯率制在 7.7500 至 7.8500 之間不被打破之假設進行計算)*")
cols = st.columns(len(st.session_state.versions))
for col, v in zip(cols, st.session_state.versions):
    # 計算 7.75 到 7.85 的年化回報極值
    min_ret = calc_return(7.75, v['base'], v['pr'], strike)
    max_ret = calc_return(7.85, v['base'], v['pr'], strike)
    min_ann = (min_ret - 1) * (12 / term_months)
    max_ann = (max_ret - 1) * (12 / term_months)
    
    # 撰寫專屬的 HTML 卡片樣式
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

# 保留門檻提示於圖表上方
st.info(f"💡 本產品最低起投金額為：**{currency} {threshold_amount:,.0f}**")

# --- Plotly 互動圖表 ---
rates = np.linspace(7.70, 7.86, 160)
fig = go.Figure()
colors = ['#0070C0', '#E26B0A', '#2CA02C', '#D62728', '#9467BD']

for i, v in enumerate(st.session_state.versions):
    curve = [calc_return(r, v['base'], v['pr'], strike) for r in rates]
    color = colors[i % len(colors)]
    fig.add_trace(go.Scatter(x=rates, y=curve, mode='lines', name=v['name'], line=dict(color=color, width=3)))
    
    # 標註保底線 (Floor)
    floor_val = 1 + v['base']
    fig.add_annotation(x=7.72, y=floor_val, text=f"底部保護 ({v['name']})", showarrow=False, font=dict(color=color, size=11), yshift=10)

# 標註香港聯繫匯率天花板 (7.85)
fig.add_vline(x=7.85, line_dash="dash", line_color="red")
fig.add_annotation(x=7.85, y=1.08, text="弱方兌換保證 (7.85上限)", textangle=-90, font=dict(color="red"))

# 當前選擇匯率線
fig.add_vline(x=spot_fixing, line_dash="dot", line_color="gray", annotation_text=f"模擬期末匯率: {spot_fixing:.4f}")

fig.update_layout(
    title='收益結構動態對比圖',
    xaxis_title='期末匯率 (Fixing Rate)', yaxis_title='到期總回報',
    yaxis_tickformat='.1%', hovermode="x unified", template="plotly_white", height=450
)
st.plotly_chart(fig, use_container_width=True)

# --- 底部數據表格：等距匯率點與年化回報 ---
st.subheader("📊 主要匯率點收益試算表")
# 生成從 7.75 到 7.85，間隔 0.01 的均勻檔位 (共 11 個檔位)
key_rates = np.linspace(7.75, 7.85, 11) 
table_data = {"預期期末匯率 (Fixing)": [f"{r:.4f}" for r in key_rates]}

for v in st.session_state.versions:
    ann_rets = []
    for r in key_rates:
        tr = calc_return(r, v['base'], v['pr'], strike)
        ar = (tr - 1) * (12 / term_months)
        ann_rets.append(f"{ar:.2%}")
    # 表格僅保留年化回報
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
