import os
import json
import shutil
import copy
from typing import List, Tuple
from app.gpt_client import GPTClient
from app.dbms_connectors.implements.sqlite_connector import SqliteConnector
from app.Tools.load_table_schema import load_database_table_schema
from app.DAIL_SQL_Prompt.PromptReprTemplate import NumberSignCOTPrompt
from app.sql_generator import DefaultSQLGenerator
from app.prompt_transformer.transformer_factory import get_prompt_transformer_by_hallucination_type
from app.bug_detector import BugDetector
from app.evaluation_manager import EvaluationManager
from app.MR_checker.MRChecker_factory import get_mr_checker_by_sql_type
from app.hallucination_type_retrieval.hallucination_type_identify import HallucinationTypeIdentify
from app.hallucination_type_retrieval.question_normalization import QuestionNormalization
from app.hallucination_type_retrieval.sql_normalization import SQLNormalization
import time
current_file_path = os.path.abspath(__file__)
current_dir = os.path.dirname(current_file_path)

class ExperimentRunner:
    def __init__(
        self,
        llm_model_config_file: str,
        runner_config_file: str,
        sql_type: str = "SELECT",
        strict: bool = True
    ):
        if not os.path.exists(llm_model_config_file):
            print(f"{llm_model_config_file} doesn't exist.")
            return
        with open(llm_model_config_file, "r", encoding="utf-8") as r:
            llm_model_config = json.load(r)
        os.environ["OPENAI_API_KEY"] = llm_model_config.get('api_key', '')
        os.environ["OPENAI_API_BASE"] = llm_model_config.get('api_base', '')
        self.model_name = llm_model_config.get('model_name', 'gpt-4o-mini')
        self.llm_type = llm_model_config.get('llm_type', 'general-purpose')
        self.url = llm_model_config.get('url', '')
        self.stream = llm_model_config.get('stream', '')

        if not os.path.exists(runner_config_file):
            print(f"{runner_config_file} doesn't exist.")
            return
        with open(runner_config_file, "r", encoding="utf-8") as r:
            runner_config = json.load(r)

        self.temperature = runner_config.get('temperature',0.0)
        self.n = runner_config.get('n', 10)
        self.sql_type = sql_type.upper()
        self.strict = strict
        self.threshold_cross_validation = runner_config.get('threshold_cross_validation', 0.8)
        self.top_match_k = runner_config.get('top_match_k', 10)
        self.threshold_similarity = runner_config.get('threshold_similarity', 0.75)
        self.ablation = runner_config.get('ablation',False)

        self.hkb_path = os.path.join(current_dir, "..", "HallucinationKnowledgeBaseMerge", "merge_hkb_whole.json")
        self.hkb_cache_path = os.path.join(current_dir, "..", "HallucinationKnowledgeBaseMerge","merge_hkb_whole_cache.npy")

        # 0.75s: gpt = GPTClient
        self.gpt_generating_component = GPTClient(
            model_name=self.model_name,
            llm_type=self.llm_type,
            temperature= self.temperature,
            api_key=os.getenv("OPENAI_API_KEY"),
            api_base=os.getenv("OPENAI_API_BASE"),
            url=self.url,
            stream=self.stream
        )

        self.gpt_prompt_paraphasing = GPTClient(
            model_name=self.model_name,
            llm_type=self.llm_type,
            temperature=self.temperature,
            api_key=os.getenv("OPENAI_API_KEY"),
            api_base=os.getenv("OPENAI_API_BASE"),
            url=self.url,
            stream=self.stream
        )

    def run(self, input_json_path: str, dataset_name: str,dataset_dic:str, output_dic_path: str, item_num: int = 5):
        output_dic_path = os.path.join(output_dic_path, f"mr-sqlgen_{dataset_name}_{self.model_name.replace(':', '-')}")
        os.makedirs(output_dic_path, exist_ok=True)
        if not os.path.exists(input_json_path):
            return

        token_cnt_total = []

        with open(os.path.join(output_dic_path,"config.json"),"w", encoding="utf-8") as w:
            config = {
                "model_name": self.model_name,
                "temperature":self.temperature,
                "n":self.n,
                "threshold_cross_validation": self.threshold_cross_validation,
                "top_match_k" : self.top_match_k,
                "threshold_similarity" : self.threshold_similarity,
                "input_json_path": input_json_path,
                "output_dic_path": output_dic_path,
                "item_num":item_num
            }
            json.dump(config,w,indent=4)

        with open(input_json_path, "r", encoding="utf-8") as r:
            contents = json.load(r)

        # Hallucination Type Identify
        matcher = HallucinationTypeIdentify(model_name='bert-base-uncased', device=None, hkb_path=self.hkb_path,
                                            hkb_cache_path=self.hkb_cache_path)
        if not matcher.hkb_units:
            matcher.build_hkb()

        for content in contents[:item_num]:
            types_identify_qmr = {}
            index_dic_path = os.path.join(output_dic_path, str(content["index"]))
            print(f"Start Process：{str(content['index'])}")

            os.makedirs(index_dic_path, exist_ok=True)

            table_schema, table_schema_dic = load_database_table_schema(dataset_dic, content["db_id"])
            content["tables"] = table_schema

            with open(os.path.join(index_dic_path,"input.json"), "w", encoding="utf-8") as w:
                json.dump(content,w,indent=4)

            if not os.path.exists(os.path.join(index_dic_path,"origin_generate.json")):
                # 2. Generate for original prompt
                query, origin_gene_usage, origin_target_result = self.generating_component(content, table_schema_dic, dataset_dic, self.temperature)

                # 5. Execute ground truth
                ground_result = self.execute_ground_truth(content, table_schema_dic, dataset_dic)

                # 6. Compare target with ground truth
                checker = get_mr_checker_by_sql_type(
                    hallu_type= "basic",
                    sqlite_exec_one=origin_target_result,
                    sqlite_exec_two=ground_result,
                    sql_type=self.sql_type
                )
                real_flag = not checker.check(mode="equivalent", strict=self.strict)  # ：

                ## 2. Generate for original prompt,5. Execute ground truth, # 6. Compare target with ground truth
                target_result, target_rowcount, target_err = origin_target_result
                TargetResult_json = {"result": str(target_result), "rowcount": target_rowcount, "err": target_err}
                ground_result, ground_rowcount, ground_err = ground_result
                GroundResult_json = {"result": str(ground_result), "rowcount": ground_rowcount, "err": ground_err}
                with open(os.path.join(index_dic_path,"origin_generate.json"), "w", encoding="utf-8") as w:
                    json.dump({"TargetQuery":query, "usage":origin_gene_usage, "TargetResult":TargetResult_json, "GroundResult": GroundResult_json,"mr_relation":"equivalent", "real":real_flag},w,indent=4)
            else:
                print("Exist " + os.path.join(index_dic_path,"origin_generate.json"))
                with open(os.path.join(index_dic_path, "origin_generate.json"), "r", encoding="utf-8") as r:
                    origin_generate_temp = json.load(r)
                    TargetResult_json = origin_generate_temp["TargetResult"]
                    query = origin_generate_temp["TargetQuery"]
                    real_flag = origin_generate_temp["real"]

            # origin_generate  TargetQuery
            if len(TargetResult_json["err"]) != 0: # err，，
                with open(os.path.join(index_dic_path, "pred_real.json"), "w", encoding="utf-8") as w:
                    json.dump({"pred_flag": True, "real_flag": real_flag, "basic": {"pred": False}}, w, indent=4)
                ## time
                with open(os.path.join(index_dic_path, "time.json"), "w", encoding="utf-8") as w:
                    json.dump({"time": [0]}, w, indent=4)
                self.update_chunk_pred_flag(index_dic_path, types_identify_qmr)
                self.update_whole_pred_flag(index_dic_path, types_identify_qmr)
                continue

            start = time.perf_counter()  # start
            # 0. Hallucination Type Identify
            types_identify_json = os.path.join(index_dic_path, "type_identify.json")
            if not os.path.exists(types_identify_json):
                ## sql normalization
                sql_normalizer = SQLNormalization({"query": query})
                _, _, structured_query, _, normalized_query, normalized_structured_query, node_type = sql_normalizer.sql_normalize("sqlite")

                ## question normalization
                question_normalizer = QuestionNormalization(metadata=content)
                normalized_question = question_normalizer.question_normalize()

                hkb_whole = [{"index": content['index'], "node_type": node_type, "question": normalized_question,
                              "query": normalized_query}]
                with open(os.path.join(index_dic_path, "hkb_whole.json"), "w", encoding="utf-8") as w:
                    json.dump(hkb_whole,w,indent=4)

                ## Hallucination Type Identify
                types_retrieval, types_identify = matcher.type_identify_whole(normalized_question, normalized_query,
                                                                              self.top_match_k, self.threshold_similarity)
                # type，(pred,real)
                pred_real = {}
                for key, value in node_type.items():
                    pred_flag = True if key in types_retrieval else False
                    pred_real[key] = [pred_flag, value]
                with open(os.path.join(index_dic_path, "type_identify.json"), "w", encoding="utf-8") as w:
                    json.dump({"type_retrieval": types_retrieval, "types_identify": types_identify, "pred_real": pred_real},w, indent=4)
            else:
                print("Exist " + os.path.join(index_dic_path, "type_identify.json"))
                with open(os.path.join(index_dic_path, "type_identify.json"), "r", encoding="utf-8") as r:
                    types_identify_temp = json.load(r)
                    types_identify = types_identify_temp["types_identify"]

            # types_identify
            types_identify_qmr["basic"] = self.ablation
            for hallu_type, flag in types_identify.items():
                if hallu_type in ["Operator", "ColumnNameOPLiteral", "ConditionExpression"]:
                    types_identify_qmr[f"QMR-1-{hallu_type}"] = flag
                if hallu_type in ["ConditionExpression", "AggregationFunction", "GroupBy"]:
                    types_identify_qmr[f"QMR-2-{hallu_type}"] = flag
                if hallu_type in ["LIMIT", "ConditionExpression",  "Distinct","OrderBy"]:
                    types_identify_qmr[f"QMR-3-{hallu_type}"] = flag
                types_identify_qmr[f"QMR-4-{hallu_type}"] = flag

            for idx, (hallu_type, flag) in enumerate(types_identify_qmr.items()):
                if not flag:
                    continue
                hallu_dic = hallu_type
                os.makedirs(os.path.join(index_dic_path, hallu_dic), exist_ok=True)

                # 1. Prompt Paraphrasing
                if not os.path.exists(os.path.join(index_dic_path, hallu_dic, "prompt_paraphrasing.json")):
                    mr_questions, mr_relations, para_usage  = self.prompt_paraphasing(content, hallu_type)
                    ## 1. Prompt Paraphrasing
                    with open(os.path.join(index_dic_path, hallu_dic, "prompt_paraphrasing.json"), "w", encoding="utf-8") as w:
                        json.dump({"mr_questions":mr_questions, "mr_relations":mr_relations, "usage":para_usage},w,indent=4)
                else:
                    print("Exist " + os.path.join(index_dic_path, hallu_dic, "prompt_paraphrasing.json"))
                    with open(os.path.join(index_dic_path, hallu_dic, "prompt_paraphrasing.json"), "r", encoding="utf-8") as r:
                        prompt_paraphrasing_temp = json.load(r)
                        mr_questions = prompt_paraphrasing_temp["mr_questions"]
                        mr_relations = prompt_paraphrasing_temp["mr_relations"]

                # 3. Generate for metamorphic prompts
                mutant_records = []
                mutant_results = []
                paraphrasing_generate_json = os.path.join(index_dic_path, hallu_dic, "paraphrasing_generate.json")

                if not os.path.exists(paraphrasing_generate_json):
                    for i, question in enumerate(mr_questions):
                        content_new = copy.deepcopy(content)
                        content_new["question"] = question
                        query_temp, gene_usage_temp, result_temp = self.generating_component(content_new, table_schema_dic, dataset_dic, self.temperature)
                        result, rowcount, err = result_temp
                        mutant_records.append({"TargetQuery": query_temp, "usage": gene_usage_temp,"TargetResult": {"result": str(result), "rowcount": rowcount, "err": err}})
                        mutant_results.append(result_temp)

                    # 4. Detect hallucination
                    ## Execute original sql
                    content_temp = copy.deepcopy(content)
                    content_temp["query"] = query
                    origin_target_result = self.execute_ground_truth(content_temp, table_schema_dic, dataset_dic)
                    pred_flag, mr_check_results = self.bug_detector(origin_target_result, mutant_results, hallu_type,mr_relations)
                    for i, item in enumerate(mr_check_results):
                        mutant_records[i]["mr_relation"] = mr_relations[i]
                        mutant_records[i]["mr_check"] = item

                    ## 3. Generate for metamorphic prompts ,# 4. Detect hallucination
                    with open(paraphrasing_generate_json, "w",encoding="utf-8") as w:
                        json.dump(mutant_records, w, indent=4)

            end = time.perf_counter()
            ## time
            if not os.path.exists(os.path.join(index_dic_path, "time.json")):
                with open(os.path.join(index_dic_path, "time.json"), "w", encoding="utf-8") as w:
                    json.dump({"time": [end-start]}, w, indent=4)

            # chunk:  hallu_type  QMR1-QMR4   [，，MR relation]
            token_cnt_temp = self.update_chunk_pred_flag(index_dic_path, types_identify_qmr)
            token_cnt_total.append(token_cnt_temp)
            # whole:  hallu_type  QMR1-QMR4   [，，MR relation]
            self.update_whole_pred_flag(index_dic_path, types_identify_qmr)

            print(f"End Process：{str(content['index'])}")

        # prompt count
        prompt_cnt_total = []
        for i, item in enumerate(contents[:item_num]):
            index_dic_path = os.path.join(output_dic_path, str(item["index"]))
            with open(os.path.join(index_dic_path, "pred_real.json"), "r", encoding="utf-8") as r:
                pred_real_temp = json.load(r)
            cnt_temp = 0
            for key,value in pred_real_temp.items():
                if type(value) == dict:
                    cnt_temp += value["total"]
            prompt_cnt_total.append(cnt_temp)
        with open(os.path.join(output_dic_path,"prompt_count.json"),"w", encoding="utf-8") as w:
            json.dump({"prompt_count_list": prompt_cnt_total, "average_prompt_count": sum(prompt_cnt_total)/item_num},w,indent=4)

        # token cost
        with open(os.path.join(output_dic_path,"token_cost.json"),"w", encoding="utf-8") as w:
            json.dump({"token_list": token_cnt_total, "average_token": sum(token_cnt_total)/item_num},w,indent=4)

        # time cost
        time_total = []
        for i, item in enumerate(contents[:item_num]):
            index_dic_path = os.path.join(output_dic_path, str(item["index"]))
            with open(os.path.join(index_dic_path, "time.json"), "r", encoding="utf-8") as r:
                time_temp = json.load(r)
            time_total.append(sum(time_temp["time"]))
        with open(os.path.join(output_dic_path,"time_cost.json"),"w", encoding="utf-8") as w:
            json.dump({"time_list": time_total, "average_token": sum(time_total)/item_num},w,indent=4)


        #  Hallucination Type Identify
        pred_real_list = []
        for content in contents[:item_num]:
            #
            index_dic_path = os.path.join(output_dic_path, str(content["index"]))
            if not os.path.exists(os.path.join(index_dic_path, "type_identify.json")):
                continue
            with open(os.path.join(index_dic_path, "type_identify.json"), "r", encoding="utf-8") as r:
                pred_real = json.load(r)["pred_real"]
            for key, value in pred_real.items():
                pred_real_list.append(value)
        em = EvaluationManager(pred_real_list)
        evaluation_result = em.summary()
        with open(os.path.join(output_dic_path, f"type_identify_evaluation_{str(self.top_match_k)}_{str(self.threshold_similarity)}.json"), "w",
                  encoding="utf-8") as w:
            json.dump(evaluation_result, w, indent=4)

        # basic
        if self.ablation:
            pred_real_list = []
            for i in range(item_num):
                if not os.path.isdir(os.path.join(output_dic_path,str(i))):
                    continue

                # spider90：bird153.5，spider99
                with open(os.path.join(output_dic_path, str(i), "input.json"), "r", encoding="utf-8") as r:
                    input_temp = json.load(r)
                if "spider" in dataset_dic.lower() and len(input_temp["query"]) < 90:
                    continue

                with open(os.path.join(output_dic_path,str(i), "pred_real.json"), "r", encoding="utf-8") as r:
                    temp = json.load(r)
                    if "basic" in temp:
                        pred_real_list.append([temp["basic"]["pred"], temp["real_flag"]])
                    else:
                        pred_real_list.append([temp["pred_flag"], temp["real_flag"]])
            evaluation_res = self.evaluation(pred_real_list)

            with open(os.path.join(output_dic_path, f"ablation_evaluation_{str(self.threshold_cross_validation)}.json"), "w", encoding="utf-8") as w:
                json.dump(evaluation_res, w, indent=4)


        # ："pred_real.json"，
        ## chunk
        pred_real_list = []
        FP = []
        origin_query_fail_cnt = 0
        query_length = []
        for i in range(item_num):
            if not os.path.isdir(os.path.join(output_dic_path,str(i))):
                continue
            
            # # spider90：bird153.5，spider99
            # with open(os.path.join(output_dic_path,str(i),"input.json"), "r", encoding="utf-8") as r:
            #     input_temp = json.load(r)
            # if "spider" in dataset_dic.lower() and len(input_temp["query"]) < 90:
            #     continue
            # print(input_temp)
            # query_length.append(len(input_temp["query"]))

            with open(os.path.join(output_dic_path,str(i),"pred_real.json"), "r", encoding="utf-8") as r:
                temp = json.load(r)
                pred_real_list.append([temp["pred_flag"], temp["real_flag"]])
                if temp["pred_flag"] and not temp["real_flag"]:
                    FP.append(i)
        evaluation_res = self.evaluation(pred_real_list)

        with open(os.path.join(output_dic_path, f"evaluation_{str(self.threshold_cross_validation)}.json"), "w", encoding="utf-8") as w:
            json.dump(evaluation_res, w, indent=4)

        ## whole
        pred_real_list = []
        for i in range(item_num):
            if not os.path.isdir(os.path.join(output_dic_path,str(i))):
                continue
            
            # spider90：bird153.5，spider99
            # with open(os.path.join(output_dic_path,str(i),"input.json"), "r", encoding="utf-8") as r:
            #     input_temp = json.load(r)
            # if "spider" in dataset_dic.lower() and len(input_temp["query"]) < 90:
            #     continue

            with open(os.path.join(output_dic_path,str(i),"whole_pred_real.json"), "r", encoding="utf-8") as r:
                temp = json.load(r)
                pred_real_list.append([temp["pred_flag"], temp["real_flag"]])
        evaluation_res = self.evaluation(pred_real_list)

        with open(os.path.join(output_dic_path, f"whole_evaluation_{str(self.threshold_cross_validation)}.json"), "w", encoding="utf-8") as w:
            json.dump(evaluation_res, w, indent=4)

        # nums_query_length = sorted(query_length, reverse=True)
        # n_temp = len(nums_query_length)
        # if n_temp % 2 == 1:  #
        #     median = nums_query_length[n_temp// 2]
        # else:
        #     median = (nums_query_length[n_temp // 2 - 1] + nums_query_length[n_temp // 2]) / 2
        # print("median:", median)


    def update_chunk_pred_flag(self, index_dic_path, types_identify_qmr):
        token_cnt = 0
        #  origin_generate  TargetQuery
        with open(os.path.join(index_dic_path, "origin_generate.json"), "r", encoding="utf-8") as r:
            temp = json.load(r)
            real_flag = temp["real"]
            token_cnt += temp["usage"][2] # token count
            if len(temp["TargetResult"]["err"]) != 0:  # err，
                pred_real_content = {"pred_flag": True, "real_flag": True}
                with open(os.path.join(index_dic_path, "pred_real.json"), "w", encoding="utf-8") as w:
                    json.dump(pred_real_content, w, indent=4)
                return token_cnt

        pred_real_content = {"pred_flag": False, "real_flag": real_flag}
        for idx, (hallu_type, flag) in enumerate(types_identify_qmr.items()):
            if not flag:
                continue

            hallu_dic = hallu_type
            if hallu_dic == "basic":
                qmr_name = "QMR-0"
                hallu_type_name = hallu_dic
            else:
                parts = hallu_dic.split("-", 2)
                qmr_name = "-".join(parts[:2])
                hallu_type_name = parts[2]

            # token count
            with open(os.path.join(index_dic_path, hallu_dic, "prompt_paraphrasing.json"), "r",encoding="utf-8") as r:
                prompt_paraphrasing_list = json.load(r)
            token_cnt += prompt_paraphrasing_list["usage"][2]

            with open(os.path.join(index_dic_path, hallu_dic, "paraphrasing_generate.json"), "r",encoding="utf-8") as r:
                content_list = json.load(r)
            total_cnt = len(content_list)
            effective_cnt = 0
            mr_satisfied_cnt = 0
            for item in content_list:
                token_cnt += item["usage"][2] # token count
                if type(item["mr_check"]) == bool:
                    effective_cnt += 1
                    if item["mr_check"]:
                        mr_satisfied_cnt += 1
            if hallu_type_name not in pred_real_content: pred_real_content[hallu_type_name] = {}
            pred_real_content[hallu_type_name][qmr_name] = [total_cnt, effective_cnt, mr_satisfied_cnt]

        # hallu_typepred
        pred_true_cnt = 0
        pred_total_cnt = 0
        for hallu, value in pred_real_content.items():
            if type(value) != dict:
                continue
            total_sum = 0
            effective_sum = 0
            mr_satisfied_sum = 0
            for qmr_index, cnts in value.items():
                total_sum += cnts[0]
                effective_sum += cnts[1]
                mr_satisfied_sum += cnts[2]
            value["total"] = total_sum
            value["effective"] = effective_sum
            value["satisfied"] = mr_satisfied_sum
            value["pred"] = not (mr_satisfied_sum >= self.threshold_cross_validation * effective_sum)

            # if value["pred"]: pred_real_content["pred_flag"] = True # basic
            if value["pred"] and hallu != "basic": pred_real_content["pred_flag"] = True  # basic

            # # basic
            # if value["pred"]:
            #     pred_true_cnt += 1

            # # basic
            # if value["pred"] and hallu != "basic":
            #     pred_true_cnt += 1
            # pred_total_cnt += 1

        # if pred_true_cnt >= 1: pred_real_content["pred_flag"] = True
        with open(os.path.join(index_dic_path, "pred_real.json"), "w", encoding="utf-8") as w:
            json.dump(pred_real_content, w, indent=4)

        return token_cnt


    def update_whole_pred_flag(self, index_dic_path, types_identify_qmr):
        # whole:  hallu_type  QMR1-QMR4   [，，MR relation]
        with open(os.path.join(index_dic_path, "origin_generate.json"), "r", encoding="utf-8") as r:
            temp = json.load(r)
            real_flag = temp["real"]
            if len(temp["TargetResult"]["err"]) != 0:  # err，
                print(index_dic_path)
                pred_real_content = {"pred_flag": True, "real_flag": True}
                with open(os.path.join(index_dic_path, "whole_pred_real.json"), "w", encoding="utf-8") as w:
                    json.dump(pred_real_content, w, indent=4)
                return

        pred_real_content = {"pred_flag": False, "real_flag": real_flag, "total_whole": 0, "effective_whole": 0,
                             "mr_satisfied_whole": 0}
        total_whole = 0
        effective_whole = 0
        mr_satisfied_whole = 0
        for idx, (hallu_type, flag) in enumerate(types_identify_qmr.items()):
            #
            if not flag:
                continue

            hallu_dic = hallu_type
            if hallu_dic == "basic":
                qmr_name = "QMR-0"
                hallu_type_name = hallu_dic
            else:
                parts = hallu_dic.split("-", 2)
                qmr_name = "-".join(parts[:2])
                hallu_type_name = parts[2]

            with open(os.path.join(index_dic_path, hallu_dic, "paraphrasing_generate.json"), "r",
                      encoding="utf-8") as r:
                content_list = json.load(r)
            total_cnt = len(content_list)
            effective_cnt = 0
            mr_satisfied_cnt = 0
            for item in content_list:
                if type(item["mr_check"]) == bool:
                    effective_cnt += 1
                    if item["mr_check"]:
                        mr_satisfied_cnt += 1
            if hallu_type_name not in pred_real_content: pred_real_content[hallu_type_name] = {}
            pred_real_content[hallu_type_name][qmr_name] = [total_cnt, effective_cnt, mr_satisfied_cnt]

        # hallu_typepred
        for hallu, value in pred_real_content.items():
            if type(value) != dict:
                continue
            total_sum = 0
            effective_sum = 0
            mr_satisfied_sum = 0
            for qmr_index, cnts in value.items():
                total_sum += cnts[0]
                effective_sum += cnts[1]
                mr_satisfied_sum += cnts[2]
            value["total"] = total_sum
            value["effective"] = effective_sum
            value["satisfied"] = mr_satisfied_sum
            value["pred"] = not (mr_satisfied_sum >= self.threshold_cross_validation * effective_sum)

            # basic
            if value["pred"] and hallu != "basic": pred_real_content["pred_flag"] = True
            if hallu != "basic":
                total_whole += total_sum
                effective_whole += effective_sum
                mr_satisfied_whole += mr_satisfied_sum

        pred_real_content["total_whole"] = total_whole
        pred_real_content["effective_whole"] = effective_whole
        pred_real_content["mr_satisfied_whole"] = mr_satisfied_whole
        # pred_real_content["pred_flag"] = not (mr_satisfied_whole >= self.threshold_cross_validation * effective_whole)
        # MRSQLGen-CV
        pred_real_content["pred_flag"] = not(mr_satisfied_whole >= 1 * effective_whole)
        with open(os.path.join(index_dic_path, "whole_pred_real.json"), "w", encoding="utf-8") as w:
            json.dump(pred_real_content, w, indent=4)

    def generating_component(self, content, table_schema_dic, dataset_dic, temperature_):
        db_id = str(content["db_id"])  # ，
        origin_db_path = os.path.join(dataset_dic, table_schema_dic, db_id, f"{db_id}.sqlite")
        if "spider" in dataset_dic.lower():
            target_folder = os.path.join(dataset_dic, "..", "spider_data_db_temp", table_schema_dic, f"{db_id}-{content['index']}")
        elif "bird" in dataset_dic.lower():
            target_folder = os.path.join(dataset_dic, "..", "bird_data_db_temp", table_schema_dic, f"{db_id}-{content['index']}")
        else:
            pass
        os.makedirs(target_folder, exist_ok=True)

        db_file_new_name = f"{db_id}-{self.model_name.replace(':', '-')}-{content['index']}.sqlite"
        db_path = os.path.join(target_folder, db_file_new_name)
        shutil.copy(origin_db_path, db_path)

        db = SqliteConnector(db_path=db_path)
        prompt_generator = NumberSignCOTPrompt()
        sql_gen = DefaultSQLGenerator(llm_client=self.gpt_generating_component, db_connector=db, prompt_generator=prompt_generator, metadata=content)
        formatted_prompt = sql_gen.prompt_messages_construct()
        query, usage = sql_gen.generate_target_query()
        result, rowcount, err = sql_gen.execute_target_query()
        db.close()
        if os.path.exists(db_path):
            os.remove(db_path)
        return query, usage, (result, rowcount, err)

    def prompt_paraphasing(self, content, hallu_type) -> Tuple[List[str], List[str],dict]:
        transformer = get_prompt_transformer_by_hallucination_type(
            hallu_type= hallu_type,
            llm_client=self.gpt_prompt_paraphasing,
            n=self.n,
            metadata=content
        )
        return transformer.generate_metamorphic_prompts(hallu_type)

    def bug_detector(self, target_result, mutant_results, hallu_type, mr_relations) -> Tuple[bool, List[bool]]:
        detector = BugDetector(
            hallu_type= hallu_type,
            target_result=target_result,
            mutant_results=mutant_results,
            sql_type=self.sql_type,
            mr_relations=mr_relations,
            strict=self.strict,
            threshold=self.threshold_cross_validation
        )
        return detector.check_bug()

    def execute_ground_truth(self, content, table_schema_dic, dataset_dic) -> Tuple[list, int, str]:
        origin_db_path = os.path.join(dataset_dic, table_schema_dic, content["db_id"], f"{content['db_id']}.sqlite")
        target_folder = os.path.join(dataset_dic, "..", "spider_data_db_temp", table_schema_dic, content["db_id"])
        os.makedirs(target_folder, exist_ok=True)
        shutil.copy(origin_db_path, target_folder)
        db_path = os.path.join(target_folder, f"{content['db_id']}.sqlite")

        db = SqliteConnector(db_path=db_path)
        result, rowcount, err = db.execute(content["query"])
        db.close()
        if os.path.exists(db_path):
            os.remove(db_path)
        return (result, rowcount, err)

    def evaluation(self, pred_real_list: List[Tuple[bool, bool]]):
        em = EvaluationManager(pred_real_list)
        return em.summary()
