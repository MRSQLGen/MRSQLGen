from typing import Any, List, Dict, Tuple
import json
import os
from ..interfaces.prompt_transformer import PromptTransformer
current_dir = os.path.dirname(os.path.abspath(__file__))

class ConditionLogicHallucinationPromptTransformer(PromptTransformer):
    """
    ViolatingValueSpecificationPromptTransformer
    =======================
     LLM  question ，，（prompt paraphasing）。
    """
    def prompt_transformer_instruction_construct(self):
        #  prompt
        return "your constructed prompt here"

    def qmr_1_prompt_transformer_instruction_construct_equivalent(self, n) -> List[dict]:
        # 
        prompt = (
            f"Generate {n} simple English questions that are semantically equivalent to the following question but different from each other, "
            f"and whose corresponding SQL queries would also be logically equivalent. "
            f"You must achieve this by modifying only the condition logic descriptions (e.g., rephrasing logical connections, restructuring condition expressions) "
            f"without changing the query's overall meaning or result set.\n\n"
            
            f"Example 1:\n"
            f"Original question: Show orders with amount greater than 10000.\n"
            f"Equivalent question: Display all orders where the order amount exceeds 10000.\n"

            f"Example 2:\n"
            f"Original question: Show employees whose salary is between 5000 and 10000.\n"
            f"Equivalent question: Retrieve employees with salary greater than or equal to 5000 and less than or equal to 10000.\n"

            f"Example 3:\n"
            f"Original question: Find users aged between 18 and 25 and are female.\n"
            f"Equivalent question: Show all female users with age in the range of 18 to 25.\n"

            f"Example 4:\n"
            f"Original question: Find users who signed up before 2020.\n"
            f"Equivalent question: Retrieve all users whose signup date is earlier than January 1st, 2020.\n"

            f"Example 5:\n"
            f"Original question: Show users with income over 5000 and living in NY or LA.\n"
            f"Equivalent question: Display all users earning more than 5000 whose city is either NY or LA.\n"

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

    def qmr_1_prompt_transformer_instruction_construct_superset(self, n) -> List[dict]:
        # 
        prompt = (
            f"Generate {n} simple English questions whose corresponding SQL queries would return a superset of the original query's result set. "
            f"i.e., the generated query should include all results of the original query and potentially more. "
            f"The generated questions must be obtained by modifying only the condition logic descriptions (e.g., relaxing logical connections, broadening condition ranges, simplifying structures), "
            f"thus expanding the scope of the returned data without changing other parts of the question.\n\n"

            f"Example 1:\n"
            f"Original question: Show orders with amount greater than 10000.\n"
            f"Superset question: Display orders with amount greater than 5000.\n"

            f"Example 2:\n"
            f"Original question: Find employees whose salary is between 5000 and 10000.\n"
            f"Superset question: Retrieve employees whose salary is at least 5000 (without an upper limit).\n"

            f"Example 3:\n"
            f"Original question: Find users aged between 18 and 25 and are female.\n"
            f"Superset question: Show users who are female or aged between 18 and 25.\n"

            f"Example 4:\n"
            f"Original question: Find users who signed up before 2020.\n"
            f"Superset question: Find users who signed up before 2021.\n"

            f"Example 5:\n"
            f"Original question: Show users with income over 5000 and living in NY or LA.\n"
            f"Superset question: Show users with income over 5000 or living in NY or LA.\n"

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

    def qmr_1_prompt_transformer_instruction_construct_subset(self, n) -> List[dict]:
        # 
        prompt = (
            f"Generate {n} simple English questions whose corresponding SQL queries would return a subset of the original query's result set. "
            f"i.e., the generated query should include only a portion of the results of the original query. "
            f"The generated questions must be obtained by modifying only the condition logic descriptions (e.g., tightening logical connections, narrowing condition ranges, adding further restrictions), "
            f"thus reducing the scope of the returned data without changing other parts of the question.\n\n"

            f"Example 1:\n"
            f"Original question: Show orders with amount greater than 10000.\n"
            f"Subset question: Display orders with amount greater than 20000.\n"

            f"Example 2:\n"
            f"Original question: Find employees whose salary is between 5000 and 10000.\n"
            f"Subset question: Retrieve employees whose salary is strictly between 6000 and 9000.\n"

            f"Example 3:\n"
            f"Original question: Find users aged between 18 and 25 and are female.\n"
            f"Subset question: Show users who are female and aged between 20 and 22.\n"

            f"Example 4:\n"
            f"Original question: Find users who signed up before 2020.\n"
            f"Subset question: Retrieve users who signed up before 2019.\n"

            f"Example 5:\n"
            f"Original question: Show users with income over 5000 and living in NY or LA.\n"
            f"Subset question: Display users with income over 8000 and living only in NY.\n"

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
        transformer_instruction_equivalent = self.qmr_1_prompt_transformer_instruction_construct_equivalent(gene_num * 3)
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
        transformer_instruction_superset = self.qmr_1_prompt_transformer_instruction_construct_superset(gene_num)
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
        transformer_instruction_subset = self.qmr_1_prompt_transformer_instruction_construct_subset(gene_num)
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


    def qmr_2_prompt_transformer_instruction_construct_equivalent(self, n) -> List[dict]:
        # 
        prompt = (
            f"Rewrite the following question into {n} equivalent questions, which include both original question and logically decomposed step-by-step CoT instructions. "
            f"Each rewritten version must preserve the original question's meaning and result set, but explicitly decompose its logic into smaller steps (especially Condition Logic,e.g., filtering, joining). "    
            f"Your rewrites should focus only on logical decomposition, not on rephrasing or paraphrasing individual words.\n\n"
             
            f"Example 1:\n"
            f"Original question: Find employees with salary greater than 5000 and less than 10000.\n"
            f"Equivalent question: Find employees with salary greater than 5000 and less than 10000. CoT Steps:Filter employees with salary > 5000. Filter employees with salary < 10000.\n"

            f"Example 2:\n"
            f"Original question: Retrieve students who are either from New York or from Los Angeles and are older than 18.\n"
            f"Equivalent question: Retrieve students who are either from New York or from Los Angeles and are older than 18. CoT Steps:Filter students with city = 'New York' OR city = 'Los Angeles'.Filter students with age > 18.\n"

            f"Example 3:\n"
            f"Original question: Show products priced below 100 or above 1000, but only those in stock.\n"
            f"Equivalent question: Show products priced below 100 or above 1000, but only those in stock. CoT Steps:Filter products with price < 100 OR price > 1000. Filter products with stock > 0.\n"
            
            f"Now generate {n} equivalent questions for the following question:\n"
            f"Question: {self.question}\n"
            f"Do not include any explanations in your response. Ensure that return total {n} equivalent questions, each separated by a newline, totally {n} lines."
        )

        #  LLM （system + user）
        formatted_instruction = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ]
        return formatted_instruction

    def qmr_2_generate_metamorphic_prompts(self,  hallu_type) -> Tuple[List[str], List[str], Any]:
        """
         LLM ，。
        3，。
        """
        metamorphic_questions_temp = []
        mr_relations_temp = []
        completion_tokens = 0
        prompt_tokens = 0
        total_tokens = 0
        gene_num = self.n // 2# 

        # equivalent
        transformer_instruction_equivalent = self.qmr_2_prompt_transformer_instruction_construct_equivalent(gene_num)
        for attempt in range(1, 5):
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


    def qmr_3_prompt_transformer_instruction_construct_equivalent(self, n) -> List[dict]:
        # 
        prompt = (
            f"Rewrite the following question into {n} equivalent questions, which include both original question and explicit constraints about Condition Expression, making all implicit constraints about Condition Expression explicit."
            f"You should reformulate vague or underspecified instructions into precise control parameters, without changing the query's overall meaning or result set.\n\n"

            f"Example 1:\n"
            f"Original question: Show orders with amount greater than 10000.\n"
            f"Equivalent question: Show orders with amount greater than 10000.Explicit constraints about Condition Expression: Eexclude orders with amount equal to or less than 10000.\n"

            f"Example 2:\n"
            f"Original question: Show employees whose salary is between 5000 and 10000.\n"
            f"Equivalent question: Show employees whose salary is between 5000 and 10000. Explicit constraints about Condition Expression: Show employees whose salary is greater than or equal to 5000 and less than or equal to 10000, inclusive of both bounds.\n"

            f"Example 3:\n"
            f"Original question: Find users aged between 18 and 25 and are female.\n"
            f"Equivalent question: Find users aged between 18 and 25 and are female. Explicit constraints about Condition Expression: Find users whose age is greater than or equal to 18 and less than or equal to 25, and whose gender is explicitly female.\n"

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

    def qmr_3_generate_metamorphic_prompts(self,  hallu_type) -> Tuple[List[str], List[str], Any]:
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

        hallu_type_name = "Condition Logic Hallucination"
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
        if "qmr-2" in hallu_type.lower():
            return self.qmr_2_generate_metamorphic_prompts(hallu_type)
        if "qmr-3" in hallu_type.lower():
            return self.qmr_3_generate_metamorphic_prompts(hallu_type)
        elif "qmr-4" in hallu_type.lower():
            return self.qmr_4_generate_metamorphic_prompts(hallu_type)

