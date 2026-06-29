from typing import List 
import torch 
from math import exp, log 
from torch import nn 
import tokenizers 
from math import log2
import json
from colorama import Fore, Back, Style
from transformers import AutoModelForCausalLM, AutoTokenizer
#先加载模型，获取上下文并进行掩码，计算自然度
CUDA = True 
BIG_MODEL = True


class Infiller: 
    def __init__(self, model_name):
        self.model_name = model_name


        if 'incoder' in model_name:
            self.kwargs = dict(revision="float16",torch_dtype=torch.float16,low_cpu_mem_usage=True,)
        else:
            self.kwargs = dict(torch_dtype=torch.float16,low_cpu_mem_usage=True,)
        
    def load_model(self): 
        print(f"{Style.DIM}{Fore.BLUE}Loading model...{Style.RESET_ALL}")
        self.model = AutoModelForCausalLM.from_pretrained(self.model_name, **self.kwargs)
        self.model = self.model.half().cuda()
        self.max_len = self.model.config.to_dict()['max_position_embeddings']
        print("Max length: {}".format(self.max_len))
        
    def load_tokenizer(self):
        print(f"{Style.DIM}{Fore.BLUE}Loading tokenizer...{Style.RESET_ALL}")
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        return self.tokenizer

    def load(self):
        self.load_model()
        self.load_tokenizer()
        print("Loading complete")
        if CUDA:
            self.model = self.model.half().cuda()

    def tokenize_line(self, line):
        return self.tokenizer.encode(line+'\n', add_special_tokens=False)

    def detokenize(self, context):
        return self.tokenizer.decode(context, clean_up_tokenization_spaces=False)
    
    def get_bos_id(self):
        return self.tokenizer.bos_token_id

    def get_mask_id(self, index):
        mask_str = f'<|mask:{index}|>'
        tok = self.tokenizer.encode(mask_str, add_special_tokens=False)
        return tok[0]

    def generate(self, input_ids, num_return_sequences, max_to_generate: int=52, temperature : float=0.5):
        input_ids = tensorize(input_ids).cuda()
        max_length = max_to_generate + input_ids.flatten().size(0)
        if max_length > 2048:
            print('Max length exceeded')
        with torch.no_grad():
            output = self.model.generate(input_ids=input_ids, do_sample=True, top_p=0.95, temperature=0.5, max_length=max_length, return_dict_in_generate=True, output_scores=True, num_return_sequences=num_return_sequences, pad_token_id=self.tokenizer.eos_token_id)
            return output
    
    def entropy(self, code_before_toks, code_after_toks, line_ids):
        code_before_toks, code_after_toks = truncate(code_before_toks, line_ids, code_after_toks, self.max_len, self.model_name, self.tokenizer)
        input = code_before_toks + line_ids + code_after_toks
        input_ids = tensorize(input)
        target_len = len(line_ids)
        start_loc = len(code_before_toks)
        end_loc = start_loc + target_len
        context_mask = input_ids.clone()
        context_mask[0][0:start_loc] = -100
        context_mask[0][end_loc:] = -100
        encodings = input_ids.to("cuda")
        context_mask = context_mask.to("cuda")
        with torch.no_grad():
            outputs = self.model(encodings, labels=context_mask)
            logits = outputs.logits
            shift_logits = logits[..., :-1, :].contiguous()
            shift_labels = context_mask[..., 1:].contiguous()
            loss_fct = nn.CrossEntropyLoss(reduction="none")
            loss = loss_fct(shift_logits.view(-1, shift_logits.size(-1)), shift_labels.view(-1))
            loss_list = loss.tolist()
            entropy = loss_list[start_loc-1:end_loc-1]   
            avrg_entropy = loss.sum() / (target_len)
        return avrg_entropy.item(), entropy

def tensorize(token_list):
    tensor = torch.tensor(token_list)
    tensor = tensor[None, :]
    return tensor

def truncate(code_before_toks, line_ids, code_after_toks, max_len, model_name, tokenizer):
    # token_start = tokenizer.encode("<｜fim▁begin｜>")deepseekcoder使用的
    # token_end = tokenizer.encode("<｜fim▁end｜>")
    #starcoder2使用的
    # token_start = tokenizer.encode("<fim_prefix>", add_special_tokens=False)
    # token_end = tokenizer.encode("<fim_suffix>", add_special_tokens=False)
    token_start = []
    token_after = []
    token_mid = []
    if model_name == "incoder":
        max_len = max_len-4
        token_start.append(2)
        token_after.append(50262)
        token_after.append(50261)
    if model_name == "deepseekcoder":
        max_len = max_len - 4
        start = tokenizer.encode("<｜fim▁begin｜>")
        token_start.append(start)
        end = tokenizer.encode("<｜fim▁end｜>")
        token_after.append(end)
    if model_name == "qwen":
        max_len = max_len - 4
        start = tokenizer.encode("<fim_prefix>", add_special_tokens=False)
        token_after.append(start)
        end = tokenizer.encode("<fim_suffix>", add_special_tokens=False)
        mid = tokenizer.encode("<fim_middle>", add_special_tokens=False)
        token_after.append(end)
        token_mid.append(mid)

    L_target = len(line_ids)
    max_len_for_context = max_len - L_target

    max_len_before = max_len_for_context // 2
    max_len_after = max_len_for_context - max_len_before

    # 截断前文，保留靠近目标的部分
    if len(code_before_toks) > max_len_before:
        code_before_toks = code_before_toks[-max_len_before:]

    # 截断后文，保留靠近目标的部分
    if len(code_after_toks) > max_len_after:
        code_after_toks = code_after_toks[:max_len_after]
    if model_name == "incoder":
        code_before_toks = token_start + code_before_toks
        code_after_toks = code_after_toks + [50262] + [50261]
    if model_name == "deepseekcoder":
        code_before_toks = token_start + code_before_toks
        code_after_toks = code_after_toks + token_after
    if model_name == "qwen":
        code_before_toks = token_start + code_before_toks
        code_after_toks = token_after + code_after_toks + token_mid
    return code_before_toks, code_after_toks
