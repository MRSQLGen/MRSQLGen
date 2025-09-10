from __future__ import annotations
import os
from abc import ABC, abstractmethod
from importlib.metadata import metadata
from os.path import split
from typing import Any, List, Dict, Tuple

class PromptTransformer(ABC):
    """
    Abstract Class: PromptTransformer
    =================================
    This class defines the interface for prompt rewriting, which is used to generate multiple
    metamorphic questions (MR-conformant but with different forms) based on the input question and context.

    This is the abstract base class for all PromptTransformer implementations. It defines a unified interface
    to construct metamorphic prompts using LLMs for hallucination analysis.

    Subclasses must implement the following three abstract methods:
    - prompt_transformer_instruction_construct()
    - generate_metamorphic_prompts()
    - metamorphic_prompts_process()
    """

    def __init__(
        self,
        llm_client: Any,
        n: int,
        metadata: Dict = None  # 用于初始化中间值的可选输入
    ) -> None:
        """
        Initialize a PromptTransformer object.

        :param llm_client: LLM interface client (e.g., an OpenAI API wrapper)
        :param n: Number of sentences to generate that satisfy the MR
        :param metadata: Optional task context, including db_id, question, tables, etc.
        """

        self.llm_client = llm_client
        self.n = n
        self.metadata = metadata

        # 默认中间值字段（可由 metadata 初始化）
        self.db_id: str = ""
        self.question: str = ""
        self.tables: Any = None
        self.transformer_instruction: List[dict] = []
        self.metamorphic_prompts: str = ""
        self.metamorphic_questions: List[str] = []
        self.trans_usage: (int, int, int) = (0,0,0)


        if metadata:
            self.db_id = metadata.get("db_id", "")
            self.question = metadata.get("question", "")
            self.tables = metadata.get("tables", None)

    @abstractmethod
    def prompt_transformer_instruction_construct(self) -> List[dict]:
        raise NotImplementedError

    @abstractmethod
    def generate_metamorphic_prompts(self,  hallu_type: str) -> Tuple[List[str], List[str], Any]:
        raise NotImplementedError

    def metamorphic_prompts_process(self, answer: str) -> List[str]:
        split_answer = answer.strip().split('\n')
        for item in split_answer:
            if len(item) == 0:
                split_answer.remove(item)
        return split_answer






