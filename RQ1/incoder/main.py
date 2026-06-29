import os
import re
import time
from colorama import Fore, Style
import math
import argparse
import subprocess
import chardet
from infiller import Infiller
from codebert import CodeBert
from codeT5plus import CodeT5Plus

# --- 辅助函数 1：判断是否需要跳过（排除）代码行 ---
model_name = "codeT5plus"
start = time.time()
if model_name == "incoder":
    model_infiller = "../../incoder"
    infiller = Infiller(model_infiller)
    infiller.load_model()
if model_name == "codebert":
    model_infiller = "../../codebert"
    infiller = CodeBert(model_infiller)
if model_name == "codeT5plus":
    model_infiller = "../../codeT5plus"
    infiller = CodeT5Plus(model_infiller)
if model_name == "deepseekcoder":
    model_infiller = "../../deepseekcoder"
    infiller = Infiller(model_infiller)
    infiller.load_model()
if model_name == "qwen":
    model_infiller = "../../model/qwen"
    infiller = Infiller(model_infiller)
    infiller.load_model()
#infiller = Infiller(model_infiller)
end = time.time()
tokenizer = infiller.load_tokenizer()

print(f"{Fore.BLUE}{Style.BRIGHT}Time to load model: {end - start} sec{Style.RESET_ALL}")
print(f"{Fore.BLUE}{Style.BRIGHT}Starting entropy calculation...{Style.RESET_ALL}")
def is_line_skippable(line: str) -> bool:
    """
    判断一行代码是否需要被跳过（排除），不计算其自然度。
    专门处理 /** ... */ 风格的多行注释，并且假设注释不与代码混杂在同一行。

    Args:
        line: 当前正在处理的行字符串。

    Returns:
        should_skip:
    """
    stripped_line = line.strip()
    should_skip = False

    # 1. 空行
    if not stripped_line:
        should_skip = True

    # 2. 以 'import' 开头的行
    elif stripped_line.startswith("import "):
        should_skip = True

    # 3. 以 'package' 开头的行
    elif stripped_line.startswith("package "):
        should_skip = True

    # 4. 单行注释 (// ...)
    elif stripped_line.startswith("//"):
        should_skip = True

    # 5. 多行注释 (/** ... */) 处理
    elif stripped_line.startswith("/*") or stripped_line.startswith("*/"):
        should_skip = True

    # 6. 多行注释内部的处理
    elif stripped_line.startswith("*"):
        should_skip = True

    return should_skip


# --- 辅助函数 2：提取上下文 ---

def extract_context(target_line_num: int, all_lines_content: list, context_window=50):
    """
    根据目标行号提取上下文。

    Args:
        target_line_num: 目标代码行的行号（从 1 开始）。
        all_lines_content: 文件中所有行的列表。
        context_window: 上/下文的总行数。

    Returns:
        返回目标代码行上下文窗口在列表中的开始位置和结尾位置
    """
    lines_from_top = target_line_num - 1
    lines_from_bot = len(all_lines_content) - target_line_num
    file_end = len(all_lines_content)+1
    file_start = 0
    if (
            lines_from_top > context_window
            and lines_from_bot > context_window
    ):
        start = target_line_num - context_window
        end = target_line_num + context_window
    elif lines_from_top <= context_window:
        start = 0
        add = context_window - lines_from_top
        end = target_line_num + context_window + add
        if end > file_end:
            end = file_end
    elif lines_from_bot <= context_window:
        end = file_end
        add = context_window - lines_from_bot
        start = target_line_num - context_window - add
        if start < file_start:
            start = file_start
    else:
        start = file_start
        end = file_end
    return start, end


def list_to_string(string_list) ->str:
    separator = ""
    return separator.join(string_list)
# --- 主处理函数 ---

def process_java_file_for_naturalness(file_path: str, output_file_path):
    """
    逐行读取 Java 文件，判断是否需要计算自然度。
    对于需要计算的行，提取其上下文（上文/下文共 context_window_size 行）。

    Args:
        file_path: Java 文件的路径。
        context_window_size: 上下文的总行数（上文 + 下文）。

    """
    if os.path.exists(output_file_path) and os.path.getsize(output_file_path) > 0:
        return
    all_file_lines = []  # 存储所有行的内容，方便根据行号获取上下文

    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                all_file_lines.append(line)  # 保存原始行
    except FileNotFoundError:
        print(f"错误：文件未找到 - {file_path}")
        exit(0)
    except Exception as e:
        print(f"读取文件 {file_path} 时发生错误: {e}")
        exit(0)

    # 结果列表
    results_to_write = []
    file_name = os.path.basename(file_path).replace(".java", "")  # 获取文件名

    # 遍历文件的每一行
    for i, line in enumerate(all_file_lines):
        current_line_num = i + 1

        # 调用 is_line_skippable 来判断是否跳过当前行
        should_skip = is_line_skippable(
            line
        )

        # 如果该行需要被跳过，则 continue
        if should_skip:
            continue

        # --- 到这里，这行是有效代码行，需要计算自然度 ---


        # --- 获取该有效代码行的上下文 ---
        # 调用 extract_context，传递 is_line_skippable 函数和固定的参数
        # 注意：extract_context 现在不管理注释状态，并且它内部也不再调用 is_line_skippable 来过滤注释。
        # 它会直接返回原始行内容（只移除行尾的换行符）

        prefix_start_index, suffix_end_index = extract_context(
            target_line_num=current_line_num,
            all_lines_content=all_file_lines
            )
        prefix = all_file_lines[prefix_start_index:current_line_num]
        suffix = all_file_lines[current_line_num+1:suffix_end_index+1]
        prefix_str = list_to_string(prefix)
        suffix_str = list_to_string(suffix)
        prefix_toks =  tokenizer.encode(prefix_str)
        suffix_toks =  tokenizer.encode(suffix_str)
        orig_line_entropy, orig_line_ids, per_tok_entropy = get_line_entropy(
            line, prefix_toks, suffix_toks
        )
        result_entrop = f"{file_name}#{current_line_num},{orig_line_entropy}"
        results_to_write.append(result_entrop)
        results_to_write.sort(key=lambda x: float(x.split(",")[-1]), reverse=True)
        if results_to_write:
            try:
                output_dir = os.path.dirname(output_file_path)
                # 2. 如果目录不存在，则创建它（包括所有中间目录）
                if output_dir and not os.path.exists(output_dir):  # 确保目录存在且非空字符串
                    os.makedirs(output_dir)
                    print(f"已创建输出目录：{output_dir}")
                # 以写入模式打开文件，如果不存在则创建
                with open(output_file_path, 'w', encoding='utf-8', errors='ignore') as outfile:
                    for entry in results_to_write:
                        outfile.write(entry + '\n')  # 每条结果占一行
                print(f"结果已写入：{output_file_path}")
            except Exception as e:
                print(f"写入文件 {output_file_path} 时发生错误: {e}")
        else:
            print(f"未找到需要计算自然度的代码行，或处理过程中未产生结果。文件 {output_file_path} 未被修改。")


def get_line_entropy(original_line, code_before_toks, code_after_toks):
    line_ids = tokenizer.encode(original_line, add_special_tokens=False)
    if len(line_ids) == 0:
        line_ids = tokenizer.encode("\n", add_special_tokens=False)
    #entropy_prompt, start_loc = form_entropy_prompt(gen_prompt_toks, line_ids)
    #start_loc = len(tokenizer.encode(code_before_toks, add_special_tokens=False))
    line_entropy, per_tok_entropy = infiller.entropy(
        code_before_toks, code_after_toks, line_ids
    )
    return line_entropy, line_ids, per_tok_entropy

def find_java_files(base_path: str, output_path):
    #projects = ["Chart", "Closure", "Lang", "Time", "Math", "Mockito"]
    #projects = ["Chart", "Closure", "Lang", "Time", "Math"]
    projects = ["Chart"]
    # 检查基础路径是否存在
    if not os.path.isdir(base_path):
        print(f"错误：基础路径 '{base_path}' 不存在或不是一个目录。")
        exit(0)

    if not os.path.isdir(output_path):
        print(f"错误：基础路径 '{output_path}' 不存在或不是一个目录。")
        exit(0)

    # 遍历项目子文件夹
    for project_name in projects:
        project_path = os.path.join(base_path, project_name)
        base_project_output_path = os.path.join(output_path, project_name)


        # 检查项目子文件夹是否存在
        if not os.path.isdir(project_path):
            print(f"警告：项目路径 '{project_path}' 不存在，跳过。")
            exit(0)

        # 遍历数字文件夹
        for item in os.listdir(project_path):
            number_folder_path = os.path.join(project_path, item)
            # 重新创建一个新的输出路径（不会影响下次循环）
            number_output_path = os.path.join(base_project_output_path, item)
            entropy_output_file = os.path.join(number_output_path, "entropy.txt")
            # 确保这是一个目录，并且看起来像一个数字文件夹
            # （这里假设数字文件夹名就是数字，或者只是一个文件夹名，更通用的做法是检查是否是目录）
            if os.path.isdir(number_folder_path):
                # 遍历数字文件夹中的文件
                for filename in os.listdir(number_folder_path):
                    if filename.endswith(".java"):
                        java_file_path = os.path.join(number_folder_path, filename)
                        # print(f"找到: {java_file_path}") # 可选：打印找到的文件路径
                        process_java_file_for_naturalness(java_file_path, entropy_output_file)


# --- 示例用法 ---
if __name__ == "__main__":
    # 请将这里的路径替换为你实际的基础路径
    source_directory = "../source_file"
    output_path = f"../result/{model_name}"
    print(f"正在查找路径 '{source_directory}' 下的 .java 文件...")
    find_java_files(source_directory,output_path)


