import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import re


def create_final_plot():
    """
    一个完整的函数，用于解析数据并生成最终样式的高质量图表：
    - 精确定位图例到 'Mockito' 和 'Time' 项目上方。
    - 使用您指定的4种颜色。
    """

    # ================================================================= #
    # 1. 您的原始数据 (保持不变)
    # ================================================================= #
    raw_data = """
    Num$_{nl}$=10
    ========================================
    Per-project total runtime summary:
      Chart           0.33 min (19.91 sec)
      Closure         1.86 min (111.86 sec)
      Lang            0.97 min (58.21 sec)
      Math            1.52 min (91.43 sec)
      Mockito         0.45 min (26.94 sec)
      Time            0.38 min (22.93 sec)
    ========================================
    
    Num$_{nl}$=50
    ========================================
    Per-project total runtime summary:
      Chart           0.33 min (88.86 sec)
      Closure         1.86 min (548.83 sec)
      Lang            0.97 min (203.26 sec)
      Math            1.52 min (436.87 sec)
      Mockito         0.45 min (137.99 sec)
      Time            0.38 min (112.13 sec)
    ========================================

    Num$_{nl}$=100
    ========================================
    Per-project total runtime summary:
      Chart           2.64 min (158.53 sec)
      Closure         18.01 min (1080.62 sec)
      Lang            4.97 min (298.04 sec)
      Math            13.68 min (820.65 sec)
      Mockito         4.61 min (276.64 sec)
      Time            3.73 min (223.54 sec)
    ========================================

    Num$_{nl}$=200
    ========================================
    Per-project total runtime summary:
      Chart           4.23 min (254.12 sec)
      Closure         35.79 min (2147.30 sec)
      Lang            6.89 min (413.34 sec)
      Math            24.46 min (1467.66 sec)
      Mockito         9.07 min (544.32 sec)
      Time            7.44 min (446.48 sec)
    ========================================

    Num$_{nl}$=All
    ========================================
    Per-project total runtime summary:
      Chart           20.243 min (1214.58 sec)
      Closure         711.51 min (42690.56 sec)
      Lang            8.59 min (516.58 sec)
      Math            58.02 min (3481.77 sec)
      Mockito         26.42 min (1585.69 sec)
      Time            54.33 min (3259.84 sec)
    ========================================
    """

    # ================================================================= #
    # 2. 解析数据 (保持不变)
    # ================================================================= #
    print("[*] Parsing data...")
    data_list = []
    # ... (此处省略与之前完全相同的解析代码)
    current_category = None
    data_blocks = re.split(r'\n\s*\n', raw_data.strip())
    for block in data_blocks:
        lines = block.strip().split('\n')
        category_line = lines[0].strip()
        if category_line.startswith("Num") or category_line.startswith("All"):
            current_category = category_line
        else:
            continue
        for line in lines:
            line = line.strip()
            match = re.search(r"^\s*(\w+)\s+.*\(([\d\.]+)\s+sec\)", line)
            if match:
                project_name = match.group(1)
                runtime_sec = float(match.group(2))
                data_list.append(
                    {"Project": project_name, "Category": current_category, "Runtime (seconds)": runtime_sec})
    df = pd.DataFrame(data_list)
    print("[*] Data parsing complete.")

    # ================================================================= #
    # 3. 绘图 (应用所有修改)
    # ================================================================= #
    print("[*] Generating plot...")

    # 设置全局字体为 Times New Roman
    plt.rcParams['font.family'] = 'serif'
    plt.rcParams['font.serif'] = ['Times New Roman'] + plt.rcParams['font.serif']

    sns.set_theme(style="whitegrid", font_scale=15.0)
    fig, ax = plt.subplots(figsize=(20, 12))

    # ★★★ 核心改动 1: 定义您指定的颜色调色板 ★★★
    # 顺序: XAI4FL, MTL_transfer, transfer, CodeHealer
    custom_palette = ['#39a6d6', '#34ae94', "#b3de69", '#8e92f4', '#f67088']

    # 绘制分组柱形图
    sns.barplot(
        data=df,
        x="Project",
        y="Runtime (seconds)",
        hue="Category",
        hue_order=["Num$_{nl}$=10", "Num$_{nl}$=50", "Num$_{nl}$=100", "Num$_{nl}$=200", "Num$_{nl}$=All"],
        ax=ax,
        palette=custom_palette
    )

    # 设置坐标轴标签
    ax.set_xlabel("", fontsize=20, labelpad=20)
    ax.set_ylabel("Runtime (seconds, log scale)", fontsize=30, labelpad=20)
    ax.set_yscale("log")

    # 优化坐标轴刻度字体
    ax.tick_params(axis='x', labelsize=30)
    ax.tick_params(axis='y', labelsize=30)

    # ★★★ 核心改动 2: 精确定位图例 ★★★
    plt.legend(
        title=None,
        # 使用 bbox_to_anchor 将图例锚定到特定位置
        # (0.83, 0.98) 是一个相对坐标：
        # x=0.83 表示在横轴83%的位置 (正好在Mockito和Time之间)
        # y=0.98 表示在纵轴98%的位置 (非常高，在10^4和10^5之间)
        bbox_to_anchor=(0.83, 0.92),
        loc='upper center', # 将图例的“中上点”对准锚点
        ncol=2,
        fontsize=20,
        frameon=True,
        edgecolor='black'
    )

    # 扩大 Y 轴上限
    max_value = df["Runtime (seconds)"].max()
    ax.set_ylim(top=max_value * 10)

    # 在柱顶添加数值标签 (保持不变)
    for p in ax.patches:
        height = p.get_height()
        if height > 0:
            ax.annotate(
                f"{height:.0f}",
                (p.get_x() + p.get_width() / 2., height),
                ha='center',
                va='center',
                xytext=(0, 32),
                textcoords='offset points',
                fontsize=20,
                rotation=90
            )

    # 样式优化
    sns.despine(left=True)
    ax.grid(axis='x', visible=False)
    ax.grid(axis='y', which='major', linestyle='--', linewidth=0.8)

    # 调整布局
    plt.tight_layout()

    # ================================================================= #
    # 4. 保存为 PDF (保持不变)
    # ================================================================= #
    output_filename = "runtime.pdf"
    plt.savefig(output_filename, format='pdf', bbox_inches='tight')

    plt.show()

    print(f"[*] Final plot has been saved as '{output_filename}'")


if __name__ == "__main__":
    create_final_plot()

# import pandas as pd
# import seaborn as sns
# import matplotlib.pyplot as plt
# import re
#
#
# def create_final_plot():
#     """
#     一个完整的函数，用于解析数据并生成最终样式的高质量图表，
#     其中 'Top50' 为白色，其他类别使用您指定的原始颜色。
#     """
#
#     # ================================================================= #
#     # 1. 您的原始数据 (已包含 Top50)
#     # ================================================================= #
#     raw_data = """
#     Top10
#     ========================================
#     Per-project total runtime summary:
#       Chart           0.33 min (19.91 sec)
#       Closure         1.86 min (111.86 sec)
#       Lang            0.97 min (58.21 sec)
#       Math            1.52 min (91.43 sec)
#       Mockito         0.45 min (26.94 sec)
#       Time            0.38 min (22.93 sec)
#     ========================================
#
#     Top50
#     ========================================
#     Per-project total runtime summary:
#       Chart           0.33 min (88.86 sec)
#       Closure         1.86 min (548.83 sec)
#       Lang            0.97 min (203.26 sec)
#       Math            1.52 min (436.87 sec)
#       Mockito         0.45 min (137.99 sec)
#       Time            0.38 min (112.13 sec)
#     ========================================
#
#     Top100
#     ========================================
#     Per-project total runtime summary:
#       Chart           2.64 min (158.53 sec)
#       Closure         18.01 min (1080.62 sec)
#       Lang            4.97 min (298.04 sec)
#       Math            13.68 min (820.65 sec)
#       Mockito         4.61 min (276.64 sec)
#       Time            3.73 min (223.54 sec)
#     ========================================
#
#     Top200
#     ========================================
#     Per-project total runtime summary:
#       Chart           4.23 min (254.12 sec)
#       Closure         35.79 min (2147.30 sec)
#       Lang            6.89 min (413.34 sec)
#       Math            24.46 min (1467.66 sec)
#       Mockito         9.07 min (544.32 sec)
#       Time            7.44 min (446.48 sec)
#     ========================================
#
#     所有语句
#     ========================================
#     Per-project total runtime summary:
#       Chart           20.243 min (1214.58 sec)
#       Closure         711.51 min (42690.56 sec)
#       Lang            8.59 min (516.58 sec)
#       Math            58.02 min (3481.77 sec)
#       Mockito         26.42 min (1585.69 sec)
#       Time            54.33 min (3259.84 sec)
#     ========================================
#     """
#
#     # ================================================================= #
#     # 2. 解析数据 (保持不变)
#     # ================================================================= #
#     print("[*] Parsing data...")
#     data_list = []
#     # ... (此处省略与之前完全相同的解析代码) ...
#     current_category = None
#     data_blocks = re.split(r'\n\s*\n', raw_data.strip())
#     for block in data_blocks:
#         lines = block.strip().split('\n')
#         category_line = lines[0].strip()
#         if category_line.startswith("Top"):
#             current_category = category_line
#         elif category_line.startswith("所有语句"):
#             current_category = "All Statements"
#         else:
#             continue
#         for line in lines:
#             line = line.strip()
#             match = re.search(r"^\s*(\w+)\s+.*\(([\d\.]+)\s+sec\)", line)
#             if match:
#                 project_name = match.group(1)
#                 runtime_sec = float(match.group(2))
#                 data_list.append(
#                     {"Project": project_name, "Category": current_category, "Runtime (seconds)": runtime_sec})
#     df = pd.DataFrame(data_list)
#     print("[*] Data parsing complete.")
#
#     # ================================================================= #
#     # 3. 绘图
#     # ================================================================= #
#     print("[*] Generating plot...")
#
#     # 推荐使用 Times New Roman 字体
#     plt.rcParams['font.family'] = 'serif'
#     plt.rcParams['font.serif'] = ['Times New Roman'] + plt.rcParams['font.serif']
#
#     sns.set_theme(style="whitegrid", font_scale=1.5)
#     fig, ax = plt.subplots(figsize=(20, 12))
#     # ★★★ 核心改动: 定义包含白色和您指定颜色的自定义调色板 ★★★
#     custom_palette = {
#         "Top10": "#39a6d6",
#         "Top50": "#FFFFFF",  # <-- Top50 设置为白色
#         "Top100": "#34ae94",
#         "Top200": "#8e92f4",
#         "All Statements": "#f67088"
#     }
#
#     # 定义绘图顺序
#     category_order = ["Top10", "Top50", "Top100", "Top200", "All Statements"]
#
#     # 绘制分组柱形图 (使用更优的 x 和 hue 设置)
#     sns.barplot(
#         data=df,
#         x="Project",
#         y="Runtime (seconds)",
#         hue="Category",
#         hue_order=category_order,
#         palette=custom_palette,  # <-- 应用最终的颜色方案
#         ax=ax,
#         edgecolor='black',  # <-- 为所有柱子添加黑色边框，确保白色可见
#         linewidth=1.5
#     )
#
#     # 设置坐标轴标签 (无总标题)
#     ax.set_xlabel("", fontsize=30, labelpad=15)
#     ax.set_ylabel("Runtime (seconds, log scale)", fontsize=30, labelpad=20)
#     ax.set_yscale("log")
#
#     # 优化坐标轴刻度的字体大小
#     ax.tick_params(axis='x', labelsize=30)
#     ax.tick_params(axis='y', labelsize=30)
#
#     # 优化图例
#     plt.legend(title='Top-N Strategy', bbox_to_anchor=(1.01, 1), loc='upper left', borderaxespad=0., fontsize=25,
#                title_fontsize=25)
#     max_value = df["Runtime (seconds)"].max()
#     ax.set_ylim(top=max_value * 5)
#
#     # 在柱顶添加垂直数值标签 (保持不变)
#     for p in ax.patches:
#         height = p.get_height()
#         if height > 0:
#             ax.annotate(
#                 f"{height:.0f}",
#                 (p.get_x() + p.get_width() / 2., height),
#                 ha='center',
#                 va='center',
#                 xytext=(0, 32),
#                 textcoords='offset points',
#                 fontsize=20,
#                 rotation=90
#             )
#
#     # 样式优化
#     sns.despine(left=True)
#     ax.grid(axis='x', visible=False)
#     ax.grid(axis='y', which='major', linestyle='--', linewidth=0.8)
#
#     # 调整布局
#     plt.tight_layout(rect=[0, 0, 0.9, 1])
#
#     # ================================================================= #
#     # 4. 保存为 PDF
#     # ================================================================= #
#     output_filename = "runtime.pdf"
#     plt.savefig(output_filename, format='pdf', bbox_inches='tight')
#     plt.show()
#     print(f"[*] Final styled plot has been saved as '{output_filename}'")
#
#
# if __name__ == "__main__":
#     create_final_plot()