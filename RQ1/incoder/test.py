import os


def is_line_skippable(line: str) -> bool:
    """
    判断一行代码是否应该被跳过（忽略），不参与合并逻辑。

    Args:
        line (str): 当前正在处理的行字符串。

    Returns:
        bool: 如果该行应该被跳过，则返回 True，否则返回 False。
    """
    # 我们只对去除前后空格后的行内容进行判断
    stripped_line = line.strip()

    # 1. 空行
    if not stripped_line:
        return True

    # 2. 以 'import' 开头的行
    if stripped_line.startswith("import "):
        return True

    # 3. 以 'package' 开头的行
    if stripped_line.startswith("package "):
        return True

    # 4. 单行注释 (// ...)
    if stripped_line.startswith("//"):
        return True

    # 5. 多行注释的开始、结束或中间行
    if stripped_line.startswith("/*") or stripped_line.startswith("*") or stripped_line.endswith("*/"):
        return True

    # 6. 单独的闭合大括号 '}'
    #    (这个规则可以根据需要调整，有时闭合大括号后可以跟其他代码)
    if stripped_line == "}":
        return True

    return False


def process_java_file_with_skipping(input_path, output_path):
    """
    读取 Java 文件，处理多行语句合并，同时跳过特定类型的行，并写入新路径。
    保留未被合并行的原始格式。

    Args:
        input_path (str): 输入的 .java 文件路径。
        output_path (str): 输出的 .java 文件路径。
    """
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Error reading file {input_path}: {e}")
        return

    processed_lines = []
    i = 0
    while i < len(lines):
        # 获取原始行内容，仅去除末尾换行符
        current_line_content = lines[i].rstrip('\n')

        # === 新增逻辑：首先判断当前行是否应该被跳过 ===
        if is_line_skippable(current_line_content):
            # 如果是可跳过的行，则不进行任何合并，直接原样保留
            processed_lines.append(current_line_content + '\n')
            i += 1
            continue  # 继续处理下一行

        # --- 如果代码执行到这里，说明该行是需要判断是否合并的有效代码行 ---

        line_for_check = current_line_content.strip()

        # 判断是否需要合并 (只对非可跳过的行进行此判断)
        if not line_for_check.endswith((';', '{', '}')):
            # 需要合并，进入合并逻辑
            j = i + 1
            # 循环查找下一行并合并
            while j < len(lines):
                next_line_content = lines[j].rstrip('\n')

                # 在合并前，检查下一行是否是可跳过的行
                if is_line_skippable(next_line_content):
                    # 如果下一行是注释、import等，则不应该合并，停止当前行的合并
                    break

                # 将下一行的内容strip()一下，去除其前导空格后进行合并
                current_line_content += " " + next_line_content.strip()

                # 检查合并后的新行是否满足结束条件
                if current_line_content.strip().endswith((';', '{', '}')):
                    i = j  # 更新主循环的索引
                    break  # 跳出内部合并循环

                j += 1
            # 如果循环到了文件末尾还没结束，i也要更新
            if j == len(lines):
                i = j - 1

        # 将最终处理好的行（可能是原始单行，也可能是合并后的多行）
        # 加上换行符，添加到结果列表中
        processed_lines.append(current_line_content + '\n')

        i += 1

    # 确保输出目录存在
    output_dir = os.path.dirname(output_path)
    os.makedirs(output_dir, exist_ok=True)

    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.writelines(processed_lines)
    except Exception as e:
        print(f"Error writing file {output_path}: {e}")


def main():
    """
    主函数，遍历所有文件并进行处理。
    """
    source_root = '/home/gwj/entrop/entropy-apr-replication/RQ1/source_file'
    target_root = '/home/gwj/entrop/entropy-apr-replication/RQ1/source_change_file'

    if not os.path.exists(source_root):
        print(f"Source directory not found: {source_root}")
        return

    print(f"Starting file processing...")
    print(f"Source: {source_root}")
    print(f"Target: {target_root}")

    for dirpath, dirnames, filenames in os.walk(source_root):
        for filename in filenames:
            if filename.endswith('.java'):
                input_file_path = os.path.join(dirpath, filename)
                relative_path = os.path.relpath(input_file_path, source_root)
                output_file_path = os.path.join(target_root, relative_path)

                print(f"Processing: {input_file_path} -> {output_file_path}")

                # 调用整合了跳过逻辑的新处理函数
                process_java_file_with_skipping(input_file_path, output_file_path)

    print("Processing complete!")


if __name__ == "__main__":
    main()