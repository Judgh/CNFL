import torch
import torch.nn as nn
from colorama import Fore, Back, Style
from transformers import T5ForConditionalGeneration, AutoTokenizer
import random
import numpy as np

class CodeT5Plus:
    def __init__(self, pretrained, device=None):
        print("Initializing an Encoder-Decoder model: {} ...".format(pretrained))
        self.pretrained = pretrained
        if device is None:
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        else:
            self.device = device

        # 1. 修改模型和分词器类
        # 使用 T5ForConditionalGeneration 和 AutoTokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(pretrained)
        self.model = T5ForConditionalGeneration.from_pretrained(pretrained)

        self.max_len = 512
        print("Max length: {}".format(self.max_len))

        self.model = self.model.to(self.device)
        # 2. 同样需要设置为评估模式
        self.model.eval()
        print("Model set to evaluation mode.")

    def load_tokenizer(self):
        print(f"{Style.DIM}{Fore.BLUE}Loading tokenizer...{Style.RESET_ALL}")
        return self.tokenizer

    def entropy(self, code_before_toks, code_after_toks, line_ids):
        """
        计算给定上下文中，目标行的熵。
        这不再需要循环，而是通过一次前向传播完成。
        """
        # 3. 准备输入：编码器的输入是上下文
        # CodeT5+ 的输入格式可能需要特定的前缀，具体取决于它微调的任务
        # 对于通用的代码补全，我们可以简单地拼接。
        # 注意：这里的截断逻辑比 BERT 的要简单。
        input_toks, _ = truncate_t5(code_before_toks, [], code_after_toks, self.max_len)

        # 4. 准备标签：解码器的目标是生成 line_ids
        # 我们将 line_ids 作为标签传递。模型会自动创建 decoder_input_ids（通过右移和添加起始符）
        # 并计算 logits 和 line_ids 之间的损失。
        labels = torch.tensor([line_ids]).to(self.device)
        input_ids = torch.tensor([input_toks]).to(self.device)

        with torch.no_grad():
            # 5. 模型调用：同时提供 input_ids (给encoder) 和 labels (给decoder)
            outputs = self.model(input_ids=input_ids, labels=labels)

            # 6. 计算损失/熵
            # a) 获取每个词元的损失
            logits = outputs.logits
            loss_fct = nn.CrossEntropyLoss(reduction="none")
            # logits 的形状: [batch_size, target_len, vocab_size]
            # labels 的形状: [batch_size, target_len]
            loss = loss_fct(logits.view(-1, logits.size(-1)), labels.view(-1))
            per_token_entropy = loss.tolist()

            # b) 计算平均损失
            # outputs.loss 直接返回了整个序列的平均损失，更方便
            average_entropy = outputs.loss.item()

        return average_entropy, per_token_entropy

def truncate_t5(code_before_toks, line_ids, code_after_toks, max_len):
    """
    为T5模型截断上下文。
    line_ids 在这里通常不用于截断，因为它是解码器的目标。
    """
    # 编码器的输入只包含上下文
    input_toks = code_before_toks + code_after_toks
    if len(input_toks) > max_len:
        # 简单的从两边截断策略
        excess_tokens = len(input_toks) - max_len
        chop_before = excess_tokens // 2
        chop_after = excess_tokens - chop_before

        code_before_toks = code_before_toks[chop_before:]
        code_after_toks = code_after_toks[:-chop_after] if chop_after > 0 else code_after_toks

        input_toks = code_before_toks + code_after_toks

    # T5的分词器会自动处理起始和结束token，所以我们不需要手动添加 [0] 和 [2]
    # 但最终的输入序列需要一个结束符
    eos_token_id = 2  # T5 的 </s> token id 通常是 2
    if input_toks[-1] != eos_token_id:
        input_toks = input_toks + [eos_token_id]

    return input_toks, []  # 返回一个空的第二个值以匹配旧接口