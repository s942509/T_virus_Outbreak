import streamlit as st
import pandas as pd
import plotly.express as px
import streamlit.components.v1 as components
import json

# 1. 頁面配置
st.set_page_config(page_title="T-Virus Global Surveillance", layout="wide")

# 2. 注入 Aurora 背景與全域樣式 (CSS)
st.markdown("""
<style>
    .stApp { background: #020617 !important; }
    .stMain, .block-container { background: transparent !important; padding-top: 2rem !important; }
    
    /* 自定義 KPI 卡片樣式 */
    .kpi-box {
        background: rgba(15, 23, 42, 0.6);
        border: 1px solid rgba(0, 212, 255, 0.3);
        border-radius: 10px;
        padding: 15px;
        text-align: center;
        margin-bottom: 10px;
        backdrop-filter: blur(10px);
    }
    .kpi-value { font-size: 24px; font-weight: bold; color: #ff4d4d; }
    .kpi-label { font-size: 14px; color: #94a3b8; }
</style>
""", unsafe_allow_html=True)

# 3. 讀取數據 (假設檔名為 t_virus_global_outbreak_30k.csv)
@st.cache_data
def load_data():
    df = pd.read_csv('t_virus_global_outbreak_30k.csv')
    df['date'] = pd.to_datetime(df['date'])
    df['month_year'] = df['date'].dt.to_period('M').astype(str)
    return df

try:
    df = load_data()
except FileNotFoundError:
    st.error("找不到數據檔，請確保 t_virus_global_outbreak_30k.csv 位於同一目錄。")
    st.stop()

# --- 側邊欄控制與時間軸 ---
st.sidebar.title("☣️ 生化危機監控中心")
all_months = sorted(df['month_year'].unique())
selected_month = st.sidebar.select_slider("選擇時間線 (月)", options=all_months)

# 過濾當月數據
mask = df['month_year'] == selected_month
filtered_df = df[mask]

# --- 佈局設計：左 (KPI) | 中 (地球) | 右 (分析圖) ---
col1, col2, col3 = st.columns([1, 2, 1])

with col1:
    st.subheader("📊 關鍵 KPI")
    total_inf = filtered_df['infected'].sum()
    total_zom = filtered_df['zombified'].sum()
    avg_mut = (filtered_df['mutants'].sum() / filtered_df['infected'].sum() * 100) if total_inf > 0 else 0
    
    st.markdown(f'<div class="kpi-box"><div class="kpi-value">{total_inf:,}</div><div class="kpi-label">當月總感染</div></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="kpi-box"><div class="kpi-value">{total_zom:,}</div><div class="kpi-label">當月殭屍化</div></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="kpi-box"><div class="kpi-value">{avg_mut:.2f}%</div><div class="kpi-label">病毒突變率</div></div>', unsafe_allow_html=True)
    
    st.subheader("🛡️ 武裝部隊部署")
    fig_ut = px.bar(filtered_df.groupby('country')['ut_forces'].sum().reset_index().nlargest(5, 'ut_forces'), 
                   x='ut_forces', y='country', orientation='h', 
                   template="plotly_dark", color_discrete_sequence=['#deff9a'])
    fig_ut.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=300)
    st.plotly_chart(fig_ut, use_container_width=True)

with col2:
    # --- Globe.gl HTML 區塊 ---
    # 準備傳給 JS 的資料
    globe_data = filtered_df[['latitude', 'longitude', 'infected', 'mutants', 'ut_forces', 'admin_region']].copy()
    # 處理顏色邏輯：突變率越高越紅
    globe_data['color_ratio'] = globe_data['mutants'] / (globe_data['infected'] + 1)
    
    json_data = globe_data.to_json(orient='records')

    globe_html = f"""
    <html>
    <head>
        <script src="//unpkg.com/globe.gl"></script>
        <style> body {{ margin: 0; background: transparent; overflow: hidden; }} </style>
    </head>
    <body>
        <div id="globeViz"></div>
        <script>
            const data = {json_data};
            const world = Globe()
                (document.getElementById('globeViz'))
                .backgroundColor('rgba(0,0,0,0)')
                .showAtmosphere(true)
                .atmosphereColor('#00d4ff')
                .globeImageUrl('//unpkg.com/three-globe/example/img/earth-dark.jpg')
                .bumpImageUrl('//unpkg.com/three-globe/example/img/earth-topology.png')
                
                // Bar 設定
                .hexBinPointsData(data)
                .hexBinPointWeight('infected')
                .hexAltitude(d => Math.min(d.sumWeight * 0.00001, 0.5)) // 高度映射感染人數
                .hexBinResolution(4)
                .hexTopColor(d => {{
                    const avgMutation = d.points.reduce((acc, p) => acc + p.color_ratio, 0) / d.points.length;
                    return avgMutation > 0.1 ? '#ff0000' : '#deff9a'; // 突變率高則變紅
                }})
                .hexSideColor(d => 'rgba(0, 212, 255, 0.4)')
                .hexLabel(d => `地區: ${{d.points[0].admin_region}}<br>總感染: ${{d.sumWeight}}`)
                
                // 動畫效果
                .controls().autoRotate = true;
                world.controls().autoRotateSpeed = 0.5;

            window.addEventListener('resize', () => {{
                world.width(window.innerWidth).height(window.innerHeight);
            }});
        </script>
    </body>
    </html>
    """
    components.html(globe_html, height=600)

with col3:
    st.subheader("📈 疫情走勢 (月)")
    trend_df = df.groupby('month_year')[['infected', 'deaths']].sum().reset_index()
    fig_line = px.line(trend_df, x='month_year', y='infected', template="plotly_dark", 
                      color_discrete_sequence=['#ff4d4d'])
    fig_line.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=300)
    st.plotly_chart(fig_line, use_container_width=True)
    
    st.subheader("🧬 病毒組成分析")
    pie_data = filtered_df[['zombified', 'mutants', 'deaths']].sum().reset_index()
    pie_data.columns = ['Category', 'Count']
    fig_pie = px.pie(pie_data, values='Count', names='Category', hole=.4,
                    template="plotly_dark", color_discrete_sequence=['#deff9a', '#ff4d4d', '#94a3b8'])
    fig_pie.update_layout(paper_bgcolor='rgba(0,0,0,0)', height=300, showlegend=False)
    st.plotly_chart(fig_pie, use_container_width=True)

st.markdown("---")
st.caption("Umbrella Corp © 1998 - 生化危機即時監控系統 (Level 5 Clearance Only)")