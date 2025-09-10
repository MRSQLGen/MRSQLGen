from typing import Any
from sqlglot.expressions import Expression
from typing import Dict
from sqlglot import parse_one, exp
from typing import Tuple, Type
import json

class SQLNormalization:
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

    def is_literal_or_literals(self, e):
        # （ NULL、CURRENT_TIMESTAMP ）
        #
        if isinstance(e, exp.Literal):
            # return e.is_string or e.is_int or e.is_number
            return True
        elif isinstance(e, list):
            return all(self.is_literal_or_literals(x) for x in e)
        return False

    def is_column_op_literal_expr(self,expr):
        """
         Column OP Literal(s) ，
         OP  [=, !=, LIKE, IN, NOT IN, IS, IS NOT, GLOB]
        """

        allowed_ops = (
            exp.EQ, exp.NEQ, exp.LT, exp.LTE, exp.GT,exp.GTE,
            exp.Like, exp.In,exp.In, exp.Is, exp.Is, exp.Glob
        )

        if not isinstance(expr, allowed_ops):
            return False

        left = expr.args.get("this")
        right = expr.args.get("expression") or expr.args.get("expressions")

        if isinstance(left, exp.Column) and self.is_literal_or_literals(right):
            return True
        if isinstance(right, exp.Column) and self.is_literal_or_literals(left):
            return True

        return False


    @staticmethod
    def is_Operator(node: Expression):
        arithmetic_operators: Tuple[Type[exp.Expression], ...] = (
            # arithmetic_operators
            exp.Add,
            exp.Sub,
            exp.Mul,
            exp.Div,
            exp.Mod,
            exp.BitwiseLeftShift,
            exp.BitwiseRightShift,
            exp.BitwiseAnd,
            exp.BitwiseOr
        )

        comparison_operators: Tuple[Type[exp.Expression], ...] = (
            # comparison_operators
            exp.EQ,
            exp.NEQ,
            exp.EQ,
            exp.LT,
            exp.LTE,
            exp.GT,
            exp.GTE
        )

        logical_operators: Tuple[Type[exp.Expression], ...] = (
            # logical_operators
            exp.And,
            exp.Or,
            exp.Not,
            exp.Like,
            exp.Exists,
            exp.In,
            exp.In,
            exp.Between,
            exp.Is,
            exp.Is,
            exp.Glob
        )

        operators_misuse_nodes: Tuple[Type[exp.Expression], ...] = tuple(dict.fromkeys(
            arithmetic_operators + comparison_operators + logical_operators
        ))
        #  operator
        if isinstance(node, operators_misuse_nodes):
            return True
        else:
            return False

    @staticmethod
    def is_LIMIT(node: Expression):
        #  limit
        return isinstance(node, exp.Limit) or isinstance(node,exp.Offset)

    @staticmethod
    def is_Join(node: Expression):
        #  join
        return isinstance(node, exp.Join)

    def is_ColumnNameOPLiteral(self, node: Expression):
        #  Violating Value Specification
        return self.is_column_op_literal_expr(node)

    @staticmethod
    def is_Column(node: Expression):
        #  Column Selection Error
        return isinstance(node, exp.Column)

    @staticmethod
    def is_ConditionExpression(node: Expression):
        condition_parent_nodes = (
            exp.Where,
            exp.Join,
            exp.OnCondition,
            exp.Having,
            exp.Case,
            exp.When,
            exp.Check,
            exp.CheckColumnConstraint,
            exp.ChecksumProperty,
            exp.Exists
        )
        return isinstance(node, condition_parent_nodes)

    @staticmethod
    def is_AggregationFunction(node:Expression):
        #  Aggregation Function Misuse
        flag = False
        if isinstance(node, exp.AggFunc):
            flag = True
        if node.__class__.__name__ in ("Function", "Anonymous"):
            func_name = getattr(node, "this", "").lower()
            if func_name in {"total"}:
                flag = True
        return flag

    @staticmethod
    def is_Distinct(node:Expression):
        #  Distinct Error
        return isinstance(node, exp.Distinct)

    @staticmethod
    def is_OrderBy(node: Expression):
        #  OrderBy Misuse
        return isinstance(node, exp.Order)

    @staticmethod
    def is_GroupBy(node: Expression):
        #  GroupBy Misuse
        return isinstance(node, exp.Group)

    @staticmethod
    def normalize_node(node: Expression):
        """
        AST：
        -  T1, T2...
        -  T, T2...
        -  T1
        """
        if isinstance(node, exp.Boolean):
            #  TRUE  FALSE
            # node.set("this", "[Boolean]")
            pass
        elif isinstance(node, exp.Table):
            # ：Table ， students
            node.set("this", "[TableName]")  # students → T1
        elif isinstance(node, exp.TableAlias):
            # ：TableAlias
            node.set("this", "[TableAlias]")  # students → T1
        elif isinstance(node, exp.Alias):
            # ：SELECT name AS n
            alias_expr = node.args.get("alias")
            value_expr = node.args.get("this")  #
            if alias_expr and isinstance(alias_expr, exp.Identifier):
                #  this  Table ，
                if not isinstance(value_expr, exp.Table):
                    alias_expr.set("this", "[ColumnAlias]")
        elif isinstance(node, exp.Column):
            # :Column  s.name、students.id
            table_prefix = node.args.get("table")
            if table_prefix:
                table_prefix.set("this", "[TablePrefix]")  # s → T1

            #
            node.set("this", "[ColumnName]")
        elif isinstance(node, exp.Literal):
            value = node.this  #
            is_string = node.is_string

            # （'abc'）
            if is_string:
                if value.startswith("X'") or value.startswith("x'"):
                    #  BLOB
                    # print("BLOB literal:", value)
                    node.set("this", "[BLOB]")
                else:
                    # print("String literal:", value)
                    node.set("this", "[String]")
            #
            else:
                if "." in value or "e" in value.lower():
                    # print("Real (float) literal:", value)
                    node.set("this", "[RealNumber]")
                else:
                    # print("Integer literal:", value)
                    node.set("this", "[Integer]")
        elif isinstance(node, exp.HexString):
            # Integer（Integer Literals）:(exp.HexString)
            node.set("this", "[HexString]")
        return

    def dfs_normalize(self, node: Expression):
        """
         AST
        """
        self.normalize_node(node)  # （）

        for child in node.args.values():
            if isinstance(child, Expression):
                self.dfs_normalize(child)
            elif isinstance(child, list):
                for item in child:
                    if isinstance(item, Expression):
                        self.dfs_normalize(item)


    def get_normalized_ast_json(self, node: Expression, hallucination_flags: Dict[str, bool], structured_sql: Dict):
        """
         sqlglot AST  JSON
        """
        if node is None:
            return None, None

        # 2. Normalize （ node）
        self.normalize_node(node)

        # 1.  hallucination
        if self.is_Operator(node):
            hallucination_flags["Operator"] = True
            structured_sql["Operator"].append(node.sql())
        if self.is_LIMIT(node):
            hallucination_flags["LIMIT"] = True
            structured_sql["LIMIT"].append(node.sql())
        if self.is_Join(node):
            hallucination_flags["Join"] = True
            structured_sql["Join"].append(node.sql())
        if self.is_ColumnNameOPLiteral(node):
            hallucination_flags["ColumnNameOPLiteral"] = True
            structured_sql["ColumnNameOPLiteral"].append(node.sql())
        if self.is_Column(node):
            hallucination_flags["Column"] = True
            structured_sql["Column"].append(node.sql())
        if self.is_ConditionExpression(node):
            hallucination_flags["ConditionExpression"] = True
            structured_sql["ConditionExpression"].append(node.sql())
        if self.is_AggregationFunction(node):
            hallucination_flags["AggregationFunction"] = True
            structured_sql["AggregationFunction"].append(node.sql())
        if self.is_Distinct(node):
            hallucination_flags["Distinct"] = True
            structured_sql["Distinct"].append(node.sql())
        if self.is_OrderBy(node):
            hallucination_flags["OrderBy"] = True
            structured_sql["OrderBy"].append(node.sql())
        if self.is_GroupBy(node):
            hallucination_flags["GroupBy"] = True
            structured_sql["GroupBy"].append(node.sql())

        # 3.
        children = list(node.iter_expressions())
        if not children:
            # ： normalized SQL
            normalized_sql = node.sql()
            return normalized_sql, normalized_sql

        result = {"type": node.__class__.__name__}

        # （args）
        # args
        for arg_key, arg_value in node.args.items():
            if isinstance(arg_value, list):
                # list，
                temp = []
                for child in arg_value:
                    if isinstance(child, Expression):
                        result_temp, node_temp = self.get_normalized_ast_json(child, hallucination_flags, structured_sql)
                        temp.append(result_temp)
                    else:
                        temp.append(child)
                if len(temp):
                    result[arg_key] = temp
            elif isinstance(arg_value, Expression):
                #  Expression
                result_temp, node_temp = self.get_normalized_ast_json(arg_value, hallucination_flags, structured_sql)
                result[arg_key] = result_temp
            else:
                # （）：（ None，，）
                if not arg_value:
                    # None，astjson
                    continue
                result[arg_key] = arg_value

        # 4.  normalize ， SQL
        normalized_sql = node.sql()
        return result, normalized_sql

    def get_ast_json(self, node: Expression, hallucination_flags: Dict[str, bool], structured_sql: Dict):
        """
         sqlglot AST  JSON
        """
        if node is None:
            return None, None

        # 1.  hallucination
        if self.is_Operator(node):
            hallucination_flags["Operator"] = True
            structured_sql["Operator"].append(node.sql())
        if self.is_LIMIT(node):
            hallucination_flags["LIMIT"] = True
            structured_sql["LIMIT"].append(node.sql())
        if self.is_Join(node):
            hallucination_flags["Join"] = True
            structured_sql["Join"].append(node.sql())
        if self.is_ColumnNameOPLiteral(node):
            hallucination_flags["ColumnNameOPLiteral"] = True
            structured_sql["ColumnNameOPLiteral"].append(node.sql())
        if self.is_Column(node):
            hallucination_flags["Column"] = True
            structured_sql["Column"].append(node.sql())
        if self.is_ConditionExpression(node):
            hallucination_flags["ConditionExpression"] = True
            structured_sql["ConditionExpression"].append(node.sql())
        if self.is_AggregationFunction(node):
            hallucination_flags["AggregationFunction"] = True
            structured_sql["AggregationFunction"].append(node.sql())
        if self.is_Distinct(node):
            hallucination_flags["Distinct"] = True
            structured_sql["Distinct"].append(node.sql())
        if self.is_OrderBy(node):
            hallucination_flags["OrderBy"] = True
            structured_sql["OrderBy"].append(node.sql())
        if self.is_GroupBy(node):
            hallucination_flags["GroupBy"] = True
            structured_sql["GroupBy"].append(node.sql())

        # 3.
        children = list(node.iter_expressions())
        if not children:
            #  sql()
            return node.sql(), node.sql()

        result = {"type": node.__class__.__name__}

        # （args）
        # args
        for arg_key, arg_value in node.args.items():
            if isinstance(arg_value, list):
                # list，
                temp = []
                for child in arg_value:
                    if isinstance(child, Expression):
                        result_temp, node_temp = self.get_ast_json(child, hallucination_flags, structured_sql)
                        temp.append(result_temp)
                    else:
                        temp.append(child)
                if len(temp):
                    result[arg_key] = temp
            elif isinstance(arg_value, Expression):
                #  Expression
                result_temp, node_temp = self.get_ast_json(arg_value, hallucination_flags, structured_sql)
                result[arg_key] = result_temp
            else:
                # （）：（ None，，）
                if not arg_value:
                    # None，astjson
                    continue
                result[arg_key] = arg_value
        return result, node.sql()

    def sql_normalize(self, dialect):
        HType = {
            "Operator": False,
            "LIMIT": False,
            "Join": False,
            "ColumnNameOPLiteral": False,
            "Column": False,
            "ConditionExpression": False,
            "AggregationFunction": False,
            "Distinct": False,
            "OrderBy": False,
            "GroupBy": False
        }

        structured_sql = {
            "Operator": [],
            "LIMIT": [],
            "Join": [],
            "ColumnNameOPLiteral": [],
            "Column": [],
            "ConditionExpression": [],
            "AggregationFunction": [],
            "Distinct": [],
            "OrderBy": [],
            "GroupBy": []
        }

        normalized_structured_sql = {
            "Operator": [],
            "LIMIT": [],
            "Join": [],
            "ColumnNameOPLiteral": [],
            "Column": [],
            "ConditionExpression": [],
            "AggregationFunction": [],
            "Distinct": [],
            "OrderBy": [],
            "GroupBy": []
        }

        # SQL -> nodeastsql
        tree = parse_one(self.query, dialect=dialect)
        json_ast,original_sql = self.get_ast_json(tree, HType, structured_sql)


        tree_for_normalize = parse_one(self.query, dialect=dialect)
        self.dfs_normalize(tree_for_normalize)
        normalized_json_ast, normalized_sql = self.get_ast_json(tree_for_normalize, HType,normalized_structured_sql)

        # print(json.dumps(normalized_json_ast, indent=2, ensure_ascii=False))
        # print(normalized_sql)
        # print(json.dumps(normalized_structured_sql, indent=2, ensure_ascii=False))
        return json_ast,original_sql, structured_sql, normalized_json_ast, normalized_sql, normalized_structured_sql, HType

