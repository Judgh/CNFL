import csv
import os
import re
from collections import defaultdict
from itertools import groupby
import sys


def merge_files_with_weights(input_dir1, input_dir2, output_dir):
    """
    将 input_dir1(topN) 和 input_dir2(natural) 中的文件进行合并，并将结果保存到 output_dir 中。
    """
    # 检查输入路径是否存在
    if not os.path.exists(input_dir1):
        print(f"[错误] 输入目录1不存在: {input_dir1}")
        return
    if not os.path.exists(input_dir2):
        print(f"[错误] 输入目录2不存在: {input_dir2}")
        return

    # 遍历 input_dir1 中的目录结构
    for root, dirs, files in os.walk(input_dir1):
        # 获取相对路径（相对于 input_dir1）
        relative_path = os.path.relpath(root, input_dir1)

        # 遍历文件
        for file in files:
            if file == "stmt-susps.txt":
                # 构建输入文件路径
                file_path1 = os.path.join(root, file)  # input_dir1 中的 stmt-susps.txt
                file_path2 = os.path.join(input_dir2, relative_path, "entropy.txt")  # input_dir2 中的 entropy.txt

                # 检查文件是否存在
                if not os.path.exists(file_path2):
                    print(f"[警告] 文件 {file_path2} 不存在，跳过该文件")
                    sys.exit(1)

                # 构建输出路径
                output_path = os.path.join(output_dir, relative_path, file)
                os.makedirs(os.path.dirname(output_path), exist_ok=True)

                # 处理合并
                merged_data = process_files(file_path1, file_path2)
                print(f"合并结果保存到: {output_path}")

                # 写入结果
                with open(output_path, 'w') as f_out:
                    for key, value in merged_data.items():
                        f_out.write(f"{key},{value:.10f}\n")


# def process_files(file1, file2):
#     # 读取文件1（stmt-susps.txt）
#     data1 = defaultdict(float)
#     with open(file1, 'r') as f:
#         for line in f:
#             if line and ',' in line:
#                 key, value = line.rsplit(',', 1)
#                 key = key.replace('/', '.')  # 将 / 替换为 .
#                 try:
#                     data1[key.strip()] = float(value.strip())
#                 except ValueError:
#                     print(f"[错误] 文件 {file1} 的值无效: {value}")
#
#     data2 = defaultdict(float)
#     # 读取文件2（entropy.txt）
#     if os.path.getsize(file2) == 0:#当entropy.txt内容为空时：
#         result = {k: v*0 for k, v in data1.items()}
#         return dict(result)
#
#     with open(file2, 'r') as f:
#         for line in f:
#             if line and ',' in line:
#                 key, value = line.rsplit(',', 1)
#                 key = key.replace('/', '.')  # 将 / 替换为 .
#                 try:
#                     data2[key.strip()] = float(value.strip())
#                 except ValueError:
#                     print(f"[错误] 文件 {file2} 的值无效: {value}")
#     data2 = dict(data2)
#     # 合并数据
#     merged = defaultdict(float)
#     all_keys = set(data1.keys()).union(data2.keys())
#
#     for key in all_keys:
#         merged[key] = data1.get(key,0) * data2.get(key,0)  # 使用默认值 1.0
#     merged = dict(merged)
#     # 按值降序排序
#     return dict(sorted(merged.items(), key=lambda x: x[1], reverse=True))
def process_files(file1, file2):
    # 读取文件1（stmt-susps.txt）
    data1 = {}
    original_order = []  # 新增：记录原始键顺序
    with open(file1, 'r') as f:
        for line in f:
            if line and ',' in line:
                key, value = line.rsplit(',', 1)
                original_key = key.strip().replace('/', '.')
                try:
                    data1[original_key] = float(value.strip())
                    original_order.append(original_key)  # 记录原始顺序
                except ValueError:
                    print(f"[错误] 文件 {file1} 的值无效: {value}")
        # 新增：将data1的值归一化到0~1之间
    if data1:
        values = list(data1.values())
        min_val = min(values)
        max_val = max(values)
        # 处理所有值相同的情况（避免除以0）
        if min_val == max_val:
            # 所有值设为中间值1.0（0~2的中间点）
            for key in data1:
                data1[key] = 1.0
        else:
            # 归一化公式：value = (原值 - min) / (max - min) + 0
            for key in data1:
                data1[key] = ((data1[key] - min_val) / (max_val - min_val))

    data2 = defaultdict(float)
    # 读取文件2（entropy.txt）
    if os.path.getsize(file2) == 0:
        result = {k: v * 0 for k, v in data1.items()}
        return dict(result)

    with open(file2, 'r') as f:
        for line in f:
            if line and ',' in line:
                key, value = line.rsplit(',', 1)
                key = key.replace('/', '.')
                try:
                    data2[key.strip()] = float(value.strip())
                except ValueError:
                    print(f"[错误] 文件 {file2} 的值无效: {value}")

    # 新增：对data2进行0-1归一化
    if data2:
        values = list(data2.values())
        min_val = min(values)
        max_val = max(values)
        # 处理所有值相同的情况（避免除以0）
        if min_val == max_val:
            # 如果全部值相同，统一设为0.5（中性值）
            normalized_value = 0.5
            for key in data2:
                data2[key] = normalized_value
        else:
            for key in data2:
                data2[key] = (data2[key] - min_val) / (max_val - min_val)

    data2 = dict(data2)
    # 合并数据
    # merged = defaultdict(float)
    # all_keys = set(data1.keys()).union(data2.keys())
    #
    # for key in all_keys:
    #     #merged[key] = data1.get(key, 0) * data2.get(key, 0)
    #     merged[key] = data1.get(key, 0) * data2.get(key, 0)
    # merged = dict(merged)
    # x = dict(sorted(merged.items(), key=lambda x: x[1], reverse=True))
    # # 按值降序排序
    # return x
    merged = defaultdict(float)
    all_keys = set(data1.keys()).union(data2.keys())

    # 创建字典记录每个key在data1中的原始位置
    original_positions = {key: idx for idx, key in enumerate(original_order)}

    # 合并时记录每个key的原始位置
    merged_with_pos = []
    for key in all_keys:
        value = (data1.get(key, 0)**0.7) * (data2.get(key, 0)**0.3)
        #value = (0.8*(data1.get(key, 0)) +(0.2*data2.get(key, 0)))**0.5
        #value = data1.get(key, 0)*data2.get(key, 0)
        pos = original_positions.get(key, len(original_order))  # 不在data1中的key放在最后
        merged_with_pos.append((key, value, pos))

    # 排序：先按值降序，值相同则按原始位置升序
    sorted_items = sorted(merged_with_pos,
                          key=lambda x: (-x[1], x[2]))  # 负号实现降序

    # 返回排序后的字典
    return {item[0]: item[1] for item in sorted_items}

def extract_project_info(project_id):
    """从项目ID中提取前缀和数字（例如 'Chart19' → ('Chart', 19)）"""
    match = re.match(r"([A-Za-z]+)(\d+)", project_id)
    if match:
        return (match.group(1), int(match.group(2)))
    return (project_id, 0)  # 默认处理
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
def read_rankings(file_path):
    """读取stmt-susps.txt文件并返回{类名: 排名}的字典（按文件顺序分配排名）"""
    if not os.path.exists(file_path):
        return {}

    with open(file_path, 'r') as f:
        lines = [line.strip() for line in f if line.strip()]

    if lines and lines[0].startswith("Statement,Suspiciousness"):
        lines = lines[1:]

    entries = []
    for line in lines:
        if ',' in line:
            parts = line.rsplit(',', 1)
            if len(parts) == 2:
                stmt, score = parts
                try:
                    # 保留原始顺序，直接记录语句
                    entries.append((stmt.strip(), float(score.strip())))
                except ValueError:
                    continue

    # 直接按读取顺序分配排名（从1开始）
    return {stmt: rank for rank, (stmt, _) in enumerate(entries, 1)}
def process_project(project, buggy_lines_file, sbfl_dir1, sbfl_dir2):
    """处理单个项目，返回结果列表"""
    results = []
    project_type, number_part = project.split('-')
    number = int(number_part.split('.')[0])
    project_id = f"{project_type}{number}"

    dir1_file = os.path.join(sbfl_dir1, project_type, str(number), "stmt-susps.txt")
    dir2_file = os.path.join(sbfl_dir2, project_type, str(number), "stmt-susps.txt")

    rankings1 = read_rankings(dir1_file)
    rankings2 = read_rankings(dir2_file)

    with open(buggy_lines_file, 'r', errors='ignore') as f:
        buggy_lines = [line.strip() for line in f if line.strip()]

    for stmt in buggy_lines:
        rank1 = rankings1.get(stmt, -1)
        rank2 = rankings2.get(stmt, -1)

        if rank1 == -1 and rank2 == -1:
            continue

        # 计算差值：rank2 - rank1
        diff = rank2 - rank1 if (rank1 != -1 and rank2 != -1) else -1

        results.append({
            "project_id": project_id,
            "stmt": stmt,
            "rank1": rank1,
            "rank2": rank2,
            "diff": diff,
            "type": project_type,
            "number": number
        })

    return results

def result_analysis_big(multiply_path,topN_path,buggy_lines_dir,output_dir):
    all_results = []
    # 处理所有项目
    for project_type in ["Chart", "Lang", "Math", "Closure", "Mockito", "Time"]:
        buggy_base = os.path.join(buggy_lines_dir, project_type)
        for buggy_file in os.listdir(buggy_base):
            if buggy_file.endswith(".buggy.lines"):
                full_path = os.path.join(buggy_base, buggy_file)
                project_name = buggy_file.split('.')[0]
                results = process_project(
                    project=project_name,
                    buggy_lines_file=full_path,
                    sbfl_dir1=multiply_path,
                    sbfl_dir2=topN_path
                )
                all_results.extend(results)
    all_results.sort(key=lambda x: (x["type"], x["number"]))

    # 写入原始明细文件
    output_file = os.path.join(output_dir, "rank_differences1.txt")
    with open(output_file, 'w') as f:
        f.write("Project,Statement,Rank1,Rank2,Difference\n")
        for entry in all_results:
            line = f"{entry['project_id']},{entry['stmt']},{entry['rank1']},{entry['rank2']},{entry['diff']}\n"
            f.write(line)

    # 新增：按项目合并统计最小值
    # 按project_id和number分组
    sorted_for_grouping = sorted(all_results, key=lambda x: (x["project_id"], x["number"]))
    grouped_results = groupby(sorted_for_grouping, key=lambda x: (x["project_id"], x["number"]))

    merged_project_stats = []
    for (project_id, number), group in grouped_results:
        group_list = list(group)

        # 收集有效rank
        valid_rank1 = [item["rank1"] for item in group_list if item["rank1"] != -1]
        valid_rank2 = [item["rank2"] for item in group_list if item["rank2"] != -1]

        # 计算最小值
        min_rank1 = min(valid_rank1) if valid_rank1 else -1
        min_rank2 = min(valid_rank2) if valid_rank2 else -1

        # 计算差值（仅当两者都有有效值时）
        diff = min_rank2 - min_rank1 if (min_rank1 != -1 and min_rank2 != -1) else -1

        merged_project_stats.append({
            "project_id": project_id,
            "min_rank1": min_rank1,
            "min_rank2": min_rank2,
            "diff": diff,
            "number": number
        })

    # 按项目类型和数字排序
    merged_project_stats.sort(key=lambda x: (extract_project_info(x["project_id"])[0], x["number"]))

    # 写入合并统计文件
    merged_output_file = os.path.join(output_dir, "归一化相乘加上次方参数/project_min_ranks_stmt0-1.txt")
    # 确保目录存在（自动创建所有不存在的父目录）
    os.makedirs(os.path.dirname(merged_output_file), exist_ok=True)
    with open(merged_output_file, 'w') as f:
        f.write("Project,MinRank1,MinRank2,Difference\n")
        for stat in merged_project_stats:
            line = f"{stat['project_id']},{stat['min_rank1']},{stat['min_rank2']},{stat['diff']}\n"
            f.write(line)

    print(f"处理完成！原始结果保存至: {output_file}")
    print(f"合并统计保存至: {merged_output_file}")

def count_ranks(file_path):
    # 初始化数据结构
    project_stats = defaultdict(lambda: {
        'min_rank1': {'1': 0, '<3': 0, '<5': 0},
        'min_rank2': {'1': 0, '<3': 0, '<5': 0}
    })

    total_stats = {
        'min_rank1': {'1': 0, '<3': 0, '<5': 0},
        'min_rank2': {'1': 0, '<3': 0, '<5': 0},
        'sum1': 0,
        'sum2': 0,
        'count': 0
    }

    with open(file_path, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            # 解析项目名称（例如 Chart3 -> Chart）
            project_name = ''.join([c for c in row['Project'] if not c.isdigit()])

            rank1 = int(row['MinRank1'])
            rank2 = int(row['MinRank2'])

            # 更新项目统计（仅计数）
            update_project_stats(project_stats[project_name], rank1, rank2)
            # 更新总统计（包含求和）
            update_total_stats(total_stats, rank1, rank2)

    # 计算总MFR
    total_stats['MFR1'] = total_stats['sum1'] / total_stats['count'] if total_stats['count'] > 0 else 0
    total_stats['MFR2'] = total_stats['sum2'] / total_stats['count'] if total_stats['count'] > 0 else 0

    return project_stats, total_stats

def update_project_stats(proj_stats, rank1, rank2):
    """ 更新子项目统计（仅计数） """
    # MinRank1
    if rank1 == 1:
        proj_stats['min_rank1']['1'] += 1
    if 0 < rank1 <= 3:
        proj_stats['min_rank1']['<3'] += 1
    if 0 < rank1 <= 5:
        proj_stats['min_rank1']['<5'] += 1

    # MinRank2
    if rank2 == 1:
        proj_stats['min_rank2']['1'] += 1
    if 0 < rank2 <= 3:
        proj_stats['min_rank2']['<3'] += 1
    if 0 < rank2 <= 5:
        proj_stats['min_rank2']['<5'] += 1


def update_total_stats(total_stats, rank1, rank2):
    """ 更新总统计（包含求和） """
    # MinRank1
    if rank1 == 1:
        total_stats['min_rank1']['1'] += 1
    if 0 < rank1 <= 3:
        total_stats['min_rank1']['<3'] += 1
    if 0 < rank1 <= 5:
        total_stats['min_rank1']['<5'] += 1
    total_stats['sum1'] += rank1

    # MinRank2
    if rank2 == 1:
        total_stats['min_rank2']['1'] += 1
    if 0 < rank2 <= 3:
        total_stats['min_rank2']['<3'] += 1
    if 0 < rank2 <= 5:
        total_stats['min_rank2']['<5'] += 1
    total_stats['sum2'] += rank2

    total_stats['count'] += 1
def count135(rank_file,analysis_file):
    project_stats, total_stats = count_ranks(rank_file)

    with open(analysis_file, 'w') as f:
        # 各子项目统计
        for proj_name, stats in project_stats.items():
            f.write(f"\n======= {proj_name} 项目统计 =======\n")
            f.write("MinRank1 统计结果:\n")
            f.write(f"值为 1 的数量: {stats['min_rank1']['1']}\n")
            f.write(f"值小于 3 的数量: {stats['min_rank1']['<3']}\n")
            f.write(f"值小于 5 的数量: {stats['min_rank1']['<5']}\n")

            f.write("\nMinRank2 统计结果:\n")
            f.write(f"值为 1 的数量: {stats['min_rank2']['1']}\n")
            f.write(f"值小于 3 的数量: {stats['min_rank2']['<3']}\n")
            f.write(f"值小于 5 的数量: {stats['min_rank2']['<5']}\n")

        # 总体统计
        f.write(f"\n{'=' * 30} 总体统计 {'=' * 30}\n")
        f.write("MinRank1 总计:\n")
        f.write(f"值为 1 的总数: {total_stats['min_rank1']['1']}\n")
        f.write(f"值小于 3 的总数: {total_stats['min_rank1']['<3']}\n")
        f.write(f"值小于 5 的总数: {total_stats['min_rank1']['<5']}\n")
        f.write(f"平均 MFR1: {total_stats['MFR1']:.5f}\n")

        f.write("\nMinRank2 总计:\n")
        f.write(f"值为 1 的总数: {total_stats['min_rank2']['1']}\n")
        f.write(f"值小于 3 的总数: {total_stats['min_rank2']['<3']}\n")
        f.write(f"值小于 5 的总数: {total_stats['min_rank2']['<5']}\n")
        f.write(f"平均 MFR2: {total_stats['MFR2']:.5f}\n")

    print(f"统计结果已保存到 {analysis_file}")

if __name__ == "__main__":
    proList = ["dstar2", "jaccard", "LLMAO_window", "MTL_transfer", "ochiai", "opt2", "rogot1", "tarantula", "transfer",
                "rogers_tanimoto", "russell_rao", "CodeHealer","XAI4FL"]
    #proList = ["XAI4FL"]
    #topNList= [10,20,30,50,100]
    topNList = [1000]
    Slice = "noSlice"
    model = "codebert"
    for pro in proList:
        for topN in topNList:
            # 输入路径
            topN_path = f"/home/gwj/entrop/entropy-apr-replication/TopN/{pro}/top{topN}"
            natural_path = f"/home/gwj/entrop/entropy-apr-replication/RQ2_final/natural/{Slice}/total/top{topN}/{model}"
            # 输出路径
            #multiply_path = f"/home/gwj/entrop/entropy-apr-replication/Multiply_Result_6b/noSlice/{pro}/top{topN}"
            multiply_path = f"/home/gwj/entrop/entropy-apr-replication/RQ2_final/Deal_With_Result/{model}/{Slice}/归一化相乘加上次方参数/{pro}/top{topN}"
            # 合并文件
            merge_files_with_weights(topN_path, natural_path, multiply_path)#将错误定位的结果和熵进行相乘
            buggy_lines_dir = f"/home/gwj/entrop/entropy-apr-replication/bug_line"
            Experimen_Result = f"/home/gwj/entrop/entropy-apr-replication/RQ2_final/Experimen_Result/{model}/noSlice/{pro}/top{topN}"
            os.makedirs(Experimen_Result, exist_ok=True)
            result_analysis_big(multiply_path,topN_path,buggy_lines_dir,Experimen_Result)#生成结果文件
            rank_file = f'/home/gwj/entrop/entropy-apr-replication/RQ2_final/Experimen_Result/{model}/noSlice/{pro}/top{topN}/归一化相乘加上次方参数/project_min_ranks_stmt0-1.txt'
            analysis_file = f'/home/gwj/entrop/entropy-apr-replication/RQ2_final/Experimen_Result/{model}/noSlice/{pro}/top{topN}/归一化相乘加上次方参数/result_proj_stmt0-1.txt'
            count135(rank_file,analysis_file)
    import shutil

    deal_with_result_dir = (
        "/home/gwj/entrop/entropy-apr-replication/"
        "RQ2_final/Deal_With_Result"
    )

    if os.path.exists(deal_with_result_dir):
        shutil.rmtree(deal_with_result_dir)
        print(f"已删除目录: {deal_with_result_dir}")