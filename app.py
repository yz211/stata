import streamlit as st
import pandas as pd
import numpy as np
import statsmodels.api as sm
import statsmodels.formula.api as smf
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import seaborn as sns
from scipy import stats
import io
import json

# --- 页面配置 ---
st.set_page_config(
    page_title="政务服务满意度分析系统", 
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 自定义 CSS 美化 ---
st.markdown("""
<style>
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    h1, h2, h3 {
        color: #2c3e50;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        font-weight: bold;
    }
    .stButton>button:hover {
        border-color: #2c3e50;
        color: #2c3e50;
    }
    .highlight-box {
        padding: 1.5rem;
        border-radius: 0.5rem;
        background-color: #f0f2f6;
        border-left: 5px solid #4e8cff;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
    }
    /* 侧边栏宽度调整 */
    [data-testid="stSidebar"] {
        min-width: 600px !important;
        width: 600px !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 辅助函数：处理中文列名 ---
def safe_rename(df):
    """将中文列名映射为安全变量名 (v1, v2...)，避免 patsy 公式报错"""
    col_map = {col: f"v_{i}" for i, col in enumerate(df.columns)}
    reverse_map = {v: k for k, v in col_map.items()}
    df_safe = df.rename(columns=col_map)
    return df_safe, col_map, reverse_map

def get_formula_term(original_name, col_map, is_cat=False):
    safe_name = col_map[original_name]
    if is_cat:
        return f"C({safe_name})"
    return safe_name

def is_categorical(series, threshold=15):
    """判断是否为分类变量"""
    # 如果是 object 类型或者是 category 类型，或者是数值类型但唯一值很少
    if pd.api.types.is_object_dtype(series) or pd.api.types.is_categorical_dtype(series):
        return True
    if pd.api.types.is_numeric_dtype(series) and series.nunique() < threshold:
        return True
    return False

# --- 主程序 ---

def main():
    st.title("📊 政务服务满意度两阶段残差回归分析系统")
    st.markdown("""
    <div class="highlight-box">
    本系统基于 Stata 分析流程开发，支持自动化进行两阶段回归分析。
    <br><b>核心流程：</b> 1. 控制变量回归提取残差 → 2. 残差诊断与极端值处理 → 3. 交互效应回归与可视化
    </div>
    """, unsafe_allow_html=True)

    # --- 侧边栏：数据与变量配置 ---
    with st.sidebar:
        st.header("📂 1. 数据加载")
        uploaded_file = st.file_uploader("上传数据文件 (.dta, .csv, .xlsx)", type=['dta', 'csv', 'xlsx'])
        
        df_raw = None
        all_cols = []

        if uploaded_file:
            try:
                if uploaded_file.name.endswith('.dta'):
                    df_raw = pd.read_stata(uploaded_file)
                elif uploaded_file.name.endswith('.csv'):
                    df_raw = pd.read_csv(uploaded_file)
                else:
                    df_raw = pd.read_excel(uploaded_file)
                st.success(f"✅ 数据加载成功: {df_raw.shape[0]} 行, {df_raw.shape[1]} 列")
                all_cols = df_raw.columns.tolist()
            except Exception as e:
                st.error(f"数据读取失败: {e}")
                return
        else:
            st.info("请先上传数据文件")
            return

        st.markdown("---")
        st.header("🔧 配置管理")
        with st.expander("导入/导出 配置", expanded=True):
            # 1. 导入配置
            uploaded_cfg = st.file_uploader("加载配置文件 (.json)", type="json")
            if uploaded_cfg:
                try:
                    cfg = json.load(uploaded_cfg)
                    # 更新 Session State
                    for k, v in cfg.items():
                        # 简单的有效性检查：如果配置中的列名存在于当前数据中
                        is_valid = False
                        if isinstance(v, str):
                            if v in all_cols or v == "(不使用聚类)":
                                is_valid = True
                        elif isinstance(v, list):
                            if all(c in all_cols for c in v):
                                is_valid = True
                        
                        if is_valid:
                            st.session_state[k] = v
                    st.success("配置已加载！")
                except Exception as e:
                    st.error(f"配置文件加载失败: {e}")

            # 2. 导出配置 (需要获取当前选定的值，由于使用了 key，直接从 session_state 获取即可)
            # 注意：在首次运行时 session_state 可能为空，这里做个保护
            current_config = {}
            keys_to_save = ['dep_var', 'control_vars', 'fe_vars', 'vce_mode', 'cluster_var', 
                            'interact_var1', 'interact_var2', 'stage2_controls']
            
            # 检查是否所有 key 都在 session_state 中 (意味着用户至少渲染过一次界面)
            if all(k in st.session_state for k in keys_to_save):
                for k in keys_to_save:
                    current_config[k] = st.session_state[k]
                
                st.download_button(
                    label="💾 保存当前配置",
                    data=json.dumps(current_config, ensure_ascii=False, indent=2),
                    file_name="analysis_config.json",
                    mime="application/json"
                )

        st.markdown("---")
        st.header("⚙️ 2. 变量映射")
        
        # 辅助索引查找
        def find_idx(options, keywords):
            for i, opt in enumerate(options):
                if any(k in opt for k in keywords):
                    return i
            return 0

        # 1. 因变量
        # 注意：使用 key 后，default/index 参数仅在 key 不在 session_state 时生效 (即首次运行)
        dep_var = st.selectbox(
            "因变量 (Y)", 
            all_cols, 
            index=find_idx(all_cols, ["满意度", "satisfaction", "sat"]), 
            help="第一阶段回归的被解释变量",
            key="dep_var"
        )
        
        # 2. 控制变量
        st.subheader("第一阶段配置")
        control_vars = st.multiselect(
            "控制变量 (Controls)", 
            [c for c in all_cols if c != dep_var], 
            default=[c for c in all_cols if c != dep_var][:3],
            key="control_vars"
        )
        fe_vars = st.multiselect(
            "固定效应 (Fixed Effects)", 
            [c for c in all_cols if c != dep_var and c not in control_vars],
            key="fe_vars"
        )
        vce_mode = st.radio(
            "标准误处理方式 (VCE)",
            ["不使用", "vce(robust)", "vce(cluster)"],
            index=0,
            key="vce_mode"
        )
        if st.session_state.get("vce_mode") == "vce(cluster)":
            cluster_var = st.selectbox(
                "聚类变量 (Cluster groups)", 
                ["(未选择)"] + all_cols, 
                index=0,
                key="cluster_var"
            )
            if cluster_var == "(未选择)":
                cluster_var = "(不使用聚类)"
        else:
            cluster_var = "(不使用聚类)"

        # 3. 交互变量
        st.subheader("第二阶段配置")
        interact_var1 = st.selectbox(
            "交互变量 A (如: 服务人员特征)", 
            all_cols, 
            index=0,
            key="interact_var1"
        )
        interact_var2 = st.selectbox(
            "交互变量 B (如: 公众特征)", 
            all_cols, 
            index=1 if len(all_cols)>1 else 0,
            key="interact_var2"
        )
        
        # 确保默认选项在可用选项列表中
        stage2_options = [c for c in all_cols if c not in [interact_var1, interact_var2]]
        stage2_default = [c for c in control_vars if c in stage2_options]
        
        stage2_controls = st.multiselect(
            "第二阶段额外控制 (可选)", 
            stage2_options, 
            default=stage2_default, 
            help="通常保持与第一阶段一致或根据理论添加",
            key="stage2_controls"
        )

    # --- 数据预处理与安全映射 ---
    # 选取所有涉及的变量
    used_cols = list(set([dep_var] + control_vars + fe_vars + [interact_var1, interact_var2] + stage2_controls))
    if st.session_state.get("vce_mode") == "vce(cluster)" and cluster_var in all_cols:
        used_cols.append(cluster_var)
    
    # 简单清洗：删除含有缺失值的行 (仅针对所选变量)
    df_clean = df_raw[used_cols].dropna().copy()
    
    # 创建变量名映射 (解决中文列名问题)
    df_safe, col_map, reverse_map = safe_rename(df_clean)
    
    # 获取映射后的变量名
    safe_dep = col_map[dep_var]
    safe_controls = [col_map[c] for c in control_vars]
    safe_fes = [col_map[c] for c in fe_vars]
    safe_interact1 = col_map[interact_var1]
    safe_interact2 = col_map[interact_var2]
    safe_stage2_controls = [col_map[c] for c in stage2_controls]
    safe_cluster = col_map[cluster_var] if (st.session_state.get("vce_mode") == "vce(cluster)" and cluster_var in col_map) else None

    # --- 主界面 Tabs ---
    tab1, tab2, tab3, tab4 = st.tabs(["📋 数据概览", "📈 第一阶段: 残差提取", "🔍 残差诊断", "🚀 第二阶段: 交互回归"])

    with tab1:
        st.subheader("数据预览 (已自动剔除缺失值)")
        st.markdown(f"有效样本量: **{len(df_clean)}** (原始: {len(df_raw)}, 剔除: {len(df_raw)-len(df_clean)})")
        st.dataframe(df_clean.head())
        
        st.subheader("变量统计描述")
        st.dataframe(df_clean.describe())

    # --- Session State 管理 ---
    if 'resid_col' not in st.session_state:
        st.session_state.resid_col = None
    if 'is_stage1_done' not in st.session_state:
        st.session_state.is_stage1_done = False

    with tab2:
        st.header("第一阶段回归")
        st.markdown("目标：剔除控制变量和固定效应的影响，提取纯净的残差 (Residuals)。")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            # 构建公式
            fe_terms = [f"C({f})" for f in safe_fes]
            formula_parts = safe_controls + fe_terms
            formula_str = f"{safe_dep} ~ {' + '.join(formula_parts)}"
            
            st.code(f"Model: {dep_var} ~ {' + '.join(control_vars + [f'FixedEffect({f})' for f in fe_vars])}", language="python")
            
        with col2:
            run_stage1 = st.button("▶️ 运行回归", type="primary")

        if run_stage1:
            with st.spinner("正在拟合模型..."):
                try:
                    model_inst = smf.ols(formula=formula_str, data=df_safe)
                    if st.session_state.get("vce_mode") == "vce(cluster)":
                        if safe_cluster:
                            model1 = model_inst.fit(cov_type='cluster', cov_kwds={'groups': df_safe[safe_cluster]})
                            st.info(f"已使用 vce(cluster): {cluster_var}")
                        else:
                            st.error("请选择聚类变量")
                            return
                    elif st.session_state.get("vce_mode") == "vce(robust)":
                        model1 = model_inst.fit(cov_type='HC1')
                        st.info("已使用 vce(robust)")
                    else:
                        model1 = model_inst.fit()
                    
                    # 保存残差
                    df_safe['resid_sat'] = model1.resid
                    df_clean['resid_sat'] = model1.resid # 同步回原数据方便展示
                    
                    st.session_state.model1 = model1
                    st.session_state.df_safe_with_resid = df_safe
                    st.session_state.df_clean_with_resid = df_clean
                    st.session_state.is_stage1_done = True
                    st.toast("第一阶段回归完成！", icon="✅")
                    
                except Exception as e:
                    st.error(f"回归出错: {e}")

        if st.session_state.is_stage1_done:
            st.subheader("回归结果摘要")
            # 替换回中文变量名以便阅读
            summary_str = st.session_state.model1.summary().as_text()
            for safe_name, real_name in reverse_map.items():
                summary_str = summary_str.replace(safe_name, real_name)
            st.text(summary_str)

    with tab3:
        if not st.session_state.is_stage1_done:
            st.info("请先在“第一阶段”标签页运行回归。")
        else:
            st.header("残差诊断与清洗")
            df_res = st.session_state.df_clean_with_resid
            resid_vals = df_res['resid_sat']

            # 1. 可视化
            col_g1, col_g2 = st.columns(2)
            with col_g1:
                st.subheader("残差分布直方图")
                fig_hist, ax_hist = plt.subplots(figsize=(6, 4))
                sns.histplot(resid_vals, kde=True, color="skyblue", ax=ax_hist)
                ax_hist.set_title("Histogram of Residuals")
                st.pyplot(fig_hist)
            
            with col_g2:
                st.subheader("Q-Q 图 (正态性检验)")
                fig_qq, ax_qq = plt.subplots(figsize=(6, 4))
                stats.probplot(resid_vals, dist="norm", plot=ax_qq)
                ax_qq.get_lines()[0].set_color("skyblue")
                ax_qq.get_lines()[1].set_color("red")
                st.pyplot(fig_qq)

            # 2. 极端值检测
            st.subheader("极端值检测 (3σ原则)")
            mean_resid = resid_vals.mean()
            std_resid = resid_vals.std()
            threshold = 3 * std_resid
            
            df_res['is_extreme'] = df_res['resid_sat'].abs() > threshold
            n_extreme = df_res['is_extreme'].sum()
            
            col_m1, col_m2, col_m3 = st.columns(3)
            col_m1.metric("残差均值", f"{mean_resid:.4f}")
            col_m2.metric("标准差 (σ)", f"{std_resid:.4f}")
            col_m3.metric("极端值数量 (>3σ)", f"{n_extreme} ({n_extreme/len(df_res):.2%})")

            if n_extreme > 0:
                st.dataframe(df_res[df_res['is_extreme']].head())
            
            # 设置到 session state 供下一阶段使用
            st.session_state.df_res_analyzed = df_res
            st.session_state.df_safe_analyzed = st.session_state.df_safe_with_resid.copy()
            st.session_state.df_safe_analyzed['is_extreme'] = df_res['is_extreme'].values # 确保对齐

    with tab4:
        if 'df_safe_analyzed' not in st.session_state:
             st.info("请先完成残差诊断。")
        else:
            st.header("第二阶段：交互效应分析")
            
            col_opt1, col_opt2 = st.columns(2)
            with col_opt1:
                remove_extreme = st.toggle("剔除极端值样本", value=True)
            
            with col_opt2:
                st.markdown(f"当前分析模型: **Residual ~ {interact_var1} × {interact_var2} + Controls**")

            st.subheader("图表与输出设置")
            col_set1, col_set2, col_set3 = st.columns(3)
            with col_set1:
                chart_type = st.selectbox("图表类型", ["点图", "折线图", "柱状图"], index=0)
                show_ci = st.checkbox("显示置信区间", value=True)
                ci_level = st.slider("置信水平", min_value=0.80, max_value=0.99, value=0.90, step=0.01)
            with col_set2:
                fig_width = st.number_input("图宽(px)", min_value=600, max_value=2000, value=1000, step=50)
                fig_height = st.number_input("图高(px)", min_value=400, max_value=1500, value=600, step=50)
                fig_dpi = st.number_input("DPI", min_value=100, max_value=600, value=200, step=50)
            with col_set3:
                font_choice = st.selectbox("字体", ["默认", "SimSun", "Microsoft YaHei", "Arial"], index=0)
                uploaded_font = st.file_uploader("上传字体文件(.ttf)", type=["ttf"], accept_multiple_files=False)
                if uploaded_font is not None:
                    try:
                        bytes_data = uploaded_font.read()
                        tmp_path = f"/tmp/{uploaded_font.name}"
                        with open(tmp_path, "wb") as f:
                            f.write(bytes_data)
                        fm.fontManager.addfont(tmp_path)
                        plt.rcParams['font.family'] = fm.FontProperties(fname=tmp_path).get_name()
                        plt.rcParams['axes.unicode_minus'] = False
                    except Exception:
                        pass
                else:
                    if font_choice != "默认":
                        plt.rcParams['font.sans-serif'] = [font_choice]
                        plt.rcParams['axes.unicode_minus'] = False

            run_stage2 = st.button("🚀 运行第二阶段回归", type="primary")
            
            if run_stage2:
                # 准备数据
                data_for_reg = st.session_state.df_safe_analyzed.copy()
                if remove_extreme:
                    data_for_reg = data_for_reg[~data_for_reg['is_extreme']]
                
                # 判断是否需要Categorical处理
                # 自动检测：如果是非数值列，或者数值列但唯一值较少，则视为分类变量
                is_cat1 = is_categorical(data_for_reg[safe_interact1])
                is_cat2 = is_categorical(data_for_reg[safe_interact2])
                
                term1 = f"C({safe_interact1})" if is_cat1 else safe_interact1
                term2 = f"C({safe_interact2})" if is_cat2 else safe_interact2
                
                # 构建公式: resid ~ A * B + Controls
                formula_s2 = f"resid_sat ~ {term1} * {term2}"
                if safe_stage2_controls:
                    formula_s2 += " + " + " + ".join(safe_stage2_controls)
                
                try:
                    with st.spinner("计算中..."):
                        model_inst2 = smf.ols(formula=formula_s2, data=data_for_reg)
                        if st.session_state.get("vce_mode") == "vce(cluster)":
                            if safe_cluster:
                                model2 = model_inst2.fit(cov_type='cluster', cov_kwds={'groups': data_for_reg[safe_cluster]})
                            else:
                                st.error("请选择聚类变量")
                                return
                        elif st.session_state.get("vce_mode") == "vce(robust)":
                            model2 = model_inst2.fit(cov_type='HC1')
                        else:
                            model2 = model_inst2.fit()
                        
                        st.success("分析完成！")
                        
                        st.subheader("回归结果")
                        coef_df = pd.DataFrame({
                            '变量': model2.params.index,
                            '系数': model2.params.values,
                            '标准误': model2.bse.values,
                            't值': model2.tvalues.values,
                            'p值': model2.pvalues.values
                        })
                        ci = model2.conf_int()
                        coef_df['CI下限'] = ci[0].values
                        coef_df['CI上限'] = ci[1].values
                        coef_df['变量'] = coef_df['变量'].replace(reverse_map)
                        st.dataframe(coef_df)
                        styled_html = coef_df.to_html(index=False)
                        st.download_button("📥 下载系数表 (HTML)", data=styled_html, file_name="stage2_coefficients.html", mime="text/html")

                        # --- 可视化 ---
                        st.markdown("---")
                        st.subheader("交互效应可视化 (Predictive Margins)")
                        
                        if is_cat1 and is_cat2:
                            # 仅当两个都是分类变量时，绘图最有意义
                            # 构造预测网格
                            u1 = sorted(data_for_reg[safe_interact1].unique())
                            u2 = sorted(data_for_reg[safe_interact2].unique())
                            
                            import itertools
                            grid = list(itertools.product(u1, u2))
                            pred_df = pd.DataFrame(grid, columns=[safe_interact1, safe_interact2])
                            
                            # 填充控制变量为均值或众数
                            for c in safe_stage2_controls:
                                if pd.api.types.is_numeric_dtype(data_for_reg[c]):
                                    pred_df[c] = data_for_reg[c].mean()
                                else:
                                    pred_df[c] = data_for_reg[c].mode()[0]
                            
                            alpha = 1 - ci_level
                            pred = model2.get_prediction(pred_df)
                            sf = pred.summary_frame(alpha=alpha)
                            pred_df['predicted_resid'] = sf['mean']
                            pred_df['ci_lower'] = sf['mean_ci_lower']
                            pred_df['ci_upper'] = sf['mean_ci_upper']
                            
                            # 映射回真实值用于绘图标签
                            pred_df['Label_1'] = pred_df[safe_interact1] # 暂时保留原始值
                            pred_df['Label_2'] = pred_df[safe_interact2]
                            
                            # 绘图
                            fig_margin, ax_margin = plt.subplots(figsize=(fig_width/100, fig_height/100), dpi=fig_dpi)
                            sns.set_style("whitegrid")
                            cats = sorted(pred_df[safe_interact1].unique())
                            pos_map = {v:i for i,v in enumerate(cats)}
                            for h in sorted(pred_df[safe_interact2].unique()):
                                sub = pred_df[pred_df[safe_interact2] == h]
                                x = [pos_map[v] for v in sub[safe_interact1]]
                                y = sub['predicted_resid']
                                ax_margin.plot(x, y, marker='o', label=f"{interact_var2}={h}")
                                if show_ci:
                                    yerr_lower = y - sub['ci_lower']
                                    yerr_upper = sub['ci_upper'] - y
                                    ax_margin.errorbar(x, y, yerr=[yerr_lower, yerr_upper], fmt='none', ecolor='gray', capsize=4)
                            ax_margin.set_xticks(list(range(len(cats))))
                            ax_margin.set_xticklabels(cats)
                            
                            # 设置标签
                            ax_margin.set_xlabel(interact_var1)
                            ax_margin.set_ylabel(f"Predicted Residual of {dep_var}")
                            ax_margin.legend(title=interact_var2)
                            ax_margin.set_title(f"Interaction Effect: {interact_var1} × {interact_var2}")
                            
                            st.pyplot(fig_margin)
                            buf = io.BytesIO()
                            fig_margin.savefig(buf, format='png', dpi=fig_dpi, bbox_inches='tight')
                            buf.seek(0)
                            st.download_button("📥 下载图像 (PNG)", data=buf, file_name="margins_plot.png", mime="image/png")
                            
                            # 导出绘图数据
                            export_df = pred_df.rename(columns=reverse_map)
                            st.dataframe(export_df)
                            st.download_button("📥 下载绘图数据 (CSV)", data=export_df.to_csv(index=False).encode('utf-8-sig'), file_name="plot_data.csv", mime="text/csv")
                            margin_html = export_df.to_html(index=False)
                            st.download_button("📥 下载边际效应数据 (HTML)", data=margin_html, file_name="margins_data.html", mime="text/html")
                        else:
                            st.warning("当前仅支持两个交互变量均为分类变量（或取值较少）时的自动绘图。")

                except Exception as e:
                    st.error(f"第二阶段分析出错: {e}")
                    st.markdown("**Debug 提示**: 请检查变量类型是否正确，或者是否存在多重共线性问题。")

if __name__ == "__main__":
    main()
