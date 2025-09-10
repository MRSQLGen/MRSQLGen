from typing import Any, List, Dict, Tuple
import sqlglot
import json
from sqlglot.expressions import Expression
from typing import Dict
from sqlglot import parse_one, exp
from collections import OrderedDict
from typing import Tuple, Type
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
import time
import spacy
nlp = spacy.load("en_core_web_sm")  #  en_core_web_lg


class QuestionNormalization:
    def __init__(
        self,
        metadata: Dict = None  #
    ) -> None:
        self.metadata = metadata

        # （ metadata ）
        self.db_id: str = ""
        self.query: str = ""
        self.question: str = ""
        self.tables: Any = None

        if metadata:
            self.db_id = metadata.get("db_id", "")
            self.query = metadata.get("query", "")
            self.question = metadata.get("question", "")
            self.tables = metadata.get("tables", None)

    def normalize_text(self, text):
        doc = nlp(text)
        tokens = []
        for token in doc:
            if token.pos_ in ["NOUN", "PROPN"]:  # 、
                tokens.append("[NOUN]")
            elif token.like_num:
                tokens.append("[NUMBER]")
            else:
                tokens.append(token.text)
        return " ".join(tokens)

    def normalize_structured_question(self, structured_question):
        if type(structured_question) != dict:
            return {}
        else:
            normalized_structured_question = {}
        for key, value in structured_question.items():
            new_items = []
            for item in value:
                new_items.append(self.normalize_text(item))
            normalized_structured_question[key] = new_items
        return normalized_structured_question

    def question_normalize(self):
        normalized_question = self.normalize_text(self.question)
        return normalized_question








