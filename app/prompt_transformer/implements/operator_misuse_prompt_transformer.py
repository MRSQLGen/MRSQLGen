from typing import Any, List, Dict, Tuple
import json
import os
from ..interfaces.prompt_transformer import PromptTransformer
current_dir = os.path.dirname(os.path.abspath(__file__))
class OperatorMisusePromptTransformer(PromptTransformer):
    """
    OperatorMisusePromptTransformer
    =======================
     LLM  question ，，（prompt paraphasing）。
    """
    def prompt_transformer_instruction_construct(self):
        #  prompt
        return "your constructed prompt here"

    def prompt_transformer_instruction_construct_equivalent(self, n) -> List[dict]:
        # 
        prompt = (
            f"Generate {n} simple English questions that are semantically equivalent to the following question but different from each other, and whose corresponding SQL queries would also be logically equivalent. "
            f"You must achieve this by modifying only the arithmetic, comparison, or logical operation descriptions without changing the query's overall meaning or result set.\n\n"

            f"Example 1:\n"
            f"Original question: Show each employee and their total compensation(positive number), calculated as `base_salary + bonus`.\n"
            f"Equivalent question: Display all employees with `total_compensation = base_salary + bonus`(positive number).\n"

            f"Example 2:\n"
            f"Original question: Find employees with a salary greater than 5000.\n"
            f"Equivalent question: Retrieve all employees whose salary is strictly above five thousand dollars.\n"

            f"Example 3:\n"
            f"Original question: Find customers who are from New York or Los Angeles.\n"
            f"Equivalent question:Retrieve customers whose city is either New York or Los Angeles.\n"

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

    def prompt_transformer_instruction_construct_superset(self, n) -> List[dict]:
        # 
        prompt = (
            f"Generate {n} simple English questions whose corresponding SQL queries would return a superset of the original query's result set. "
            f"i.e., the generated query should include all results of the original query and potentially more. "
            f"The generated questions must be obtained by modifying only the arithmetic, comparison, or logical operation descriptions in the given question to relax or broaden the conditions, "
            f"thus expanding the scope of the returned data, without changing other parts of the question.\n\n"

            f"Example 1:\n"
            f"Original question:Show each employee and their total compensation(positive number), calculated as `base_salary + bonus`.\n"
            f"Superset question: Display all employees with `total_compensation = base_salary + bonus`, including employees with zero bonus.\n"

            f"Example 2:\n"
            f"Original question: Find employees with a salary greater than 5000.\n"
            f"Superset question: Find employees with a salary greater than or equal to 4000.\n"

            f"Example 3:\n"
            f"Original question: Find videos longer than 10 minutes.\n"
            f"Superset question: Find customers who are from New York, Los Angeles, or Chicago.\n"

            f"Now generate {n} superset questions for the following question:\n"
            f"Question: {self.question}\n"
            f"Please only return the {n} superset questions separated by newlines, without any explanations or additional text."
        )

        #  LLM （system + user）
        formatted_instruction = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ]
        return formatted_instruction

    def prompt_transformer_instruction_construct_subset(self, n) -> List[dict]:
        # 
        prompt = (
            f"Generate {n} simple English questions whose corresponding SQL queries would return a subset of the original query's result set. "
            f"i.e., the generated query should include only a portion of the result of the original query. "
            f"The generated questions must be obtained by modifying only the arithmetic, comparison, or logical operation descriptions in the given question to tighten or strengthen the conditions, "
            f"thus narrowing the scope of the returned data, without changing other parts of the question.\n\n"

            f"Example 1:\n"
            f"Original question: Show each employee and their total compensation(positive number), calculated as `base_salary + bonus`.\n"
            f"Subset question: Display employees with `total_compensation = base_salary + bonus` and bonus > 1000.\n"

            f"Example 2:\n"
            f"Original question: Find employees with a salary greater than 5000.\n"
            f"Subset question: Find employees with a salary greater than 6000.\n"

            f"Example 3:\n"
            f"Original question: Find customers who are from New York or Los Angeles.\n"
            f"Subset question: Find customers who are from New York only.\n"

            f"Now generate {n} subset questions for the following question:\n"
            f"Question: {self.question}\n"
            f"Please only return the {n} subset questions separated by newlines, without any explanations or additional text."
        )

        #  LLM （system + user）
        formatted_instruction = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ]
        return formatted_instruction

    def qmr_1_generate_metamorphic_prompts(self,  hallu_type) -> Tuple[List[str], List[str], Any]:
        """
         LLM ，。
        3，。
        """
        metamorphic_questions_temp = []
        mr_relations_temp = []
        completion_tokens = 0
        prompt_tokens = 0
        total_tokens = 0
        gene_num = self.n // 2 # 
        gene_num = gene_num  // 3  # 

        # equivalent
        transformer_instruction_equivalent = self.prompt_transformer_instruction_construct_equivalent(gene_num * 3)
        for attempt in range(1, 5):
            answer, _usage = self.llm_client.generate(transformer_instruction_equivalent)
            split_questions = self.metamorphic_prompts_process(answer)
            completion_tokens += _usage[0]
            prompt_tokens += _usage[1]
            total_tokens += _usage[2]
            if len(split_questions) == gene_num * 3:
                metamorphic_questions_temp.extend(split_questions)
                mr_relations_temp.extend(["equivalent"] * gene_num * 3)
                break


        # superset
        transformer_instruction_superset = self.prompt_transformer_instruction_construct_superset(gene_num)
        for attempt in range(1, 5):
            answer, _usage = self.llm_client.generate(transformer_instruction_superset)
            split_questions = self.metamorphic_prompts_process(answer)
            completion_tokens += _usage[0]
            prompt_tokens += _usage[1]
            total_tokens += _usage[2]
            if len(split_questions) == gene_num:
                metamorphic_questions_temp.extend(split_questions)
                mr_relations_temp.extend(["superset"] * gene_num)
                break

        # Subset
        transformer_instruction_subset = self.prompt_transformer_instruction_construct_subset(gene_num)
        for attempt in range(1, 4):
            answer, _usage = self.llm_client.generate(transformer_instruction_subset)
            split_questions = self.metamorphic_prompts_process(answer)
            completion_tokens += _usage[0]
            prompt_tokens += _usage[1]
            total_tokens += _usage[2]
            if len(split_questions) == gene_num:
                metamorphic_questions_temp.extend(split_questions)
                mr_relations_temp.extend(["subset"] * gene_num)
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

        hallu_type_name = "Operator Misuse"
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

    def generate_metamorphic_prompts(self, hallu_type) -> Tuple[List[str], List[str], Any]:
        if "qmr-1" in hallu_type.lower():
            return self.qmr_1_generate_metamorphic_prompts(hallu_type)
        elif "qmr-4" in hallu_type.lower():
            return self.qmr_4_generate_metamorphic_prompts(hallu_type)

