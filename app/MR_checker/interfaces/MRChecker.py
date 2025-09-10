from __future__ import annotations
import os
from abc import ABC, abstractmethod
from importlib.metadata import metadata
from os.path import split
from typing import Any, List, Dict, Tuple

class MRChecker(ABC):
    def __init__(
        self,
        sqlite_exec_one: Tuple[Any, int, str],
        sqlite_exec_two: Tuple[Any, int, str],
        sql_type: str  # "SELECT" / "INSERT" / "UPDATE" / "DELETE"
    ) -> None:
        self.result_one, self.rowcount_one, self.result_error_one = sqlite_exec_one
        self.result_two, self.rowcount_two, self.result_error_two = sqlite_exec_two
        self.sql_type = sql_type.upper()

    @abstractmethod
    def check(self, **kwargs) -> bool:

        pass







