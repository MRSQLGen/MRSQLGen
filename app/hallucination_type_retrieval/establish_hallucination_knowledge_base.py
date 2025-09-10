import os
import json
from app.hallucination_type_retrieval.question_normalization import QuestionNormalization
from app.hallucination_type_retrieval.sql_normalization import SQLNormalization


class EstablishHallucinationKnowledgeBase:
    def __init__(
        self,
        api_key: str,
        api_base: str,
        model_name: str = "gpt-3.5-turbo",
        temperature: float = 0.0
    ):
        os.environ["OPENAI_API_KEY"] = api_key
        os.environ["OPENAI_API_BASE"] = api_base
        self.model_name = model_name
        self.temperature = temperature

    def run(self, input_json_path: str, dataset_dic: str,output_dic_path: str,output_merge_dic_path: str,item_num: int = 5):
        os.makedirs(output_dic_path, exist_ok=True)
        if not os.path.exists(input_json_path):
            print(f"Not exist {input_json_path}")
            return

        #
        with open(input_json_path, "r", encoding="utf-8") as r:
            contents = json.load(r)

        if item_num >= len(contents):
            item_num = len(contents)

        # 0. ，
        with open(os.path.join(output_dic_path,"config.json"),"w", encoding="utf-8") as w:
            config = {
                "model_name": self.model_name,
                "temperature":self.temperature,
                "input_json_path": input_json_path,
                "output_dic_path": output_dic_path,
                "item_num":item_num
            }
            json.dump(config,w,indent=4)

        for content in contents[:item_num]:
            #
            index_dic_path = os.path.join(output_dic_path, str(content["index"]))
            index = content["index"]
            if not os.path.exists(index_dic_path):
                os.makedirs(index_dic_path, exist_ok=True)

            print(f"：{str(index)}")

            # 1. SQL Normalization
            sql_normalization_json = os.path.join(index_dic_path, "sql_normalization.json")
            node_type_json = os.path.join(index_dic_path, "node_type.json")
            structured_query = None
            if not os.path.exists(sql_normalization_json):
                sql_normalizer = SQLNormalization({"query": content["query"]})
                _, _, structured_query, _, normalized_query, normalized_structured_query, node_type = sql_normalizer.sql_normalize("sqlite")
                with open(sql_normalization_json, "w", encoding="utf-8") as w:
                    json.dump({"query":content["query"],"structured_query": structured_query, "normalized_query": normalized_query, "normalized_structured_query": normalized_structured_query},w,indent=4)
                with open(node_type_json, "w", encoding="utf-8") as w:
                    json.dump(node_type, w, indent=4)
            else:
                with open(sql_normalization_json, "r", encoding="utf-8") as r:
                    temp = json.load(r)
                    structured_query = temp["structured_query"]
                    normalized_query = temp["normalized_query"]
                    normalized_structured_query = temp["normalized_structured_query"]
                with open(node_type_json, "r", encoding="utf-8") as r:
                    node_type = json.load(r)

            # 2. Question Normalization
            question_normalization_json = os.path.join(index_dic_path, "question_normalization.json")
            if not os.path.exists(question_normalization_json):
                question_normalizer = QuestionNormalization(metadata=content)
                normalized_question = question_normalizer.question_normalize()
                with open(question_normalization_json, "w", encoding="utf-8") as w:
                    json.dump({"question":content["question"], "normalized_question": normalized_question},w,indent=4)
            else:
                with open(question_normalization_json, "r", encoding="utf-8") as r:
                    temp = json.load(r)
                normalized_question = temp["normalized_question"]

            # 3 . map the question and query
            hkb_whole_json = os.path.join(index_dic_path, "hkb_whole.json")
            hkb_whole = [{"index":index, "node_type": node_type,  "question": normalized_question, "query": normalized_query}]
            if not os.path.exists(hkb_whole_json):
                with open(hkb_whole_json, "w", encoding="utf-8") as w:
                    json.dump(hkb_whole,w,indent=4)
            print(f"：{str(index)}")

        # 3. merge HallucinationKnowledgeBase to dic HallucinationKnowledgeBaseMerge
        merge_hkb_whole = []
        for content in contents[:item_num]:
            #
            index_dic_path = os.path.join(output_dic_path, str(content["index"]))
            with open(os.path.join(index_dic_path,"hkb_whole.json"), "r", encoding="utf-8") as r:
                temp = json.load(r)
            merge_hkb_whole.extend(temp)
        with open(os.path.join(output_merge_dic_path, "merge_hkb_whole.json"), "w", encoding="utf-8") as w:
            json.dump(merge_hkb_whole, w, indent=4)