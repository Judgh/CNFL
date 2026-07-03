import os
from collections import defaultdict


def normalize_key(key):
    """统一键格式：将路径中的斜杠和#号统一为点"""
    return key.replace('/', '.').replace('#', '.').strip()


def load_bug_lines(bug_file):
    """加载.buggy.lines文件并标准化键格式"""
    bug_lines = set()
    with open(bug_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and '#' in line:
                normalized = normalize_key(line)
                bug_lines.add(normalized)
    return bug_lines


def analyze_ranking(copeland_file, bug_lines, top_list=[1, 3, 5]):
    """分析每个.buggy.lines文件中排名最靠前的bug行"""
    results = defaultdict(int)

    # 读取Copeland排名数据
    try:
        with open(copeland_file, 'r') as f:
            ranked_lines = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        return results

    # 建立 {key: rank} 映射
    rank_dict = {}
    for rank, line in enumerate(ranked_lines, 1):
        key = normalize_key(line.split(',')[0])
        rank_dict[key] = rank

    # 找出当前文件中所有bug行中的最小排名
    min_rank = float('inf')
    for bug_key in bug_lines:
        current_rank = rank_dict.get(bug_key, float('inf'))
        if current_rank < min_rank:
            min_rank = current_rank

    # 仅统计最小排名的行
    if min_rank != float('inf'):
        for n in top_list:
            if min_rank <= n:
                results[n] += 1  # 整个文件只统计一次

    return results


def process_project(project, copeland_root, bugline_root):
    """处理单个项目，返回 (汇总统计, 详细数据)"""
    summary_stats = defaultdict(lambda: {'top1': 0, 'top3': 0, 'top5': 0})
    detail_stats = defaultdict(dict)  # 存储详细数据 {version: {metric: count}}

    # 遍历bug_line目录
    bug_dir = os.path.join(bugline_root, project)
    copeland_dir = os.path.join(copeland_root, project)

    if not os.path.exists(bug_dir) or not os.path.exists(copeland_dir):
        return summary_stats, detail_stats

    # 处理每个.buggy.lines文件
    for bug_file in os.listdir(bug_dir):
        if not bug_file.endswith('.buggy.lines'):
            continue

        # 提取版本号
        try:
            _, version_part = bug_file.split('-')
            version = version_part.split('.')[0]
        except ValueError:
            continue

        # 加载bug行
        bug_path = os.path.join(bug_dir, bug_file)
        bug_lines = load_bug_lines(bug_path)
        if not bug_lines:
            continue

        # 加载对应copeland结果
        copeland_path = os.path.join(copeland_dir, version, 'stmt-susps.txt')
        if not os.path.exists(copeland_path):
            continue

        # 分析排名（每个文件只统计一次）
        ranking = analyze_ranking(copeland_path, bug_lines)

        # 累加汇总统计
        summary_stats[version]['top1'] += ranking.get(1, 0)
        summary_stats[version]['top3'] += ranking.get(3, 0)
        summary_stats[version]['top5'] += ranking.get(5, 0)

        # 记录详细数据
        detail_stats[version] = {
            'top1': ranking.get(1, 0),
            'top3': ranking.get(3, 0),
            'top5': ranking.get(5, 0)
        }

    return summary_stats, detail_stats


def main():
    #projList = ["dstar2", "jaccard", "LLMAO", "MTL_transfer", "ochiai", "opt2", "rogot1", "tarantula", "transfer"]
    projList = [
        "dstar2", "jaccard", "LLMAO", "MTL_transfer", "ochiai",
        "opt2", "rogot1", "tarantula", "transfer", "rogers_tanimoto",
        "russell_rao", "CodeHealer", "XAI4FL"
    ]
    #projList = ["dstar2"]
    #topNList = [10, 20, 30, 50, 100]
    topNList = [10]
    model = "deepseekcoder"

    # 基础路径
    base_output_dir = f"/home/gwj/entrop/entropy-apr-replication/实验结果/{model}/noSlice/CopelandFusion"

    for technique in projList:
        for topN in topNList:
            # 动态生成输出目录（例如：.../dstar2/top10）
            output_dir = os.path.join(base_output_dir, technique, f"top{topN}")
            os.makedirs(output_dir, exist_ok=True)  # 自动创建目录

            # 输入路径保持不变
            copeland_path = os.path.join(base_output_dir, technique, f"top{topN}")  # 原数据路径
            bugline_path = "/home/gwj/entrop/entropy-apr-replication/bug_line"

            final_stats = defaultdict(lambda: {'top1': 0, 'top3': 0, 'top5': 0})
            projects = ["Chart", "Closure", "Lang", "Math", "Mockito", "Time"]
            all_details = {}  # 存储所有项目的详细数据

            # 处理项目...
            for project in projects:
                project_summary, project_detail = process_project(project, copeland_path, bugline_path)

                # 累加汇总统计
                for version in project_summary:
                    for metric in ['top1', 'top3', 'top5']:
                        final_stats[project][metric] += project_summary[version][metric]

                # 存储详细数据
                all_details[project] = project_detail

            # 写入统计汇总文件（statistics.txt）
            output_file = os.path.join(output_dir, "statistics1.txt")
            with open(output_file, 'w') as f:
                f.write(f"Technique: {technique}\n")
                f.write(f"TopN: {topN}\n\n")
                f.write(f"{'Project':<10} | {'Top1':<6} | {'Top3':<6} | {'Top5':<6}\n")
                f.write("-" * 35 + "\n")

                total_sums = {'top1': 0, 'top3': 0, 'top5': 0}
                for project in projects:
                    data = final_stats[project]
                    total_sums['top1'] += data['top1']
                    total_sums['top3'] += data['top3']
                    total_sums['top5'] += data['top5']
                    f.write(f"{project:<10} | {data['top1']:<6} | {data['top3']:<6} | {data['top5']:<6}\n")

                f.write("-" * 35 + "\n")
                f.write(
                    f"{'Total':<10} | {total_sums['top1']:<6} | {total_sums['top3']:<6} | {total_sums['top5']:<6}\n\n")

            # 写入详细文件（detail.txt）
            detail_file = os.path.join(output_dir, "detail.txt")
            with open(detail_file, 'w') as f:
                f.write(f"Technique: {technique}  TopN: {topN}\n\n")

                for project in projects:
                    f.write(f"=== Project: {project} ===\n")
                    f.write(f"{'Version':<10} | {'Top1':<6} | {'Top3':<6} | {'Top5':<6}\n")
                    f.write("-" * 35 + "\n")

                    # 获取该项目的所有版本数据（按版本号排序）
                    details = all_details.get(project, {})
                    for version in sorted(details.keys(), key=lambda x: int(x)):
                        data = details[version]
                        f.write(f"{version:<10} | {data['top1']:<6} | {data['top3']:<6} | {data['top5']:<6}\n")

                    f.write("\n")  # 项目间空行

            print(f"生成文件: {output_file} 和 {detail_file}")


if __name__ == "__main__":
    main()