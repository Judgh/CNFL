# import csv
# import os
# import re
# from collections import defaultdict
# from itertools import groupby
# import sys
#
# a = 0.8#可疑度相乘的权重
# b = 0.2#排名的权重
# def merge_files_with_weights(input_dir1, input_dir2, output_dir,topN):
#     """
#     将 input_dir1(topN) 和 input_dir2(natural) 中的文件进行合并，并将结果保存到 output_dir 中。
#     """
#     # 检查输入路径是否存在
#     if not os.path.exists(input_dir1):
#         print(f"[错误] 输入目录1不存在: {input_dir1}")
#         return
#     if not os.path.exists(input_dir2):
#         print(f"[错误] 输入目录2不存在: {input_dir2}")
#         return
#
#     # 遍历 input_dir1 中的目录结构
#     for root, dirs, files in os.walk(input_dir1):
#         # 获取相对路径（相对于 input_dir1）
#         relative_path = os.path.relpath(root, input_dir1)
#
#         # 遍历文件
#         for file in files:
#             if file == "stmt-susps.txt":
#                 # 构建输入文件路径
#                 file_path1 = os.path.join(root, file)  # input_dir1 中的 stmt-susps.txt
#                 file_path2 = os.path.join(input_dir2, relative_path, "entropy.txt")  # input_dir2 中的 entropy.txt
#
#                 # 检查文件是否存在
#                 if not os.path.exists(file_path2):
#                     print(f"[警告] 文件 {file_path2} 不存在，跳过该文件")
#                     sys.exit(1)
#
#                 # 构建输出路径
#                 output_path = os.path.join(output_dir, relative_path, file)
#                 os.makedirs(os.path.dirname(output_path), exist_ok=True)
#
#                 # 处理合并
#                 merged_data = process_files(file_path1, file_path2,topN)
#                 print(f"合并结果保存到: {output_path}")
#
#                 # 写入结果
#                 # with open(output_path, 'w') as f_out:
#                 #     for key, value in merged_data.items():
#                 #         f_out.write(f"{key},{value:.10f}\n")
#
#
# def normalize(data2):
#     """
#     归一化数据：将每个值除以最大值，确保数据处于 [0, 1] 范围内。
#     """
#     if data2:
#         values = list(data2.values())
#         min_val = min(values)
#         max_val = max(values)
#         # 处理所有值相同的情况（避免除以0）
#         if min_val == max_val:
#             # 如果全部值相同，统一设为0.5（中性值）
#             normalized_value = 0.5
#             for key in data2:
#                 data2[key] = normalized_value
#         else:
#             for key in data2:
#                 data2[key] = (data2[key] - min_val) / (max_val - min_val)
#     return data2
#
#
# def rank_based_weighted_average(data):
#     """
#     计算基于排名的加权平均。每个条目的权重是它的倒数排名。
#     data 是一个包含（语句，值）元组的字典。
#     """
#     total_weight = 0
#     weighted_sum = 0
#
#     # 对数据按值进行排序
#     sorted_data = sorted(data.items(), key=lambda x: x[1], reverse=True)
#
#     # 计算加权平均
#     for rank, (stmt, value) in enumerate(sorted_data, 1):
#         weight = 1 / rank  # 倒数排名作为权重
#         weighted_sum += weight * value
#         total_weight += weight
#
#     return weighted_sum / total_weight if total_weight != 0 else 0
#
#
# def process_files(file1, file2, topN):
#     """处理文件并根据两个文件的原始排名之和进行加权评分"""
#     raw_data1 = []
#     original_order = []  # 新增：记录原始键顺序
#     with open(file1, 'r') as f:
#         for line in f:
#             if line.strip() and ',' in line:
#                 key, value = line.rsplit(',', 1)
#                 key = key.replace('/', '.').strip()
#                 try:
#                     raw_data1.append((key, float(value.strip())))
#                     original_order.append(key)  # 记录原始键顺序
#                 except ValueError:
#                     print(f"[错误] 文件 {file1} 的值无效: {value}")
#
#     original_positions = {key: idx for idx, key in enumerate(original_order)}
#
#     # 排名：越前面排名越高（rank = 1 表示第一）
#     sorted_data1 = sorted(raw_data1, key=lambda x: x[1], reverse=True)
#     rank1 = {key: idx + 1 for idx, (key, _) in enumerate(sorted_data1)}
#     data1 = {key: value for key, value in raw_data1}
#     data1 = normalize(data1)
#
#     # 读取 entropy.txt
#     raw_data2 = []
#     if os.path.getsize(file2) == 0:
#         return {k: 0.0 for k in data1.keys()}  # 为空则全部为 0
#     original_order2 = [key for key, _ in raw_data2]
#     original_positions2 = {key: idx for idx, key in enumerate(original_order2)}
#
#     with open(file2, 'r') as f:
#         for line in f:
#             if line.strip() and ',' in line:
#                 key, value = line.rsplit(',', 1)
#                 key = key.replace('/', '.').strip()
#                 try:
#                     raw_data2.append((key, float(value.strip())))
#                 except ValueError:
#                     print(f"[错误] 文件 {file2} 的值无效: {value}")
#
#     sorted_data2 = sorted(raw_data2, key=lambda x: x[1], reverse=True)
#     rank2 = {key: idx + 1 for idx, (key, _) in enumerate(sorted_data2)}
#     data2 = {key: value for key, value in raw_data2}
#     data2 = normalize(data2)
#     final_scores = {}
#     all_keys = set(data1.keys()).union(data2.keys())
#     for key in all_keys:
#         val1 = data1.get(key, 0)
#         val2 = data2.get(key, 0)
#         r1 = rank1.get(key, topN + 1)
#         r2 = rank2.get(key, topN + 1)
#         # 计算得分公式
#         final_scores[key] = val1**0.9 * val2**0.1 * a + b * (1 / r1 + 1 / r2)
#
#     sorted_items = sorted(
#         final_scores.items(),
#         key=lambda x: (-x[1], original_positions.get(x[0], len(original_order) + 1))
#     )
#
#     return dict(sorted_items)
#
#
#
# def extract_project_info(project_id):
#     """从项目ID中提取前缀和数字（例如 'Chart19' → ('Chart', 19)）"""
#     match = re.match(r"([A-Za-z]+)(\d+)", project_id)
#     if match:
#         return (match.group(1), int(match.group(2)))
#     return (project_id, 0)  # 默认处理
# def read_rankings(file_path):
#     """读取stmt-susps.txt文件并返回{类名: 排名}的字典"""
#     if not os.path.exists(file_path):
#         return {}
#
#     with open(file_path, 'r') as f:
#         lines = [line.strip() for line in f if line.strip()]
#
#     if lines and lines[0].startswith("Statement,Suspiciousness"):
#         lines = lines[1:]
#
#     entries = []
#     for line in lines:
#         if ',' in line:
#             parts = line.rsplit(',', 1)
#             if len(parts) == 2:
#                 stmt, score = parts
#                 try:
#                     entries.append((stmt.strip(), float(score.strip())))
#                 except ValueError:
#                     continue
#
#     sorted_entries = sorted(entries, key=lambda x: x[1], reverse=True)
#     return {stmt: rank for rank, (stmt, _) in enumerate(sorted_entries, 1)}
# def process_project(project, buggy_lines_file, sbfl_dir1, sbfl_dir2):
#     """处理单个项目，返回结果列表"""
#     results = []
#     project_type, number_part = project.split('-')
#     number = int(number_part.split('.')[0])
#     project_id = f"{project_type}{number}"
#
#     dir1_file = os.path.join(sbfl_dir1, project_type, str(number), "stmt-susps.txt")
#     dir2_file = os.path.join(sbfl_dir2, project_type, str(number), "stmt-susps.txt")
#
#     rankings1 = read_rankings(dir1_file)
#     rankings2 = read_rankings(dir2_file)
#
#     with open(buggy_lines_file, 'r', errors='ignore') as f:
#         buggy_lines = [line.strip() for line in f if line.strip()]
#
#     for stmt in buggy_lines:
#         rank1 = rankings1.get(stmt, -1)
#         rank2 = rankings2.get(stmt, -1)
#
#         if rank1 == -1 and rank2 == -1:
#             continue
#
#         # 计算差值：rank2 - rank1
#         diff = rank2 - rank1 if (rank1 != -1 and rank2 != -1) else -1
#
#         results.append({
#             "project_id": project_id,
#             "stmt": stmt,
#             "rank1": rank1,
#             "rank2": rank2,
#             "diff": diff,
#             "type": project_type,
#             "number": number
#         })
#
#     return results
#
# def result_analysis_big(multiply_path,topN_path,buggy_lines_dir,output_dir):
#     all_results = []
#     # 处理所有项目
#     for project_type in ["Chart", "Lang", "Math", "Closure", "Mockito", "Time"]:
#         buggy_base = os.path.join(buggy_lines_dir, project_type)
#         for buggy_file in os.listdir(buggy_base):
#             if buggy_file.endswith(".buggy.lines"):
#                 full_path = os.path.join(buggy_base, buggy_file)
#                 project_name = buggy_file.split('.')[0]
#                 results = process_project(
#                     project=project_name,
#                     buggy_lines_file=full_path,
#                     sbfl_dir1=multiply_path,
#                     sbfl_dir2=topN_path
#                 )
#                 all_results.extend(results)
#     all_results.sort(key=lambda x: (x["type"], x["number"]))
#
#     # 写入原始明细文件
#     output_file = os.path.join(output_dir, "rank_differences1.txt")
#     with open(output_file, 'w') as f:
#         f.write("Project,Statement,Rank1,Rank2,Difference\n")
#         for entry in all_results:
#             line = f"{entry['project_id']},{entry['stmt']},{entry['rank1']},{entry['rank2']},{entry['diff']}\n"
#             f.write(line)
#
#     # 新增：按项目合并统计最小值
#     # 按project_id和number分组
#     sorted_for_grouping = sorted(all_results, key=lambda x: (x["project_id"], x["number"]))
#     grouped_results = groupby(sorted_for_grouping, key=lambda x: (x["project_id"], x["number"]))
#
#     merged_project_stats = []
#     for (project_id, number), group in grouped_results:
#         group_list = list(group)
#
#         # 收集有效rank
#         valid_rank1 = [item["rank1"] for item in group_list if item["rank1"] != -1]
#         valid_rank2 = [item["rank2"] for item in group_list if item["rank2"] != -1]
#
#         # 计算最小值
#         min_rank1 = min(valid_rank1) if valid_rank1 else -1
#         min_rank2 = min(valid_rank2) if valid_rank2 else -1
#
#         # 计算差值（仅当两者都有有效值时）
#         diff = min_rank2 - min_rank1 if (min_rank1 != -1 and min_rank2 != -1) else -1
#
#         merged_project_stats.append({
#             "project_id": project_id,
#             "min_rank1": min_rank1,
#             "min_rank2": min_rank2,
#             "diff": diff,
#             "number": number
#         })
#
#     # 按项目类型和数字排序
#     merged_project_stats.sort(key=lambda x: (extract_project_info(x["project_id"])[0], x["number"]))
#
#     # 写入合并统计文件
#     merged_output_file = os.path.join(output_dir, f"基于排名的加权平均/Rank-based Weighted Average（基于排名的加权平均)_project_min_ranks({a},{b}).txt")
#     # 确保目录存在（自动创建所有不存在的父目录）
#     os.makedirs(os.path.dirname(merged_output_file), exist_ok=True)
#     with open(merged_output_file, 'w') as f:
#         f.write("Project,MinRank1,MinRank2,Difference\n")
#         for stat in merged_project_stats:
#             line = f"{stat['project_id']},{stat['min_rank1']},{stat['min_rank2']},{stat['diff']}\n"
#             f.write(line)
#
#     print(f"处理完成！原始结果保存至: {output_file}")
#     print(f"合并统计保存至: {merged_output_file}")
#
# def count_ranks(file_path):
#     # 初始化数据结构
#     project_stats = defaultdict(lambda: {
#         'min_rank1': {'1': 0, '<3': 0, '<5': 0},
#         'min_rank2': {'1': 0, '<3': 0, '<5': 0}
#     })
#
#     total_stats = {
#         'min_rank1': {'1': 0, '<3': 0, '<5': 0},
#         'min_rank2': {'1': 0, '<3': 0, '<5': 0},
#         'sum1': 0,
#         'sum2': 0,
#         'count': 0
#     }
#
#     with open(file_path, 'r') as file:
#         reader = csv.DictReader(file)
#         for row in reader:
#             # 解析项目名称（例如 Chart3 -> Chart）
#             project_name = ''.join([c for c in row['Project'] if not c.isdigit()])
#
#             rank1 = int(row['MinRank1'])
#             rank2 = int(row['MinRank2'])
#
#             # 更新项目统计（仅计数）
#             update_project_stats(project_stats[project_name], rank1, rank2)
#             # 更新总统计（包含求和）
#             update_total_stats(total_stats, rank1, rank2)
#
#     # 计算总MFR
#     total_stats['MFR1'] = total_stats['sum1'] / total_stats['count'] if total_stats['count'] > 0 else 0
#     total_stats['MFR2'] = total_stats['sum2'] / total_stats['count'] if total_stats['count'] > 0 else 0
#
#     return project_stats, total_stats
#
# def update_project_stats(proj_stats, rank1, rank2):
#     """ 更新子项目统计（仅计数） """
#     # MinRank1
#     if rank1 == 1:
#         proj_stats['min_rank1']['1'] += 1
#     if 0 < rank1 <= 3:
#         proj_stats['min_rank1']['<3'] += 1
#     if 0 < rank1 <= 5:
#         proj_stats['min_rank1']['<5'] += 1
#
#     # MinRank2
#     if rank2 == 1:
#         proj_stats['min_rank2']['1'] += 1
#     if 0 < rank2 <= 3:
#         proj_stats['min_rank2']['<3'] += 1
#     if 0 < rank2 <= 5:
#         proj_stats['min_rank2']['<5'] += 1
#
#
# def update_total_stats(total_stats, rank1, rank2):
#     """ 更新总统计（包含求和） """
#     # MinRank1
#     if rank1 == 1:
#         total_stats['min_rank1']['1'] += 1
#     if 0 < rank1 <= 3:
#         total_stats['min_rank1']['<3'] += 1
#     if 0 < rank1 <= 5:
#         total_stats['min_rank1']['<5'] += 1
#     total_stats['sum1'] += rank1
#
#     # MinRank2
#     if rank2 == 1:
#         total_stats['min_rank2']['1'] += 1
#     if 0 < rank2 <= 3:
#         total_stats['min_rank2']['<3'] += 1
#     if 0 < rank2 <= 5:
#         total_stats['min_rank2']['<5'] += 1
#     total_stats['sum2'] += rank2
#
#     total_stats['count'] += 1
# def count135(rank_file,analysis_file):
#     project_stats, total_stats = count_ranks(rank_file)
#
#     with open(analysis_file, 'w') as f:
#         # 各子项目统计
#         for proj_name, stats in project_stats.items():
#             f.write(f"\n======= {proj_name} 项目统计 =======\n")
#             f.write("MinRank1 统计结果:\n")
#             f.write(f"值为 1 的数量: {stats['min_rank1']['1']}\n")
#             f.write(f"值小于 3 的数量: {stats['min_rank1']['<3']}\n")
#             f.write(f"值小于 5 的数量: {stats['min_rank1']['<5']}\n")
#
#             f.write("\nMinRank2 统计结果:\n")
#             f.write(f"值为 1 的数量: {stats['min_rank2']['1']}\n")
#             f.write(f"值小于 3 的数量: {stats['min_rank2']['<3']}\n")
#             f.write(f"值小于 5 的数量: {stats['min_rank2']['<5']}\n")
#
#         # 总体统计
#         f.write(f"\n{'=' * 30} 总体统计 {'=' * 30}\n")
#         f.write("MinRank1 总计:\n")
#         f.write(f"值为 1 的总数: {total_stats['min_rank1']['1']}\n")
#         f.write(f"值小于 3 的总数: {total_stats['min_rank1']['<3']}\n")
#         f.write(f"值小于 5 的总数: {total_stats['min_rank1']['<5']}\n")
#         f.write(f"平均 MFR1: {total_stats['MFR1']:.5f}\n")
#
#         f.write("\nMinRank2 总计:\n")
#         f.write(f"值为 1 的总数: {total_stats['min_rank2']['1']}\n")
#         f.write(f"值小于 3 的总数: {total_stats['min_rank2']['<3']}\n")
#         f.write(f"值小于 5 的总数: {total_stats['min_rank2']['<5']}\n")
#         f.write(f"平均 MFR2: {total_stats['MFR2']:.5f}\n")
#
#     print(f"统计结果已保存到 {analysis_file}")
#
# if __name__ == "__main__":
#     proList = ["dstar2", "jaccard", "LLMAO_window", "MTL_transfer", "ochiai", "opt2", "tarantula", "transfer",
#                 "russell_rao","CodeHealer","XAI4FL"]
#     #proList = ["LLMAO_window"]
#     topNList= [1000]
#     Slice = "noSlice"
#     model = "incoder"
#     for pro in proList:
#         for topN in topNList:
#             # 输入路径
#             topN_path = f"/home/gwj/entrop/entropy-apr-replication/TopN/{pro}/top{topN}"
#             natural_path = f"/home/gwj/entrop/entropy-apr-replication/RQ2_final/natural/{Slice}/total/top{topN}/{model}"
#             # 输出路径
#             #multiply_path = f"/home/gwj/entrop/entropy-apr-replication/Multiply_Result_6b/noSlice/{pro}/top{topN}"
#             multiply_path = f"/home/gwj/entrop/entropy-apr-replication/RQ2_final/Deal_With_Result/{model}/{Slice}/基于排名的加权平均/{pro}/top{topN}"
#             # 合并文件
#             merge_files_with_weights(topN_path, natural_path, multiply_path,topN)#将错误定位的结果和熵进行相乘
#             buggy_lines_dir = f"/home/gwj/entrop/entropy-apr-replication/bug_line"
#             Experimen_Result = f"/home/gwj/entrop/entropy-apr-replication/RQ2_final/Experimen_Result/{model}/noSlice/{pro}/top{topN}"
#             os.makedirs(Experimen_Result, exist_ok=True)
#             result_analysis_big(multiply_path,topN_path,buggy_lines_dir,Experimen_Result)#生成结果文件
#             rank_file = f'/home/gwj/entrop/entropy-apr-replication/RQ2_final/Experimen_Result/{model}/noSlice/{pro}/top{topN}/基于排名的加权平均/Rank-based Weighted Average（基于排名的加权平均)_project_min_ranks({a},{b}).txt'
#             analysis_file = f'/home/gwj/entrop/entropy-apr-replication/RQ2_final/Experimen_Result/{model}/noSlice/{pro}/top{topN}/基于排名的加权平均/Rank-based Weighted Average（基于排名的加权平均)_result_proj({a},{b}).txt'
#             count135(rank_file,analysis_file)

import csv
import os
import re
from collections import defaultdict
from itertools import groupby
import sys
import pandas as pd

# --- 1. 全局配置 ---
a = 0.6  # 可疑度相乘的权重
b = 0.4  # 排名的权重


# --- 2. 核心数据融合函数 ---
def process_files(file1, file2, topN):
    """处理文件并根据分数和排名进行加权评分"""
    # 读取 file1 (stmt-susps.txt)
    raw_data1 = []
    original_order = []
    with open(file1, 'r', errors='ignore') as f:
        for line in f:
            if line.strip() and ',' in line:
                try:
                    key, value = line.rsplit(',', 1)
                    original_key = key.strip().replace('/', '.')
                    raw_data1.append((original_key, float(value.strip())))
                    original_order.append(original_key)
                except ValueError:
                    print(f"[警告] 文件 {file1} 中的值无效: {value}")

    original_positions = {key: idx for idx, key in enumerate(original_order)}
    sorted_data1 = sorted(raw_data1, key=lambda x: x[1], reverse=True)
    rank1 = {key: idx + 1 for idx, (key, _) in enumerate(sorted_data1)}
    data1 = dict(raw_data1)

    # 归一化 data1
    if data1:
        values = list(data1.values())
        min_val, max_val = min(values), max(values)
        if min_val == max_val:
            data1 = {k: 0.5 for k in data1}
        else:
            data1 = {k: (v - min_val) / (max_val - min_val) for k, v in data1.items()}

    # 读取 file2 (entropy.txt)
    raw_data2 = []
    if not (os.path.exists(file2) and os.path.getsize(file2) > 0):
        data2 = {}
    else:
        with open(file2, 'r', errors='ignore') as f:
            for line in f:
                if line.strip() and ',' in line:
                    try:
                        key, value = line.rsplit(',', 1)
                        key = key.replace('/', '.').strip()
                        raw_data2.append((key, float(value.strip())))
                    except ValueError:
                        print(f"[警告] 文件 {file2} 中的值无效: {value}")

    sorted_data2 = sorted(raw_data2, key=lambda x: x[1], reverse=True)
    rank2 = {key: idx + 1 for idx, (key, _) in enumerate(sorted_data2)}
    data2 = dict(raw_data2)

    # 归一化 data2
    if data2:
        values = list(data2.values())
        min_val, max_val = min(values), max(values)
        if min_val == max_val:
            data2 = {k: 0.5 for k in data2}
        else:
            data2 = {k: (v - min_val) / (max_val - min_val) for k, v in data2.items()}

    # 融合
    final_scores = {}
    all_keys = set(original_order)  # 只处理原始sus文件中的key

    for key in all_keys:
        val1 = data1.get(key, 0)
        val2 = data2.get(key, 0)  # 如果entropy.txt中没有，默认为0
        r1 = rank1.get(key, topN + 1)
        r2 = rank2.get(key, topN + 1)

        # 应用您的复杂公式
        # 为防止 0 的 0.1 次方等数学问题，给 val2 加一个极小数
        epsilon = 1e-9
        score_part = val1  * val2 * a
        rank_part = b * (1 / r1 + 1 / r2)
        final_scores[key] = score_part + rank_part

    # 排序
    sorted_items = sorted(
        final_scores.items(),
        key=lambda x: (-x[1], original_positions.get(x[0], len(original_order) + 1))
    )
    return dict(sorted_items)


# --- 3. 排名与评估的辅助函数 ---

def extract_project_info(project_id):
    """从项目ID中提取前缀和数字"""
    match = re.match(r"([A-Za-z]+)(\d+)", project_id)
    if match:
        return (match.group(1), int(match.group(2)))
    return (project_id, 0)


def read_rankings_from_dict(scores_dict):
    """从已排序的分数字典直接创建排名映射。"""
    return {stmt: rank for rank, stmt in enumerate(scores_dict.keys(), 1)}


def read_rankings_from_file(file_path):
    """从stmt-susps.txt文件读取、排序并创建排名映射。"""
    if not os.path.exists(file_path): return {}
    entries = []
    with open(file_path, 'r', errors='ignore') as f:
        for line in f:
            if ',' in line:
                try:
                    stmt, score = line.rsplit(',', 1)
                    entries.append((stmt.strip().replace('/', '.'), float(score.strip())))
                except ValueError:
                    continue
    sorted_entries = sorted(entries, key=lambda x: x[1], reverse=True)
    return {stmt: rank for rank, (stmt, _) in enumerate(sorted_entries, 1)}


def get_min_ranks(rankings, buggy_lines):
    """从排名映射中为一组错误行计算MinRank。"""
    valid_ranks = [rankings.get(stmt, -1) for stmt in buggy_lines]
    valid_ranks = [r for r in valid_ranks if r != -1]
    return min(valid_ranks) if valid_ranks else -1


def count_ranks(file_path):
    """读取MinRank对比文件并统计TopN和MFR。"""
    project_stats = defaultdict(lambda: {'now': {'1': 0, '<3': 0, '<5': 0}, 'before': {'1': 0, '<3': 0, '<5': 0}})
    total_stats = {'now': {'1': 0, '<3': 0, '<5': 0}, 'before': {'1': 0, '<3': 0, '<5': 0}, 'sum_now': 0,
                   'sum_before': 0, 'count': 0}

    with open(file_path, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            project_name = ''.join([c for c in row['Project'] if not c.isdigit()])
            rank_now = int(row['now'])
            rank_before = int(row['before'])

            # 更新项目统计
            if rank_now == 1: project_stats[project_name]['now']['1'] += 1
            if 0 < rank_now <= 3: project_stats[project_name]['now']['<3'] += 1
            if 0 < rank_now <= 5: project_stats[project_name]['now']['<5'] += 1

            if rank_before == 1: project_stats[project_name]['before']['1'] += 1
            if 0 < rank_before <= 3: project_stats[project_name]['before']['<3'] += 1
            if 0 < rank_before <= 5: project_stats[project_name]['before']['<5'] += 1

            # 更新总统计
            if rank_before != -1:  # 只统计基线有效的数据
                if rank_now == 1: total_stats['now']['1'] += 1
                if 0 < rank_now <= 3: total_stats['now']['<3'] += 1
                if 0 < rank_now <= 5: total_stats['now']['<5'] += 1
                total_stats['sum_now'] += rank_now if rank_now != -1 else rank_before  # 填充-1

                if rank_before == 1: total_stats['before']['1'] += 1
                if 0 < rank_before <= 3: total_stats['before']['<3'] += 1
                if 0 < rank_before <= 5: total_stats['before']['<5'] += 1
                total_stats['sum_before'] += rank_before
                total_stats['count'] += 1

    total_stats['MFR_now'] = total_stats['sum_now'] / total_stats['count'] if total_stats['count'] > 0 else 0
    total_stats['MFR_before'] = total_stats['sum_before'] / total_stats['count'] if total_stats['count'] > 0 else 0
    return project_stats, total_stats


def count135(rank_file, analysis_file):
    """根据MinRank文件生成最终的分析报告。"""
    project_stats, total_stats = count_ranks(rank_file)
    with open(analysis_file, 'w') as f:
        # ... (与您之前的count135写入逻辑相同，但变量名已更新)
        f.write(f"--- 总体统计 ---\n")
        f.write("融合后 (now) 总计:\n")
        f.write(f"Top-1: {total_stats['now']['1']}\n")
        f.write(f"Top-3: {total_stats['now']['<3']}\n")
        f.write(f"Top-5: {total_stats['now']['<5']}\n")
        f.write(f"MFR: {total_stats['MFR_now']:.5f}\n\n")

        f.write("基线 (before) 总计:\n")
        f.write(f"Top-1: {total_stats['before']['1']}\n")
        f.write(f"Top-3: {total_stats['before']['<3']}\n")
        f.write(f"Top-5: {total_stats['before']['<5']}\n")
        f.write(f"MFR: {total_stats['MFR_before']:.5f}\n")
    print(f"统计结果已保存到 {analysis_file}")


# --- 4. 主程序入口 ---
if __name__ == "__main__":
    proList = ["dstar2", "jaccard", "LLMAO_window", "MTL_transfer", "ochiai", "opt2", "rogot1", "tarantula", "transfer",
               "rogers_tanimoto", "russell_rao", "CodeHealer", "XAI4FL"]
    topNList = [1000]
    model = "incoder"
    Slice = "noSlice"

    # --- 预加载所有buggy lines数据 ---
    buggy_lines_dir = "/home/gwj/entrop/entropy-apr-replication/bug_line"
    buggy_lines_map = defaultdict(list)
    for project_type in ["Chart", "Lang", "Math", "Closure", "Mockito", "Time"]:
        buggy_base = os.path.join(buggy_lines_dir, project_type)
        if not os.path.isdir(buggy_base): continue
        for buggy_file in os.listdir(buggy_base):
            if buggy_file.endswith(".buggy.lines"):
                bug_id = buggy_file.split('.')[0]
                with open(os.path.join(buggy_base, buggy_file), 'r', errors='ignore') as f:
                    buggy_lines_map[bug_id] = [line.strip().replace('/', '.') for line in f if line.strip()]

    for pro in proList:
        for topN in topNList:
            print(f"\n{'=' * 20} Processing: {pro}, topN={topN}, model={model} {'=' * 20}")

            # --- 在内存中收集所有版本的融合结果和基线结果 ---
            all_fused_scores = {}
            all_baseline_scores = {}

            base_loop_path = f"/home/gwj/entrop/entropy-apr-replication/TopN/{pro}/top{topN}"
            if not os.path.isdir(base_loop_path): continue

            for project in os.listdir(base_loop_path):
                project_path = os.path.join(base_loop_path, project)
                if not os.path.isdir(project_path): continue

                for version in os.listdir(project_path):
                    version_path = os.path.join(project_path, version)
                    if not os.path.isdir(version_path): continue

                    bug_id = f"{project}-{version}"

                    sus_file = os.path.join(version_path, "stmt-susps.txt")
                    natural_file = f"/home/gwj/entrop/entropy-apr-replication/RQ2_final/natural/{Slice}/total/top{topN}/{model}/{project}/{version}/entropy.txt"

                    if not os.path.exists(sus_file) or not os.path.exists(natural_file): continue

                    # 融合并存入内存
                    fused_scores = process_files(sus_file, natural_file, topN)
                    all_fused_scores[bug_id] = fused_scores

            # --- 在内存中进行评估 ---
            if all_fused_scores:
                all_rank_diffs = []
                for bug_id, fused_dict in all_fused_scores.items():
                    project, version = bug_id.split('-')
                    baseline_file = f"/home/gwj/entrop/entropy-apr-replication/TopN/{pro}/top{topN}/{project}/{version}/stmt-susps.txt"

                    fused_ranks = read_rankings_from_dict(fused_dict)
                    baseline_ranks = read_rankings_from_file(baseline_file)

                    buggy_lines = buggy_lines_map.get(bug_id, [])
                    if not buggy_lines: continue

                    min_rank_fused = get_min_ranks(fused_ranks, buggy_lines)
                    min_rank_baseline = get_min_ranks(baseline_ranks, buggy_lines)

                    # --- 应用您要求的特殊逻辑 ---
                    if min_rank_fused == -1 and min_rank_baseline != -1:
                        min_rank_fused = min_rank_baseline

                    diff = min_rank_baseline - min_rank_fused if min_rank_fused != -1 and min_rank_baseline != -1 else 0

                    all_rank_diffs.append({
                        "Project": bug_id,
                        "now": min_rank_fused,
                        "before": min_rank_baseline,
                        "Difference": diff
                    })

                # --- 保存最终需要的两个文件 ---
                Experimen_Result = f"/home/gwj/entrop/entropy-apr-replication/RQ2_final/Experimen_Result/{model}/noSlice/{pro}/top{topN}/基于排名的加权平均"
                os.makedirs(Experimen_Result, exist_ok=True)

                # 保存 project_min_ranks_stmt.txt
                rank_file = os.path.join(Experimen_Result,
                                         f"Rank-based Weighted Average（基于排名的加权平均)_project_min_ranks({a},{b}).txt")
                min_rank_df = pd.DataFrame(all_rank_diffs)
                min_rank_df.to_csv(rank_file, index=False)
                print(f"MinRank 文件已保存到: {rank_file}")

                # 保存 result_proj_stmt.txt
                analysis_file = os.path.join(Experimen_Result,
                                             f"Rank-based Weighted Average（基于排名的加权平均)_result_proj({a},{b}).txt")
                count135(rank_file, analysis_file)
    import shutil

    deal_with_result_dir = (
        "/home/gwj/entrop/entropy-apr-replication/"
        "RQ2_final/Deal_With_Result"
    )

    if os.path.exists(deal_with_result_dir):
        shutil.rmtree(deal_with_result_dir)
        print(f"已删除目录: {deal_with_result_dir}")