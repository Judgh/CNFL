import os
import re
import logging
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

# --- 1. 配置 (Configuration) ---
# 将所有可配置的参数放在开头，方便修改
LOG_FILE = 'copeland_fusion.log'
BASE_PATH = Path("/home/gwj/entrop/entropy-apr-replication")

# --- 2. 日志设置 (Logging Setup) ---
# 配置日志，使其能同时输出到文件和控制台
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(funcName)s] - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, mode='w'),  # 每次运行覆盖日志
        logging.StreamHandler()
    ]
)


# --- 3. 核心功能函数 (Core Functions) ---

def normalize_key(key: str) -> str:
    """
    Normalizes a statement key by replacing path separators with dots.
    Example: 'com/example/MyClass#myMethod#42' -> 'com.example.MyClass#myMethod#42'
    """
    if '#' not in key:
        logging.warning(f"Key '{key}' is missing the '#' separator. Returning as is.")
        return key

    class_part, line_part = key.split('#', 1)
    # Replace all slashes and backslashes with dots
    normalized_class = re.sub(r'[/\\]+', '.', class_part)
    return f"{normalized_class}#{line_part}"


def load_suspicion_file(file_path: Path) -> Dict[str, float]:
    """
    Loads a suspicion file (stmt-susps.txt or entropy.txt) and returns a
    dictionary of {normalized_key: score}. It handles duplicate keys by
    keeping the one with the highest score.
    """
    scores: Dict[str, float] = {}
    if not file_path.exists():
        logging.warning(f"File not found: {file_path}. Returning empty scores.")
        return scores

    try:
        with file_path.open('r', encoding='utf-8', errors='ignore') as f:
            for i, line in enumerate(f, 1):
                line = line.strip()
                if not line or ',' not in line:
                    continue

                raw_key, score_str = line.rsplit(',', 1)
                try:
                    score = float(score_str)
                    key = normalize_key(raw_key)

                    # If key exists, keep the higher score. Otherwise, add it.
                    if key not in scores or score > scores[key]:
                        scores[key] = score
                except ValueError:
                    logging.warning(f"Invalid score on line {i} in {file_path}: '{score_str}'")
                    continue
        logging.info(f"Successfully loaded {len(scores)} entries from {file_path}")
        return scores
    except Exception as e:
        logging.error(f"Failed to read or process {file_path}: {e}", exc_info=True)
        return {}


def compute_copeland_scores(ranking1: List[str], ranking2: List[str]) -> Dict[str, int]:
    """
    Computes Copeland scores for a set of items based on two rankings.
    An item's score is the number of other items it wins against minus the number it loses against.
    A win requires consensus from both rankers.
    """
    # Create a dictionary for quick rank lookup. Lower index = better rank.
    rank_map1 = {item: i for i, item in enumerate(ranking1)}
    rank_map2 = {item: i for i, item in enumerate(ranking2)}

    all_items = set(ranking1) | set(ranking2)
    scores = defaultdict(int)

    # Use a list for direct indexing, which is faster than set conversions
    items_list = list(all_items)
    n = len(items_list)

    for i in range(n):
        for j in range(i + 1, n):
            item_a = items_list[i]
            item_b = items_list[j]

            # Get ranks, defaulting to infinity if an item is not in a ranking
            rank_a1 = rank_map1.get(item_a, float('inf'))
            rank_b1 = rank_map1.get(item_b, float('inf'))

            rank_a2 = rank_map2.get(item_a, float('inf'))
            rank_b2 = rank_map2.get(item_b, float('inf'))

            # Determine winner based on consensus
            a_wins = (rank_a1 < rank_b1) and (rank_a2 < rank_b2)
            b_wins = (rank_b1 < rank_a1) and (rank_b2 < rank_a2)

            if a_wins:
                scores[item_a] += 1
                scores[item_b] -= 1
            elif b_wins:
                scores[item_a] -= 1
                scores[item_b] += 1
            # If it's a tie (split decision), scores remain unchanged (or both +0)

    return dict(scores)


# --- 4. 主处理流程 (Main Processing Logic) ---

def process_single_bug(fl_file: Path, natural_file: Path, output_file: Path, top_n: int):
    """
    Processes a single bug instance: loads data, computes Copeland scores,
    sorts the results, and writes to an output file.
    """
    logging.info(f"Processing pair: {fl_file.name} and {natural_file.name}")

    # 1. Load data
    fl_scores = load_suspicion_file(fl_file)
    natural_scores = load_suspicion_file(natural_file)

    if not fl_scores:
        logging.warning(f"FL scores are empty for {fl_file}. Cannot proceed.")
        return

    # 2. Create rankings based on scores (higher score is better)
    # The tie-breaking here is by key (alphabetical), which is a neutral choice.
    fl_ranking = sorted(fl_scores, key=lambda k: (-fl_scores[k], k))
    natural_ranking = sorted(natural_scores, key=lambda k: (-natural_scores[k], k))

    # 3. Compute Copeland scores
    copeland_scores = compute_copeland_scores(fl_ranking, natural_ranking)

    all_items = set(fl_scores.keys()) | set(natural_scores.keys())

    # 4. Final sort
    # Primary key: Copeland score (descending)
    # Secondary key (tie-breaker): Original FL score (descending). This is a common and reasonable choice.
    # Tertiary key (further tie-breaker): Alphabetical order for full determinism.
    def sort_key(item):
        key = item
        cop_score = copeland_scores.get(key, -float('inf'))
        orig_fl_score = fl_scores.get(key, -float('inf'))
        return (-cop_score, -orig_fl_score, key)

    sorted_keys = sorted(all_items, key=sort_key)

    # 5. Write results
    try:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with output_file.open('w', encoding='utf-8') as f:
            # We use the original FL scores for the output, as Copeland scores are just for ranking.
            for key in sorted_keys[:top_n]:
                # Output the original FL score for consistency with baseline formats.
                score_to_write = fl_scores.get(key, 0.0)
                f.write(f"{key},{score_to_write}\n")
        logging.info(f"Result written to {output_file}")
    except Exception as e:
        logging.error(f"Failed to write output to {output_file}: {e}")


def run_experiment_for_technique(technique: str, model: str, top_n_values: List[int]):
    """
    Runs the full experiment pipeline for a given FL technique.
    """
    logging.info(f"🚀 Starting experiment for FL Technique: {technique}")
    for top_n in top_n_values:
        logging.info(f"--- Processing Top-{top_n} configuration ---")

        topN_root = BASE_PATH / "TopN" / technique / f"top{top_n}"
        natural_root = BASE_PATH / "RQ2_final" /"natural" / "noSlice" / technique / f"top{top_n}" / model
        output_root = BASE_PATH / "实验结果" / model / "noSlice" / "CopelandFusion" / technique / f"top{top_n}"

        projects = ["Chart", "Closure", "Lang", "Math", "Mockito", "Time"]
        for project_name in projects:
            project_fl_dir = topN_root / project_name
            project_natural_dir = natural_root / project_name

            if not project_fl_dir.is_dir():
                logging.warning(f"Skipping project {project_name}: FL directory not found at {project_fl_dir}")
                continue

            for bug_dir in project_fl_dir.iterdir():
                if bug_dir.is_dir():
                    bug_id = bug_dir.name
                    fl_file = bug_dir / "stmt-susps.txt"
                    natural_file = project_natural_dir / bug_id / "entropy.txt"
                    output_file = output_root / project_name / bug_id / "stmt-susps.txt"

                    if fl_file.exists() and natural_file.exists():
                        process_single_bug(fl_file, natural_file, output_file, top_n)
                    else:
                        logging.warning(f"Skipping {bug_id} in {project_name}: missing input file(s).")


# --- 5. 脚本入口 (Script Entrypoint) ---

def main():
    """Main function to orchestrate the experiments."""
    fl_techniques = [
        "dstar2", "jaccard", "LLMAO_window", "MTL_transfer", "ochiai",
        "opt2",  "tarantula", "transfer",
        "russell_rao","CodeHealer","XAI4FL"
    ]
    #fl_techniques = ["dstar2"]
    #top_n_configs = [10, 20, 30, 50, 100]
    top_n_configs = [1000]
    model_name = "incoder"

    for technique in fl_techniques:
        run_experiment_for_technique(technique, model_name, top_n_configs)

    logging.info("✅ All experiments completed.")


if __name__ == "__main__":
    main()