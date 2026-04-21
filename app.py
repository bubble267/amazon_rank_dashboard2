import streamlit as st
import pandas as pd
import re
import plotly.express as px

st.set_page_config(page_title="亚马逊排名趋势看板", layout="wide")
st.title("📈 亚马逊产品排名波动看板")

# 加载数据（自动缓存）
@st.cache_data
def load_data():
    df = pd.read_excel("data.xlsx", sheet_name="排名 (2)", header=0)
    # 填充空SKU
    df['SKU'] = df['SKU'].fillna('')
    mask = df['SKU'] == ''
    df.loc[mask, 'SKU'] = '变体_' + df.loc[mask].index.astype(str)
    # 提取日期列
    date_cols = [col for col in df.columns if re.match(r'\d{4}-\d{2}-\d{2}', str(col))]
    date_cols = sorted(date_cols, key=lambda x: pd.to_datetime(x))
    # 提取排名函数
    def extract_rank(cell):
        if pd.isna(cell):
            return None
        cell_str = str(cell)
        match = re.search(r'#\s*(\d+)', cell_str)
        return int(match.group(1)) if match else None
    # 构建长格式数据
    records = []
    for _, row in df.iterrows():
        sku = row['SKU']
        for date in date_cols:
            rank = extract_rank(row[date])
            if rank is not None:
                records.append({'SKU': sku, '日期': pd.to_datetime(date), '排名': rank})
    df_long = pd.DataFrame(records)
    # 过滤数据点少于3个的产品
    sku_counts = df_long['SKU'].value_counts()
    valid_skus = sku_counts[sku_counts >= 3].index
    df_long = df_long[df_long['SKU'].isin(valid_skus)]
    return df_long

df = load_data()
if df.empty:
    st.warning("没有足够的排名数据（每个产品至少需要3个时间点）")
    st.stop()

# 侧边栏选择产品
sku_list = sorted(df['SKU'].unique())
selected_sku = st.sidebar.selectbox("选择产品 SKU", sku_list)

# 过滤数据
df_sku = df[df['SKU'] == selected_sku].sort_values('日期')

# 绘制曲线
fig = px.line(df_sku, x='日期', y='排名', title=f"{selected_sku} 排名变化趋势",
              markers=True, labels={'排名': '品类排名 (数值越小越好)'})
fig.update_yaxis(autorange="reversed")  # 排名越小越好，倒置Y轴
fig.update_layout(hovermode='x unified')

st.plotly_chart(fig, use_container_width=True)

# 显示数据表格
st.subheader("历史排名数据")
st.dataframe(df_sku, use_container_width=True)

# 显示统计信息
st.sidebar.subheader("📊 产品统计")
st.sidebar.metric("有效数据点", len(df_sku))
st.sidebar.metric("平均排名", round(df_sku['排名'].mean(), 1))
st.sidebar.metric("最佳排名", df_sku['排名'].min())
st.sidebar.metric("最差排名", df_sku['排名'].max())
st.sidebar.metric("排名波动 (标准差)", round(df_sku['排名'].std(), 1))