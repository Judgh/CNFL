# def get_context_path(self):
#     for i in range(1,27):
#         path = f"../../Defects4j_compile/Chart/{self.proj}_{self.id}/"
#         tmp_class_path = self.class_path
#         if (self.proj == "Lang"):
#             if int(self.id) <= 35:
#                 path = path + "src/main/java/" + tmp_class_path + ".java"
#             else:
#                 path = path + "src/java/" + tmp_class_path + ".java"
#         elif (self.proj == "Math"):
#             if int(self.id) <= 84:
#                 path = path + "src/main/java/" + tmp_class_path + ".java"
#             else:
#                 path = path + "src/java/" + tmp_class_path + ".java"
#         elif (self.proj == "Chart"):
#             path = path + "source/" + tmp_class_path + ".java"
#         elif (self.proj == "Mockito"):
#             path = path + "src/" + tmp_class_path + ".java"
#         elif (self.proj == "Closure"):
#             path = path + "src/" + tmp_class_path + ".java"
#         elif (self.proj == "Time"):
#             path = path + "src/main/java/" + tmp_class_path + ".java"
#
#         return path

import os
import shutil
import re


def process_buggy_lines_and_copy_java(buggy_lines_dir: str, output_source_dir: str):
    """
    读取 .buggy.lines 文件，根据文件内容和名称构建源 Java 文件路径，
    创建目标目录，并将找到的 Java 文件复制过去。

    Args:
        buggy_lines_dir: 包含 .buggy.lines 文件的目录路径。
                         预期结构: buggy_lines_dir/Chart/Chart-N.buggy.lines
        output_source_dir: 目标 Java 文件输出的根目录路径。
                           预期结构: output_source_dir/Chart/N/JavaFile.java
    """

    if not os.path.isdir(buggy_lines_dir):
        print(f"错误：输入的 .buggy.lines 目录 '{buggy_lines_dir}' 不存在。")
        return

    # 查找 Chart这种类型的文件夹
    proj = ["Chart", "Mockito","Math","Lang","Time","Closure"]
    for pro in proj:
        chart_dir_path = os.path.join(buggy_lines_dir, pro)
        if not os.path.isdir(chart_dir_path):
            print(f"错误：Chart 文件夹 '{chart_dir_path}' 不存在。")
            return

        print(f"开始处理文件，源目录: {chart_dir_path}")

        # 遍历 Chart 文件夹下的所有 .buggy.lines 文件
        for filename in os.listdir(chart_dir_path):
            if filename.endswith(".buggy.lines"):
                buggy_file_path = os.path.join(chart_dir_path, filename)

                # 提取文件名中的数字 i (例如 Chart-1.buggy.lines -> 1)
                try:
                    # 使用正则表达式提取数字
                    match = re.search(r'-(\d+)\.buggy\.lines$', filename)
                    if not match:
                        print(f"警告：无法从文件名 '{filename}' 中提取数字，跳过。")
                        continue
                    i = int(match.group(1))  # 提取匹配到的数字
                except Exception as e:
                    print(f"警告：解析文件名 '{filename}' 时出错: {e}，跳过。")
                    continue

                # 读取 .buggy.lines 文件中的数据行
                try:
                    with open(buggy_file_path, 'r', encoding='utf-8',errors='ignore') as f:
                        for line in f:
                            # 确保行不为空
                            if not line.strip():
                                continue

                            # 提取 # 之前的字符串 (类名)
                            class_name_part = line.split('#')[0]
                            if not class_name_part:
                                print(f"警告：在文件 '{filename}' 的行 '{line.strip()}' 中未找到类名部分，跳过。")
                                continue

                            # 1. 在类名后面加上 .java
                            java_file_name = class_name_part

                            # 2. 拼接源 Java 文件的路径
                            # 格式: "../../Defects4j_compile/Chart/Chart_{i}/" + java_file_name
                            # 注意：这里 "../../Defects4j_compile/Chart/Chart_{i}/" 是相对路径，
                            # 如果你的脚本不在 entrop/entropy-apr-replication/RQ1/ 目录下，可能需要调整。
                            # 为了代码的普适性，我们假设这是相对于脚本所在目录的路径，
                            # 或者您需要一个完整的绝对路径。
                            # 我将使用一个相对路径来演示，您可能需要根据实际情况调整。

                            # 假设您的 Defects4j_compile 目录与 entrop 目录在同一层级，
                            # 并且你的脚本执行路径是 entrop/RQ1/incoder/
                            # 那么 ../../Defects4j_compile 是正确的。
                            # 如果你的脚本执行路径不同，需要相应调整。

                            # 假设 base_java_source_dir 是 "../../Defects4j_compile/"
                            # 这是一个演示，请根据您的项目结构替换
                            # base_java_source_dir = os.path.join(
                            #     os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "..", "..",
                            #     "Defects4j_compile")
                            base_java_source_dir = f"../../Defects4j_compile"
                            java_file_name = java_file_name.replace(".", "/")
                            java_file_name = java_file_name + ".java"

                            # 拼接源 Java 文件的完整路径
                            if pro == "Chart":
                                source_java_file_path = os.path.join(base_java_source_dir, "Chart", f"Chart_{i}","source",
                                                                     java_file_name)
                            if pro == "Mockito":
                                source_java_file_path = os.path.join(base_java_source_dir, "Mockito", f"Mockito_{i}",
                                                                     "src",
                                                                     java_file_name)
                            if pro == "Closure":
                                source_java_file_path = os.path.join(base_java_source_dir, "Closure", f"Closure_{i}",
                                                                     "src",
                                                                     java_file_name)
                            if pro == "Time":
                                source_java_file_path = os.path.join(base_java_source_dir, "Time", f"Time_{i}",
                                                                     "src/main/java",
                                                                     java_file_name)
                            if pro == "Lang":
                                if i <= 35:
                                    source_java_file_path = os.path.join(base_java_source_dir, "Lang", f"Lang_{i}",
                                                                         "src/main/java",
                                                                         java_file_name)
                                else:
                                    source_java_file_path = os.path.join(base_java_source_dir, "Lang", f"Lang_{i}",
                                                                         "src/java",
                                                                         java_file_name)
                            if pro == "Math":
                                if i <= 84:
                                    source_java_file_path = os.path.join(base_java_source_dir, "Math", f"Math_{i}",
                                                                         "src/main/java",
                                                                         java_file_name)
                                else:
                                    source_java_file_path = os.path.join(base_java_source_dir, "Math", f"Math_{i}",
                                                                         "src/java",
                                                                         java_file_name)
                            # 3. 创建目标目录
                            # 格式: /home/gwj/entrop/entropy-apr-replication/RQ1/source_file/Chart/{i}
                            target_dir = os.path.join(output_source_dir, pro, str(i))

                            # 确保目标目录存在
                            try:
                                os.makedirs(target_dir, exist_ok=True)  # exist_ok=True 避免目录已存在时报错
                            except OSError as e:
                                #print(f"警告：创建目录 '{target_dir}' 失败: {e}，尝试继续但不保证成功。")
                                continue  # 跳过此文件，尝试处理下一个
                            filename = os.path.basename(java_file_name)
                            # 4. 复制 Java 文件到目标目录
                            target_java_file_path = os.path.join(target_dir, filename)

                            if not os.path.exists(source_java_file_path):
                                #print(f"警告：源 Java 文件 '{source_java_file_path}' 不存在，无法复制，跳过。")
                                continue

                            try:
                                shutil.copy2(source_java_file_path, target_java_file_path)
                                #print(f"已复制: {source_java_file_path} -> {target_java_file_path}")
                            except Exception as e:
                                print(f"复制文件 '{source_java_file_path}' 到 '{target_java_file_path}' 时出错: {e}")

                except FileNotFoundError:
                    print(f"错误：.buggy.lines 文件 '{buggy_file_path}' 未找到。")
                except Exception as e:
                    print(f"处理文件 '{buggy_file_path}' 时发生错误: {e}")


# --- 示例用法 ---
if __name__ == "__main__":
    # --- 配置 ---
    # 请根据您的实际项目结构修改这些路径！

    # bug_lines_dir: 存放 Chart-N.buggy.lines 文件的目录
    buggy_lines_input_directory = "/home/gwj/entrop/entropy-apr-replication/bug_line"

    # output_source_dir: 目标 Java 文件输出的根目录
    # 预期结构: output_source_dir/Chart/{i}/YourClass.java
    destination_source_files_directory = "/home/gwj/entrop/entropy-apr-replication/RQ1/source_file"

    # --- 实际执行 ---
    print("\n开始执行文件处理和复制流程...")

    process_buggy_lines_and_copy_java(buggy_lines_input_directory, destination_source_files_directory)

    print("\n文件处理流程完成！")