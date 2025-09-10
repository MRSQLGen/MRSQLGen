from .implements.basic_prompt_transformer import BasicPromptTransformer
from .implements.operator_misuse_prompt_transformer import OperatorMisusePromptTransformer
from .implements.limit_error_prompt_transformer import LimitErrorPromptTransformer
from .implements.violating_value_specification_prompt_transformer import ViolatingValueSpecificationPromptTransformer
from .implements.column_selection_error_prompt_transformer import ColumnSelectionErrorPromptTransformer
from .implements.condition_logic_hallucination_prompt_transformer import ConditionLogicHallucinationPromptTransformer
from .implements.join_logic_hallucination_prompt_transformer import JoinLogicHallucinationPromptTransformer
from .implements.aggregation_function_misuse_prompt_transformer import AggregationFunctionMisusePromptTransformer
from .implements.distinct_error_prompt_transformer import DistinctErrorPromptTransformer
from .implements.orderby_misuse_prompt_transformer import OrderByMisusePromptTransformer
from .implements.groupby_misuse_prompt_transformer import GroupByMisusePromptTransformer

def get_prompt_transformer_by_hallucination_type(hallu_type: str, llm_client, n: int, metadata):
    """
    Return the corresponding PromptTransformer instance based on the Hallucination Type.
    Factory method that selects the appropriate PromptTransformer implementation based on hallucination type.

    :param hallu_type: Hallucination type identifier, e.g., "basic"
    :param llm_client: Client object for communicating with the LLM
    :param n: Number of MR relation questions to generate
    :param metadata: Dictionary containing contextual information such as question / db_id / tables
    :return: An instance of a PromptTransformer subclass
    """

    print(hallu_type)
    if "operator" in hallu_type.lower():
        return OperatorMisusePromptTransformer(llm_client=llm_client, n=n, metadata=metadata)
    elif "limit" in hallu_type.lower():
        return LimitErrorPromptTransformer(llm_client=llm_client, n=n, metadata=metadata)
    elif "join" in hallu_type.lower():
        return JoinLogicHallucinationPromptTransformer(llm_client=llm_client, n=n, metadata=metadata)
    elif "columnnameopliteral" in hallu_type.lower():
        return ViolatingValueSpecificationPromptTransformer(llm_client=llm_client, n=n, metadata=metadata)
    elif "column" in hallu_type.lower() and "columnnameopliteral" not in hallu_type.lower():
        return ColumnSelectionErrorPromptTransformer(llm_client=llm_client, n=n, metadata=metadata)
    elif "conditionexpression" in hallu_type.lower():
        return ConditionLogicHallucinationPromptTransformer(llm_client=llm_client, n=n, metadata=metadata)
    elif "aggregationfunction" in hallu_type.lower():
        return AggregationFunctionMisusePromptTransformer(llm_client=llm_client, n=n, metadata=metadata)
    elif "distinct" in hallu_type.lower():
        return DistinctErrorPromptTransformer(llm_client=llm_client, n=n, metadata=metadata)
    elif "orderby" in hallu_type.lower():
        return OrderByMisusePromptTransformer(llm_client=llm_client, n=n, metadata=metadata)
    elif "groupby" in hallu_type.lower():
        return GroupByMisusePromptTransformer(llm_client=llm_client, n=n, metadata=metadata)
    elif "basic" in hallu_type.lower():
        return BasicPromptTransformer(llm_client=llm_client, n=n, metadata=metadata)
