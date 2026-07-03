import torch
import torch.nn as nn
from colorama import Fore, Back, Style
from transformers import BertForMaskedLM, BertTokenizer, RobertaForMaskedLM, RobertaTokenizer, AutoConfig, RobertaConfig


class CodeBert:
    def __init__(self,pretrained,device = None):
        print("Initializing a BERT based model: {} ...".format(pretrained))
        self.pretrained = pretrained
        if device is None:
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        else:
            self.device = device
        self.model = RobertaForMaskedLM.from_pretrained(pretrained)
        self.infill_ph = "<mask>"
        self.tokenizer = RobertaTokenizer.from_pretrained(pretrained)
        self.max_len = self.model.config.to_dict()['max_position_embeddings']
        print("Max length: {}".format(self.max_len))
        self.model = self.model.to(self.device)

    def load_tokenizer(self):
        print(f"{Style.DIM}{Fore.BLUE}Loading tokenizer...{Style.RESET_ALL}")
        return self.tokenizer

    def entropy(self, code_before_toks, code_after_toks, line_ids):
        code_before_toks, code_after_toks = truncate(code_before_toks, line_ids, code_after_toks,
                                                                   self.max_len - 6)
        target_len = len(line_ids)
        #mask0_token_id = self.tokenizer.convert_tokens_to_ids("<mask>")
        mask_token_id = self.tokenizer.mask_token_id
        prefix_len = len(code_before_toks)
        ce_values = []
        batch_input_ids = []
        mask_positions_in_sequence = []
        #准备批处理输入 (Prepare Batched Inputs)
        for i in range(target_len):
            masked_line = line_ids[:i] + [mask_token_id] + line_ids[i + 1:]
            final_toks = code_before_toks + masked_line + code_after_toks
            batch_input_ids.append(final_toks)
            mask_positions_in_sequence.append(prefix_len+i)
        # 将列表转换为张量
        input_ids_tensor = torch.tensor(batch_input_ids).to(self.device)
        #一次性模型调用 (Single Model Call for the Batch)
        with torch.no_grad():
            outputs = self.model(input_ids=input_ids_tensor)
            logits = outputs.logits  # logits 的形状是 [batch_size, seq_len, vocab_size]
        batch_indices = torch.arange(target_len).to(self.device)
        pos_indices = torch.tensor(mask_positions_in_sequence).to(self.device)
        # 使用高级索引，一次性提取所有我们关心的logits
        # masked_logits 的形状将是 [target_len, vocab_size]
        masked_logits = logits[batch_indices, pos_indices, :]

        # 准备目标 labels
        target_ids = torch.tensor(line_ids).to(self.device)

        # 5. 一次性计算所有token的交叉熵损失
        loss_fct = nn.CrossEntropyLoss(reduction="none")
        loss = loss_fct(masked_logits, target_ids)

        ce_values = loss.tolist()

        # 6. 计算平均熵
        avrg_entropy = sum(ce_values) / target_len

        return avrg_entropy, ce_values
def truncate(code_before_toks, line_ids, code_after_toks, max_len):
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
    code_before_toks = [0] + code_before_toks
    code_after_toks = code_after_toks + [2]
    return code_before_toks, code_after_toks