from typing import Any, List, Dict, Tuple
from .implements.basic_MRChecker import BasicMRChecker

def get_mr_checker_by_sql_type(hallu_type: str,sqlite_exec_one: Tuple[Any, int, str], sqlite_exec_two: Tuple[Any, int, str], sql_type: str):
    if "operator" in hallu_type.lower():
        return BasicMRChecker(sqlite_exec_one=sqlite_exec_one, sqlite_exec_two=sqlite_exec_two, sql_type=sql_type)
    elif "limit" in hallu_type.lower():
        return BasicMRChecker(sqlite_exec_one=sqlite_exec_one, sqlite_exec_two=sqlite_exec_two, sql_type=sql_type)
    elif "join" in hallu_type.lower():
        return BasicMRChecker(sqlite_exec_one=sqlite_exec_one, sqlite_exec_two=sqlite_exec_two, sql_type=sql_type)
    elif "columnnameopliteral" in hallu_type.lower():
        return BasicMRChecker(sqlite_exec_one=sqlite_exec_one, sqlite_exec_two=sqlite_exec_two, sql_type=sql_type)
    elif "column" in hallu_type.lower() and "columnnameopliteral" not in hallu_type.lower():
        return BasicMRChecker(sqlite_exec_one=sqlite_exec_one, sqlite_exec_two=sqlite_exec_two, sql_type=sql_type)
    elif "conditionexpression" in hallu_type.lower():
        return BasicMRChecker(sqlite_exec_one=sqlite_exec_one, sqlite_exec_two=sqlite_exec_two, sql_type=sql_type)
    elif "aggregationfunction" in hallu_type.lower():
        return BasicMRChecker(sqlite_exec_one=sqlite_exec_one, sqlite_exec_two=sqlite_exec_two, sql_type=sql_type)
    elif "distinct" in hallu_type.lower():
        return BasicMRChecker(sqlite_exec_one=sqlite_exec_one, sqlite_exec_two=sqlite_exec_two, sql_type=sql_type)
    elif "orderby" in hallu_type.lower():
        return BasicMRChecker(sqlite_exec_one=sqlite_exec_one, sqlite_exec_two=sqlite_exec_two, sql_type=sql_type)
    elif "groupby" in hallu_type.lower():
        return BasicMRChecker(sqlite_exec_one=sqlite_exec_one, sqlite_exec_two=sqlite_exec_two, sql_type=sql_type)
    elif "basic" in hallu_type.lower():
        return BasicMRChecker(sqlite_exec_one=sqlite_exec_one, sqlite_exec_two=sqlite_exec_two, sql_type=sql_type)

