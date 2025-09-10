

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, List, Dict, Tuple
import re


class SQLGenerator(ABC):
    """
    Abstract Class: Defines a general interface for generating SQL from natural language questions and executing it.

    Abstract base class for SQL generation via LLM and execution on SQLite.

    Used in the Generating Component and Validating Component modules of DIAL-SQL:
    - prompt -> LLM -> TargetQuery
    - TargetQuery -> SQLite -> TargetResult
    """

    def __init__(
        self,
        llm_client: Any,          # （ GPTClient）
        db_connector: Any,        # （ SqliteConnector）
        prompt_generator: Any,    # prompt（ NumberSignCOTPrompt）
        metadata: Dict = None     # （db_id, question, tables ）
    ) -> None:
        self.llm_client = llm_client
        self.db_connector = db_connector
        self.prompt_generator = prompt_generator
        self.metadata = metadata

        # （ metadata ）
        self.db_id: str = ""
        self.answer_query: str = ""     # ground-truth SQL（）
        self.question: str = ""         #
        self.tables: Any = None         #
        self.prompt_messages: List[dict] = []  #  LLM  prompt
        self.predict_query: str = ""    # LLM  SQL
        self.gene_usage: (int, int, int) = (0, 0, 0)

        if metadata:
            self.db_id = metadata.get("db_id", "")
            self.answer_query = metadata.get("query", "")
            self.question = metadata.get("question", "")
            self.tables = metadata.get("tables", None)

    @abstractmethod
    def prompt_messages_construct(self) -> List[dict]:
        raise NotImplementedError

    @abstractmethod
    def generate_target_query(self) -> Tuple[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def extract_sql_code_block(self,response:str) -> str:
        raise NotImplementedError

    @abstractmethod
    def execute_target_query(self) -> Tuple[Any, int, str]:

        raise NotImplementedError

class DefaultSQLGenerator(SQLGenerator):
    """
    DefaultSQLGenerator:
    Default implementation based on the combination of GPT and SQLite, using NumberSignCOTPrompt to construct prompts.

    This class defines the default SQL generation behavior using:
    - GPT-style LLM
    - SQLite backend
    - DIAL-SQL style prompt template
    """

    def prompt_messages_construct(self) -> List[dict]:
        prompt_generator = self.prompt_generator
        prompt = prompt_generator.format_target(self.metadata)
        formatted_prompt = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ]
        self.prompt_messages = formatted_prompt
        return formatted_prompt

    def generate_target_query(self) -> Tuple[str, Any]:
        if len(self.prompt_messages) == 0:
            self.prompt_messages_construct()
        sql, self.gene_usage = self.llm_client.generate(self.prompt_messages)
        # print("LLM ：", sql)
        self.predict_query = self.extract_sql_code_block(sql)
        # print(" SQL ：", self.predict_query)
        return self.predict_query, self.gene_usage

    def extract_sql_code_block(self, response: str) -> str:
        final_result = ""
        pattern = r"```sql\s*([\s\S]+?)\s*```"
        match = re.search(pattern, response, re.IGNORECASE)
        if match:
            final_result=match.group(1).strip()
            #  "ite"，
            if final_result.startswith("ite"):
                final_result = final_result[3:].lstrip()
            return final_result
        else:
            #  "ite"，
            if response.startswith("ite"):
                final_result = response[3:].lstrip()
            else:
                final_result = response.lstrip()
            return final_result


    def execute_target_query(self) -> Tuple[Any, int, str]:
        if self.predict_query == "":
            self.generate_target_query()
        return self.db_connector.execute(self.predict_query)


