from infiller import *
from item import *
from my_susline import *
import os
import time
from colorama import Fore, Style
import math
import argparse
import os
import subprocess
import chardet
import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"  # 必须放在导入 tokenizers/transformers 之前

from transformers import AutoTokenizer
#tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")
ap = argparse.ArgumentParser()
ap.add_argument("fl_tool")
ap.add_argument("model_name")
args = ap.parse_args()
fl_tool = args.fl_tool
model_name = args.model_name

if model_name == "incoder":
    model_infiller = "../incoder"
elif model_name == "unixcoder":
    model_infiller = "../unixcoder"
elif model_name == "deepseekcoder":
    model_infiller = "../deepseekcoder"
elif model_name == "qwen":
    model_infiller = "../qwen"
else:
    model_infiller = "../incoder"

infiller = Infiller(model_infiller)
tokenizer = infiller.load_tokenizer()
start = time.time()
infiller.load_model()
end = time.time()
print(f"{Fore.BLUE}{Style.BRIGHT}Time to load model: {end - start} sec{Style.RESET_ALL}")
print(f"{Fore.BLUE}{Style.BRIGHT}Starting entropy calculation...{Style.RESET_ALL}")
Top_N=1000#从现有的错误定位技术中选取前多少个代码行进行自然度的计算


def get_items(fl_path, results_path):
    items = []
    projects = os.listdir(fl_path)
    for proj in projects:
        bugs = os.listdir(f"{fl_path}/{proj}")
        for bug in bugs:
            # if proj == 'Math' and (bug=='44' or bug=='48' or bug=='16' or bug == '17' or bug == '54' or bug == '59'):
            #     items.append(Item(proj, bug, fl_path, results_path))
            # if proj == 'Mockito' and (bug == '18' or bug== '19' or bug == '20'):
            #     items.append(Item(proj, bug, fl_path, results_path))
            # if proj == 'Closure' and (1 <= int(bug) <= 13 or bug == '131' or bug == '132'):
            #     items.append(Item(proj, bug, fl_path, results_path))
            items.append(Item(proj, bug, fl_path, results_path))
    return items

def form_entropy_prompt(gen_prompt_toks, gen_ids):
    eom = tokenizer.encode("<|endofmask|>")[1]
    start_loc = len(gen_prompt_toks)
    entropy_prompt = gen_prompt_toks + gen_ids + [eom]
    return entropy_prompt, start_loc

def get_line_entropy(line, gen_prompt_toks):
    line_ids = tokenizer.encode(line, add_special_tokens=False)
    if len(line_ids) == 0:
        line_ids = tokenizer.encode("\n", add_special_tokens=False)
    entropy_prompt, start_loc = form_entropy_prompt(gen_prompt_toks, line_ids)
    line_entropy, per_tok_entropy = infiller.entropy(
        entropy_prompt, start_loc, len(line_ids)
    )
    return line_entropy, line_ids, per_tok_entropy

def is_target_line_in_TopN(proj,bug_id):#如果bug行不在前TOPN行中，则跳过这个bug

    # bug_line_file = "../bug_line/" + proj + "/" + proj + "-" + (str)(bug_id) + ".buggy.lines"
    # sus_line_file = "../SBFL/" + fl_tool + "/" + proj + "/" + (str)(bug_id) + "/stmt-susps.txt"
    # #sus_line_file = "../fl_results/" + fl_tool + "/" + proj + "/" + (str)(bug_id) + "/stmt-susps.txt"
    # with open(bug_line_file, 'rb') as f:
    #     raw_data = f.read()
    #     encoding = chardet.detect(raw_data)['encoding']
    # with open(bug_line_file, 'r',encoding=encoding) as file:
    #     bug_lines = [line for line in file.readlines()]  # 读取bug行
    # sus_lines = []
    # with open(sus_line_file, 'r') as file:
    #     lines = file.readlines()  # 读取所有可疑行
    #     for line in lines[:Top_N]:
    #         line = line.split(',')[0]
    #         sus_lines.append(line)
    # for line in bug_lines:
    #     line = line.strip()
    #     if line in sus_lines:
    #         return True
    return True

def write_entropy(file_path,entrop_results):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    try:
        # 打开文件，如果文件不存在会自动创建
        with open(file_path, 'w', encoding='utf-8') as file:
            # 遍历列表，将每一项写入文件，每项占一行
            for item in entrop_results:
                file.write(f"{item}\n")
        print(f"数据已成功写入 {file_path}")
    except Exception as e:
        print(f"写入文件时发生错误: {e}")

def rankaggre(proj,id):#将代码自然度和原先的错误定位结果进行聚合
    # 定义工作目录和 Java 命令
    working_directory = "/home/gwj/RAFL"
    # java_command = (
    #     "java -Djava.library.path=.:/home/gwj/R/x86_64-pc-linux-gnu-library/4.4/rJava/jri/ "
    #     f"-jar /home/gwj/RAFL/rafl.jar {proj}_{id} 2 "
    #     f"/home/gwj/entrop/entropy-apr-replication/fl_llm_aggregation/sbfl_incoder/{proj}/{id}/entropy.txt "
    #     f"/home/gwj/entrop/fl_results_rankaggre_big/sbfl/{proj}/{id}/stmt-susps.txt "
    #     "1 10000"
    # )/usr/lib/jvm/jdk1.8.0_391
    java_command = (
        "/usr/lib/jvm/jdk1.8.0_391/bin/java -Djava.library.path=.:/home/gwj/R/x86_64-pc-linux-gnu-library/4.4/rJava/jri/ "
        f"-jar /home/gwj/RAFL/out/artifacts/RAFL_jar/RAFL.jar {proj}_{id} 2 "
        #f"/home/gwj/entrop/entropy-apr-replication/fl_llm_aggregation_tmp/sbfl_incoder/{proj}/{id}/entropy.txt "
        f"/home/gwj/entrop/entropy-apr-replication/fl_llm_aggregation_abiation/sbfl_incoder/{proj}/{id}/entropy.txt "
        f"/home/gwj/entrop/fl_results_rankaggre_big/sbfl/{proj}/{id}/stmt-susps.txt "
        "1 10000"
    )


    # 组合 cd 和 Java 命令
    full_command = f"cd {working_directory} && {java_command}"

    # 执行复合命令
    try:
        result = subprocess.run(full_command, shell=True, check=True, text=True, capture_output=True)
        print("Command output:")
        print(result.stdout)
        if result.stderr:
            print("Command error:")
            print(result.stderr)
    except subprocess.CalledProcessError as e:
        print(f"Command failed with error: {e}")
        print(f"Error output: {e.stderr}")


def get_entropy():
    fl_path = f"../SBFL/{fl_tool}"#现有错误定位结果存放的路径
    #fl_path = f"../fl_results/{fl_tool}"  # 现有错误定位结果存放的路径
    #results_path = f"../fl_llm_aggregation_tmp/{fl_tool}_{model_name}"#聚合后错误定位结果存放的路径
    # results_path = f"../fl_llm_aggregation_integeration_50/{fl_tool}_{model_name}"  # 聚合后错误定位结果存放的路径
    results_path = f"../natural/noSlice/{fl_tool}/top{Top_N}/{model_name}"
    if not os.path.exists(results_path):
        os.mkdir(results_path)
    items = get_items(fl_path, results_path)
    idx=1
    for item in items:
        print(
            f"Running for {Fore.BLUE}{item.proj}_{item.id} {Style.RESET_ALL}...{idx}/{len(items)}"
        )
        start = time.time()
        file_path = item.results_directory + "/" + item.proj + "/" + item.id + "/entropy.txt"

        flag=is_target_line_in_TopN(item.proj,item.id)
        entrop_results = []
        idx += 1
        if not flag:
            write_entropy(file_path,entrop_results)
            continue

        if not os.path.exists(f"{results_path}/{item.proj}"):
            os.mkdir(f"{results_path}/{item.proj}")
        if not os.path.exists(f"{results_path}/{item.proj}/{item.id}"):
            os.mkdir(f"{results_path}/{item.proj}/{item.id}")
        sus_lines = item.sus_lines
        #bug_line_list = item.bug_line
        for sl in sus_lines:
            original_line=sl.origin_line.replace("\n", "")
            prompt = sl.form_gen_prompt()
            gen_prompt_toks = tokenizer.encode(prompt)
            orig_line_entropy, orig_line_ids, per_tok_entropy = get_line_entropy(
                original_line, gen_prompt_toks
            )
            if math.isnan(orig_line_entropy):#检查 orig_line_entropy 是否是 NaN（即 "Not a Number"）
                orig_line_entropy = 10.0
            entrop_result = f"{sl.class_path}#{sl.line_num},{orig_line_entropy:.6f}"
            entrop_results.append(entrop_result)

            # 新增排序逻辑：按熵值降序排列
        entrop_results.sort(key=lambda x: float(x.split(',')[1]), reverse=True)

        write_entropy(file_path, entrop_results)
        #rankaggre(item.proj,item.id)
        # 获取指定路径


        # 确保文件的目录存在，如果不存在则创建
        # os.makedirs(os.path.dirname(file_path), exist_ok=True)
        #
        # try:
        #     # 打开文件，如果文件不存在会自动创建
        #     with open(file_path, 'w', encoding='utf-8') as file:
        #         # 遍历列表，将每一项写入文件，每项占一行
        #         for item in entrop_results:
        #             file.write(f"{item}\n")
        #     print(f"数据已成功写入 {file_path}")
        #     idx+=1
        # except Exception as e:
        #     print(f"写入文件时发生错误: {e}")



if __name__ == "__main__":
    get_entropy()
