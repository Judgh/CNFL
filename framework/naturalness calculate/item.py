import json
import re

try:
    from my_susline import *
except:
    from my_ebfl.my_susline import *
import os
Top_N=10#从现有的错误定位技术中选取前多少个代码行进行自然度的计算
class Item:
    def __init__(self, proj, bug_id, fl_path, results_path):
        self.proj = proj
        self.id = bug_id
        self.fl_directory = fl_path#现有错误定位结果存放的路径
        self.results_directory = results_path
        self.slice = self.get_slice()#整个切片代码以字典的形式进行存放，其中行号为key，内容内容为value
        self.sus_lines = self.set_sus_lines()
        # self.results = self.set_results()
        # self.fl_results = self.get_fl_results()



    def get_codelines(self):
        """
        读取 stmt-susps.txt 文件，并返回一个列表，
        其中只包含可疑度分数大于 0 的行。
        """
        try:
            file_path = f"{self.fl_directory}/{self.proj}/{self.id}/stmt-susps.txt"

            # 检查文件是否存在
            if not os.path.exists(file_path):
                # 明确返回一个空列表，而不是错误字符串，便于后续处理
                print(f"Warning: File not found -> {file_path}")
                return []

            valid_lines = []
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                for line in file:
                    line = line.strip()
                    # 确保行不为空且包含逗号，这是解析的基础
                    if not line or ',' not in line:
                        continue

                    try:
                        # --- *** 核心修改点在这里 *** ---
                        # 1. 将行按最后一个逗号分割，以应对路径中可能包含逗号的特殊情况
                        identifier, score_str = line.rsplit(',', 1)

                        # 2. 将分数部分转换为浮点数
                        suspiciousness_score = float(score_str)

                        # 3. 判断分数是否大于 0
                        if suspiciousness_score > 0:
                            # 只有分数大于0的行才会被加入列表
                            valid_lines.append(line)
                        # --- *** 修改结束 *** ---

                    except (ValueError, IndexError):
                        # 如果某一行格式不正确（例如，逗号后不是一个有效的数字），则忽略该行
                        # print(f"Warning: Skipping malformed line in {file_path}: {line}")
                        continue

            # 返回所有满足条件的行
            return valid_lines

        except Exception as e:
            print(f"An unexpected error occurred in get_codelines: {e}")
            # 在出现意外错误时也返回空列表，保持函数返回类型的一致性
            return []

    def extract_info(self,input_list):
        class_list = []  # 存储类名的列表
        number_list = []  # 存储数字的列表

        # 遍历输入列表中的每个字符串
        for input_str in input_list:
            # Step 1: Split by '#'
            class_name, number_part = input_str.split('#')

            # Step 2: Split the number part by ','
            number, decimal = number_part.split(',')

            # Step 3: Append results to respective lists
            class_list.append(class_name)
            number_list.append(number)

        return class_list, number_list
    def set_sus_lines(self):
        sus_lines=[]
        #code_line存储"org.jfree.chart.renderer.AbstractRenderer#406,0.05345224838248487"
        code_lines=self.get_codelines()
        #class_lines和line_number_list存储的分别为org.jfree.chart.renderer.AbstractRenderer和406
        class_list,line_number_list= self.extract_info(code_lines)

        for class_path, line_number in zip(class_list, line_number_list):
            target_line=class_path+":"+line_number
            #target_line='org.jfree.chart.renderer.category.junit.AbstractCategoryItemRendererTests:397'
            # if target_line in self.slice.values():
            #     sus_lines.append(SusLine(class_path,line_number,self.proj,self.id,True))
            # else:
            #     sus_lines.append(SusLine(class_path, line_number, self.proj, self.id, False))
            sus_lines.append(SusLine(class_path, line_number, self.proj, self.id))
        return sus_lines

    def get_slice(self):
        #slice_path=f"../Slice_tmp/{self.proj}/{self.proj}{self.id}/slice.log"
        slice_path = f"../Slice/{self.proj}/{self.proj}{self.id}/slice.log"
        log_dict = {}  # 用来存储行号和对应内容的字典

        try:
            # 打开文件进行读取
            with open(slice_path, 'r', encoding='utf-8') as file:
                for line_number, line_content in enumerate(file, start=1):
                    # 将行号和对应内容存入字典
                    log_dict[line_number] = line_content.strip()  # 使用 strip() 去掉末尾的换行符

            return log_dict  # 返回字典

        except FileNotFoundError:
            return f"文件 {slice_path} 未找到。"
        except Exception as e:
            return f"发生错误: {e}"


