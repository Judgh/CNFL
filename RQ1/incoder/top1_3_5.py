import os
import re
from collections import defaultdict
from pathlib import Path
import logging
import csv
from typing import List, Dict, Tuple

# --- 1. 配置 (Configuration) ---
# 将所有路径和可变参数放在开头，方便管理
BASE_PATH = Path("/home/gwj/entrop/entropy-apr-replication")
BUG_LINE_ROOT = BASE_PATH / "bug_line"
RQ1_RESULT_ROOT = BASE_PATH / "RQ1" / "result"

# 要评估的模型列表，方便未来扩展
MODELS_TO_EVALUATE = [
    "codebert",
    "codeT5plus",
    "incoder",
    "deepseekcoder",
    "qwen"
    # ... 在这里添加更多模型
]

PROJECTS = ["Chart", "Closure", "Lang", "Math", "Mockito", "Time"]
TOP_N_LIST = [1, 3, 5]  # 定义要统计的 Top-N 等级

# --- 2. 日志设置 (Logging Setup) ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(funcName)s] - %(message)s',
    handlers=[
        logging.StreamHandler()  # 直接输出到控制台
    ]
)


# --- 3. 核心功能函数 (Core Functions) ---

def load_buggy_lines(file_path: Path) -> Dict[int, str]:
    """
    加载 .buggy.lines 文件，返回一个 {行号: 完整行内容} 的字典。
    """
    buggy_lines = {}
    if not file_path.exists():
        logging.warning(f"Buggy lines file not found: {file_path}")
        return buggy_lines

    with file_path.open('r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            line = line.strip()
            match = re.search(r'#(\d+)$', line)
            if match:
                line_number = int(match.group(1))
                buggy_lines[line_number] = line
    return buggy_lines


def find_bug_rank_in_entropy_file(entropy_file: Path, buggy_line_numbers: set) -> int:
    """
    在给定的 entropy.txt 文件中查找一组缺陷行号，并返回其中排名最靠前的那个（MinRank）。
    返回 -1 如果所有缺陷行都未找到。
    """
    if not entropy_file.exists():
        logging.warning(f"Entropy file not found: {entropy_file}")
        return -1

    ranked_lines = []
    try:
        with entropy_file.open('r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if not line or ',' not in line or '#' not in line:
                    continue

                # 提取行号和分数
                match = re.search(r'#(\d+),([\d.-]+)$', line)
                if match:
                    line_num = int(match.group(1))
                    score = float(match.group(2))
                    ranked_lines.append({'line_num': line_num, 'score': score})
    except Exception as e:
        logging.error(f"Error reading or parsing {entropy_file}: {e}")
        return -1

    # 根据熵值（分数）降序排列，熵越高排名越靠前
    ranked_lines.sort(key=lambda x: x['score'], reverse=True)

    min_rank = float('inf')
    found = False

    # 建立 {行号: 排名} 的字典以便快速查找
    rank_map = {item['line_num']: rank for rank, item in enumerate(ranked_lines, 1)}

    for bug_num in buggy_line_numbers:
        rank = rank_map.get(bug_num, float('inf'))
        if rank < min_rank:
            min_rank = rank
            found = True

    return int(min_rank) if found else -1


# --- 4. 主处理流程 (Main Processing Logic) ---

def analyze_model_performance(model_name: str):
    """
    对单个模型的所有项目和缺陷版本进行性能分析。
    """
    logging.info(f"🚀 Starting analysis for model: {model_name}")

    model_result_path = RQ1_RESULT_ROOT / model_name
    if not model_result_path.is_dir():
        logging.error(f"Result directory for model '{model_name}' not found at: {model_result_path}")
        return None

    # 存储每个缺陷版本的 MinRank 结果
    all_bug_versions_results = []

    for project in PROJECTS:
        logging.info(f"--- Processing project: {project} ---")

        project_bug_line_dir = BUG_LINE_ROOT / project
        project_result_dir = model_result_path / project

        if not project_bug_line_dir.is_dir():
            logging.warning(f"Buggy line directory for {project} not found. Skipping.")
            continue

        for bug_file in project_bug_line_dir.glob('*.buggy.lines'):
            # 从文件名 'Chart-1.buggy.lines' 提取版本号 '1'
            match = re.search(r'-(\d+)\.buggy\.lines$', bug_file.name)
            if not match:
                continue
            bug_version = match.group(1)

            # 加载真实的缺陷行
            buggy_lines_map = load_buggy_lines(bug_file)
            if not buggy_lines_map:
                continue

            # 对应的结果文件路径
            entropy_file = project_result_dir / bug_version / "entropy.txt"

            # 查找 MinRank
            min_rank = find_bug_rank_in_entropy_file(entropy_file, set(buggy_lines_map.keys()))

            if min_rank != -1:
                all_bug_versions_results.append({
                    "model": model_name,
                    "project": project,
                    "version": int(bug_version),
                    "min_rank": min_rank
                })

    return all_bug_versions_results


def generate_summary_report(all_results: List[Dict], output_dir: Path):
    """
    根据所有缺陷版本的 MinRank 结果，生成最终的汇总统计报告。
    """
    if not all_results:
        logging.warning("No results to summarize. Report generation skipped.")
        return

    output_dir.mkdir(parents=True, exist_ok=True)
    model_name = all_results[0]['model']

    # 准备统计数据结构
    stats = defaultdict(lambda: {n: 0 for n in TOP_N_LIST})
    project_bug_counts = defaultdict(int)

    for result in all_results:
        project = result['project']
        rank = result['min_rank']
        project_bug_counts[project] += 1

        for n in TOP_N_LIST:
            if rank <= n:
                stats[project][n] += 1

    # --- 写入 CSV 格式的详细报告 ---
    csv_detail_path = output_dir / f"{model_name}_min_rank_details.csv"
    all_results.sort(key=lambda x: (x['project'], x['version']))
    with csv_detail_path.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=all_results[0].keys())
        writer.writeheader()
        writer.writerows(all_results)
    logging.info(f"Detailed MinRank results saved to: {csv_detail_path}")

    # --- 写入 TXT 格式的汇总报告 ---
    txt_summary_path = output_dir / f"{model_name}_top_n_summary.txt"
    with txt_summary_path.open('w', encoding='utf-8') as f:
        f.write(f"===== Performance Summary for Model: {model_name} =====\n\n")

        header = f"{'Project':<12}" + "".join([f" | Top-{n:<4}" for n in TOP_N_LIST])
        f.write(header + "\n")
        f.write("-" * len(header) + "\n")

        total_stats = {n: 0 for n in TOP_N_LIST}

        for project in PROJECTS:
            project_stats = stats[project]
            line = f"{project:<12}"
            for n in TOP_N_LIST:
                count = project_stats.get(n, 0)
                total_stats[n] += count
                line += f" | {count:<4}"
            f.write(line + "\n")

        f.write("-" * len(header) + "\n")

        total_line = f"{'Total':<12}"
        for n in TOP_N_LIST:
            total_line += f" | {total_stats[n]:<4}"
        f.write(total_line + "\n\n")

        f.write("--- Projects with Top-N Hits ---\n")
        for n in TOP_N_LIST:
            hit_projects = [res['project'] + '-' + str(res['version']) for res in all_results if res['min_rank'] <= n]
            f.write(f"Hits within Top-{n} ({len(hit_projects)}): {', '.join(sorted(hit_projects))}\n")

    logging.info(f"Summary report saved to: {txt_summary_path}")
#现在是否需要构建每个版本的错误，如果不构建，下一步应该怎么办
#不需要构建

# --- 5. 脚本入口 (Script Entrypoint) ---
def main():
    """主函数，驱动所有模型的评估。"""
    for model in MODELS_TO_EVALUATE:
        results = analyze_model_performance(model)
        if results:
            # 定义该模型的输出目录
            output_directory = BASE_PATH / "RQ1_Analysis" / model
            generate_summary_report(results, output_directory)


if __name__ == "__main__":
    main()