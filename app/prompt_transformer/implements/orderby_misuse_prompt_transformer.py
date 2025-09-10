from typing import Any, List, Dict, Tuple
import json
import os
from ..interfaces.prompt_transformer import PromptTransformer
current_dir = os.path.dirname(os.path.abspath(__file__))
class OrderByMisusePromptTransformer(PromptTransformer):
    def prompt_transformer_instruction_construct(self):
        #  prompt
        return "your constructed prompt here"

    def qmr_3_prompt_transformer_instruction_construct_equivalent(self, n) -> List[dict]:
        prompt = (
            f"Rewrite the following question into {n} equivalent questions,which include both original question and explicit constraints about OrderBy,  making all implicit constraints about OrderBy explicit."
            f"You should reformulate vague or underspecified instructions into precise control parameters, without changing the query's overall meaning or result set.\n\n"

            f"Example 1:\n"
            f"Original question: List products by price from high to low.\n"
            f"Equivalent question: List products by price from high to low. Explicit constraints about OrderBy: List all products ordered by price in descending order, so that the most expensive products appear first.\n"

            f"Example 2:\n"
            f"Original question: List the top 10 students by GPA.\n"
            f"Equivalent question: List the top 10 students by GPA. Explicit constraints about OrderBy: List the 10 students with the highest GPA, ordered by GPA in descending order, so the top students appear first.\n"

            f"Example 3:\n"
            f"Original question: Show products ordered by category then price.\n"
            f"Equivalent question: Show products ordered by category then price. Explicit constraints about OrderBy: List all products ordered first by category in ascending order, and within each category ordered by price in descending order.\n\n"

            f"Now generate {n} equivalent questions for the following question:\n"
            f"Question: {self.question}\n"
            f"Do not include any explanations in your response. Just return the {n} equivalent questions, each separated by a newline."
        )

        #  LLM （system + user）
        formatted_instruction = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ]
        return formatted_instruction

    def qmr_3_generate_metamorphic_prompts(self, hallu_type) -> Tuple[List[str], List[str], Any]:
        """
         LLM ，。
        3，。
        """
        metamorphic_questions_temp = []
        mr_relations_temp = []
        completion_tokens = 0
        prompt_tokens = 0
        total_tokens = 0
        gene_num = self.n // 2  # 

        # equivalent
        transformer_instruction_equivalent = self.qmr_3_prompt_transformer_instruction_construct_equivalent(gene_num)
        for attempt in range(1, 8):
            answer, _usage = self.llm_client.generate(transformer_instruction_equivalent)
            split_questions = self.metamorphic_prompts_process(answer)
            print(split_questions)
            completion_tokens += _usage[0]
            prompt_tokens += _usage[1]
            total_tokens += _usage[2]
            if len(split_questions) == gene_num:
                metamorphic_questions_temp.extend(split_questions)
                mr_relations_temp.extend(["equivalent"] * gene_num)
                break

        self.metamorphic_questions = metamorphic_questions_temp
        self.trans_usage = [completion_tokens, prompt_tokens, total_tokens]
        return metamorphic_questions_temp, mr_relations_temp, self.trans_usage

    def qmr_4_generate_metamorphic_prompts(self, hallu_type) -> Tuple[List[str], List[str], Any]:
        """
         LLM ，。
        3，。
        """
        metamorphic_questions_temp = []
        mr_relations_temp = []
        completion_tokens = 0
        prompt_tokens = 0
        total_tokens = 0
        gene_num = self.n // 2  # 

        hallu_type_name = "OrderBy Misuse"
        with open(os.path.join(current_dir,"HallucinationTypeDefinition.json"), "r", encoding="utf-8") as r:
            definition = json.load(r)[hallu_type_name]

        metamorphic_question = f"{self.question}\n" + \
        f"### Important rules: 1.After generating the query, you must verify whether the query introduces a {hallu_type_name}." + \
        "2. If the query introduces such error, fix it automatically." + \
        "3. The final output must only be the corrected query, with no explanation.\n" + \
        f"### Definition of {hallu_type_name}:{definition}"

        metamorphic_question = f"{self.question}\n" + \
        f"### Important rules: 1.After generating the query, you must verify whether the query introduces a {hallu_type_name} hallucination." + \
        "2. If the query introduces such error, fix it automatically." + \
        "3. The final output must only be the corrected query, with no explanation.\n"

        metamorphic_questions_temp.extend([metamorphic_question] * gene_num )
        mr_relations_temp.extend(["equivalent"] * gene_num)

        self.metamorphic_questions = metamorphic_questions_temp
        self.trans_usage = [completion_tokens, prompt_tokens, total_tokens]
        return metamorphic_questions_temp, mr_relations_temp, self.trans_usage

    def generate_metamorphic_prompts(self,  hallu_type) -> Tuple[List[str], List[str], Any]:
        if "qmr-3" in hallu_type.lower():
            return self.qmr_3_generate_metamorphic_prompts(hallu_type)
        elif "qmr-4" in hallu_type.lower():
            return self.qmr_4_generate_metamorphic_prompts(hallu_type)
