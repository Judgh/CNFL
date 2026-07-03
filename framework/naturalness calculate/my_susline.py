class SusLine:
    def __init__(self, class_path, line_num, proj, id, context_window=50):
        self.proj = proj
        self.id = id
        self.class_path = self.deal_with_class_path(class_path)  # 目标代码行类路径
        self.line_num = int(line_num)  # 在原java代码中，目标代码行的行数
        self.context_path = self.get_context_path()  # 原java文件的路径
        # self.is_in_slice = is_in_slice
        # if not is_in_slice:
        #     return
        # self.slice_dic = slice_dic  # 存放整个代码切片
        # self.code_line = self.get_line_code()#目标代码行在切片文件中的位置
        # self.origin_line=self.read_one_code_from_txt(self.code_line)#可疑语句的代码内容
        self.origin_line = self.read_one_code_from_txt(self.line_num)
        self.context_window = context_window
        self.file_start = 1  # 文件开始行
        self.file_end = self.set_file_end()  # 源代码文件结束行
        # c_start代表上下文的开始，c_end代表上下文的结束
        self.c_start, self.c_end = self.set_index()
        self.context = self.set_context()
        self.prefix = self.set_prefix(self.c_start, self.line_num)
        self.suffix = self.set_suffix(self.line_num, self.c_end)


    def deal_with_class_path(self,class_path):
        tmp_class_path = class_path.replace('.', '/')
        tmp_class_path = tmp_class_path.rsplit("$", 1)[0]
        return tmp_class_path

    def get_context_path(self):
        path = f"../../Defects4j_compile/{self.proj}/{self.proj}_{self.id}/"
        tmp_class_path = self.class_path
        if(self.proj == "Lang"):
            if int(self.id)<=35:
                path = path + "src/main/java/"+tmp_class_path+".java"
            else:
                path = path + "src/java/"+tmp_class_path+".java"
        elif(self.proj == "Math"):
            if int(self.id)<=84:
                path = path + "src/main/java/" + tmp_class_path + ".java"
            else:
                path = path + "src/java/" + tmp_class_path + ".java"
        elif(self.proj == "Chart"):
            path = path + "source/" + tmp_class_path + ".java"
        elif(self.proj == "Mockito"):
            path = path + "src/" + tmp_class_path + ".java"
        elif(self.proj == "Closure"):
            path = path + "src/" + tmp_class_path +".java"
        elif(self.proj == "Time"):
            path = path +"src/main/java/" + tmp_class_path +".java"

        return path

    def set_file_start(self):
        return min(self.slice_dic.keys())

    def set_file_end(self):
        #return max(self.slice_dic.keys())
        with open(self.context_path, 'r', encoding='utf-8',errors='ignore') as file:
            return sum(1 for _ in file)

    def set_index(self):
        lines_from_top, lines_from_bot = self.lines_from_top(), self.lines_from_bot()
        if (
                lines_from_top > self.context_window
                and lines_from_bot > self.context_window
        ):
            start = self.line_num - self.context_window
            end = self.line_num + self.context_window
        elif lines_from_top <= self.context_window:
            start = self.file_start
            add = self.context_window - lines_from_top
            end = self.line_num + self.context_window + add
            if end > self.file_end:
                end = self.file_end
        elif lines_from_bot <= self.context_window:
            end = self.file_end
            add = self.context_window - lines_from_bot
            start = self.line_num - self.context_window - add
            if start < self.file_start:
                start = self.file_start
        else:
            start = self.file_start
            end = self.file_end
        return start, end

    def lines_from_top(self):
        return self.line_num - self.file_start
    def lines_from_bot(self):
        return self.file_end - self.line_num
    def set_context(self):
        return self.read_code_from_txt(self.c_start,self.c_end)

    def get_context(self):
        return self.context
    def get_line_code(self):#返回slice.txt文件中目标代码行的行号
        target_line=self.class_path+":"+str(self.line_num)
        slice_list=list(self.slice_dic.values())
        try:
            index = slice_list.index(target_line)+1#+1是为了与字典中的行号对齐
            print(f"目标行 {target_line} 下标为: {index}")
            return index
        except ValueError:
            print(f"目标行 {target_line} 未被找到")

    def read_one_code_from_txt(self,index):#读取源代码一行的数据
        #target_path = f"../Slice_tmp/{self.proj}/{self.proj}{self.id}/code_lines.txt"
        #target_path = f"../Slice/{self.proj}/{self.proj}{self.id}/code_lines.txt"
        target_path = self.context_path
        try:
            with open(target_path, 'r', encoding='utf-8',errors="ignore") as file:
                # 遍历文件的每一行
                for line_number, line in enumerate(file, start=1):
                    if line_number == index:
                        return line  # 返回第 i 行，去掉末尾的换行符
            return f"文件中没有第 {index} 行。"  # 如果文件中没有第 i 行
        except FileNotFoundError:
            return f"文件 {target_path} 未找到。"
        except Exception as e:
            return f"发生错误: {e}"

    def read_code_from_txt(self, start_line, end_line):  # 读取源代码 start 行到 end 行之间的数据
        #target_path = f"../Slice_tmp/{self.proj}/{self.proj}{self.id}/code_lines.txt"
        #target_path = f"../Slice/{self.proj}/{self.proj}{self.id}/code_lines.txt"
        target_path = self.context_path
        try:
            with open(target_path, 'r', encoding='utf-8',errors="ignore") as file:
                lines_dict = {}  # 创建一个空字典
                # 遍历文件的每一行
                for line_number, line in enumerate(file, start=1):
                    if start_line <= line_number < end_line:  # 检查行号是否在指定范围内
                        lines_dict[line_number] = line  # 将行号作为键，行内容作为值
                if lines_dict:
                    return lines_dict  # 返回包含行号和内容的字典
                else:
                    return f"文件中没有第 {start_line} 到第 {end_line} 行的内容。"
        except FileNotFoundError:
            return f"文件 {target_path} 未找到。"
        except Exception as e:
            return f"发生错误: {e}"
    def read_code_from_txt_prefix(self, start_line, end_line):  # 读取源代码 start 行到 end 行之间的数据
        #target_path = f"../Slice_tmp/{self.proj}/{self.proj}{self.id}/code_lines.txt"
        #target_path = f"../Slice/{self.proj}/{self.proj}{self.id}/code_lines.txt"
        target_path= self.context_path
        try:
            with open(target_path, 'r', encoding='utf-8',errors="ignore") as file:
                lines_dict = {}  # 创建一个空字典
                # 遍历文件的每一行
                for line_number, line in enumerate(file, start=1):
                    if start_line <= line_number < end_line:  # 检查行号是否在指定范围内
                        lines_dict[line_number] = line  # 将行号作为键，行内容作为值
                if lines_dict:
                    return lines_dict  # 返回包含行号和内容的字典
                else:
                    return f"文件中没有第 {start_line} 到第 {end_line} 行的内容。"
        except FileNotFoundError:
            return f"文件 {target_path} 未找到。"
        except Exception as e:
            return f"发生错误: {e}"

    def read_code_from_txt_suffix(self, start_line, end_line):  # 读取源代码 start 行到 end 行之间的数据
        #target_path = f"../Slice_tmp/{self.proj}/{self.proj}{self.id}/code_lines.txt"
        #target_path = f"../Slice/{self.proj}/{self.proj}{self.id}/code_lines.txt"
        target_path = self.context_path
        try:
            with open(target_path, 'r', encoding='utf-8',errors="ignore") as file:
                lines_dict = {}  # 创建一个空字典
                # 遍历文件的每一行
                for line_number, line in enumerate(file, start=1):
                    if start_line < line_number <= end_line:  # 检查行号是否在指定范围内
                        lines_dict[line_number] = line  # 将行号作为键，行内容作为值
                if lines_dict:
                    return lines_dict  # 返回包含行号和内容的字典
                else:
                    return ""
        except FileNotFoundError:
            return f"文件 {target_path} 未找到。"
        except Exception as e:
            return f"发生错误: {e}"

    def get_prefix(self):
        return self.prefix

    def get_suffix(self):
        return self.suffix

    def set_prefix(self, c_start, code_line):
        return self.read_code_from_txt_prefix(c_start,code_line)

    def set_suffix(self, code_line, c_end):
        return self.read_code_from_txt_suffix(code_line,c_end)

    def to_string(self, dic):
        code_str = ""
        if not dic:  # 检查字典是否为空
            return ""
        for k, v in dic.items():
            code_str += v
        return code_str

    def form_gen_prompt(self):
        code_before = self.to_string(self.prefix)
        code_after = self.to_string(self.suffix)
        prompt = code_before + "<|mask:0|>" + "\n" + code_after + "<|mask:1|><|mask:0|>"
        #prompt = code_before + "<|mask:0|>" + "\n" + code_after
        return prompt
