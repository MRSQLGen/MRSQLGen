from typing import Any, List, Dict, Tuple
from ..interfaces.MRChecker import MRChecker

class BasicMRChecker(MRChecker):
    def check(self, mode: str = "equivalent", strict: bool = False) -> bool:
        if self.sql_type == "SELECT":
            return self._check_select_result(mode=mode, strict=strict)
        elif self.sql_type in {"INSERT", "UPDATE", "DELETE"}:
            return self._check_effected_rows()
        else:
            raise ValueError(f"Unsupported SQL type: {self.sql_type}")

    def _check_select_result(self, mode: str = "equivalent", strict: bool = False) -> Any:
        result_one, _, err_one = self.result_one, self.rowcount_one, self.result_error_one
        result_two, _, err_two = self.result_two, self.rowcount_two, self.result_error_two

        if len(err_one) or len(err_two):
            return "error"

        set_one = result_one if strict else set(result_one)
        set_two = result_two if strict else set(result_two)

        if mode == "equivalent":
            return result_one == result_two if strict else set_one == set_two
        elif mode == "subset":
            return set(result_two).issubset(set(result_one))
            # return set_two <= set_one
        elif mode == "superset":
            return set(result_one).issubset(set(result_two))
            # return set_one <= set_two
        else:
            raise ValueError(f"Unsupported comparison mode: {mode}")

    def _check_effected_rows(self) -> Any:
        _, rowcount_one, err_one = self.result_one, self.rowcount_one, self.result_error_one
        _, rowcount_two, err_two = self.result_two, self.rowcount_two, self.result_error_two

        # ，，MR
        if len(err_one) or len(err_two):
            return "error"

        return rowcount_one == rowcount_two
