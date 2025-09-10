from typing import Any, List, Dict, Tuple
from ..interfaces.prompt_transformer import PromptTransformer

class BasicPromptTransformer(PromptTransformer):
    """
    BasicPromptTransformer
    =======================
    PromptTransformer 。
     LLM  question （prompt paraphasing）。
    """
    def prompt_transformer_instruction_construct(self) -> List[dict]:
        """
         LLM  prompt instruction。
         N 。
        """

        prompt = (f"Generate {self.n} different questions that are semantically equivalent to the following question."
                  f"Question: {self.question})"
                  f"Do not answer any explanations. Just return the {self.n} equivalent questions, each separated by a newline.")
        #  LLM （system + user）
        formatted_instruction = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ]
        self.transformer_instruction = formatted_instruction
        return self.transformer_instruction

    def generate_metamorphic_prompts(self, hallu_type) -> Tuple[List[str], List[str], Any]:
        """
         LLM ，。
        3，。
        """
        if len(self.transformer_instruction) == 0:
            self.prompt_transformer_instruction_construct()

        mr_relations = []
        for attempt in range(1, 4):
            answer, _usage = self.llm_client.generate(self.transformer_instruction)
            self.metamorphic_prompts = answer
            self.trans_usage = _usage
            split_questions = self.metamorphic_prompts_process(answer)
            if len(split_questions) == self.n:
                self.metamorphic_questions = split_questions
                mr_relations.extend(["equivalent"] * self.n)
                break
        return self.metamorphic_questions, mr_relations, self.trans_usage
