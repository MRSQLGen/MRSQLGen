import os
import json
import shutil
from typing import List, Tuple
from app.gpt_client import GPTClient
from app.dbms_connectors.implements.sqlite_connector import SqliteConnector
from app.Tools.load_table_schema import load_database_table_schema
from app.DAIL_SQL_Prompt.PromptReprTemplate import NumberSignCOTPrompt
from app.sql_generator import DefaultSQLGenerator
from app.bug_detector import BugDetector
from app.evaluation_manager import EvaluationManager
from app.MR_checker.MRChecker_factory import get_mr_checker_by_sql_type
from app.Baseline.selfcheckgpt import SelfCheckGPTCaller
import numpy as np

class SelfCheckGPTRunner:
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
        self.origin_temperature = runner_config.get('origin_temperature',0.0)
        self.check_temperature = runner_config.get('check_temperature',1.0)
        self.n = runner_config.get('n', 10)

        self.sql_type = sql_type.upper()
        self.hallu_type = "basic"
        self.strict = strict
        self.selfcheckgpt_model = runner_config.get('selfcheckgpt_model','nli')
        self.threshold = runner_config.get('threshold', 0.5)

    def run(self, input_json_path: str, dataset_name:str, dataset_path: str, output_dic_path: str, item_num: int = 5):
        output_dic_path = os.path.join(output_dic_path, f"selfcheckgpt_{dataset_name}_{self.model_name.replace(':', '-')}")
        os.makedirs(output_dic_path, exist_ok=True)
        if not os.path.exists(input_json_path):
            return

        with open(os.path.join(output_dic_path, "config.json"), "w", encoding="utf-8") as w:
            config = {
                "model_name": self.model_name,
                "origin_temperature": self.origin_temperature,
                "check_temperature": self.check_temperature,
                "n": self.n,
                "selfcheckgpt_model": self.selfcheckgpt_model,
                "threshold": self.threshold,
                "input_json_path": input_json_path,
                "output_dic_path": output_dic_path,
                "item_num": item_num
            }
            json.dump(config, w, indent=4)

        #
        with open(input_json_path, "r", encoding="utf-8") as r:
            contents = json.load(r)

        for content in contents[:item_num]:
            #
            index_dic_path = os.path.join(output_dic_path, str(content["index"]))
            if os.path.exists(os.path.join(index_dic_path, "pred_real.json")):
                # ，threshold. is_hallucination = bool(mean_scores > threshold)
                with open(os.path.join(index_dic_path, "pred_real.json"), "r", encoding="utf-8") as r:
                    pred_real_json = json.load(r)
                pred_flag = bool(pred_real_json['mean_scores'] > self.threshold)
                pred_real_json['pred_flag'] = pred_flag
                with open(os.path.join(index_dic_path, "pred_real.json"), "w", encoding="utf-8") as w:
                    json.dump(pred_real_json, w, indent=4)

            index = content["index"]
            print(f"Start Process：{str(index)}")

            os.makedirs(index_dic_path, exist_ok=True)

            table_schema, table_schema_dic = load_database_table_schema(dataset_path, content["db_id"])
            content["tables"] = table_schema

            if not os.path.exists(os.path.join(index_dic_path, "origin_generate.json")):
                # 2. Generate for original prompt(temperature = 0)
                query, origin_gene_usage, target_result = self.generating_component(content, table_schema_dic,dataset_path,
                                                                                    self.origin_temperature)
                # 5. Execute ground truth
                ground_result = self.execute_ground_truth(content, table_schema_dic, dataset_path)
                # 6. Compare target with ground truth
                checker = get_mr_checker_by_sql_type(
                    hallu_type=self.hallu_type,
                    sqlite_exec_one=target_result,
                    sqlite_exec_two=ground_result,
                    sql_type=self.sql_type
                )
                real_flag = not checker.check(mode="equivalent", strict=self.strict)  # ：
                ## 2. Generate for original prompt,5. Execute ground truth, # 6. Compare target with ground truth
                target_result, target_rowcount, target_err = target_result
                TargetResult_json = {"result": str(target_result), "rowcount": target_rowcount, "err": target_err}
                ground_result, ground_rowcount, ground_err = ground_result
                GroundResult_json = {"result": str(ground_result), "rowcount": ground_rowcount, "err": ground_err}
                with open(os.path.join(index_dic_path, "origin_generate.json"), "w", encoding="utf-8") as w:
                    json.dump({"TargetQuery": query, "usage": origin_gene_usage, "TargetResult": TargetResult_json,
                               "GroundResult": GroundResult_json, "real": real_flag}, w, indent=4)
            else:
                with open(os.path.join(index_dic_path, "origin_generate.json"), "r", encoding="utf-8") as r:
                    origin_generate_temp = json.load(r)
                query = origin_generate_temp["TargetQuery"]
                real_flag = origin_generate_temp["real"]

            if not os.path.exists(os.path.join(index_dic_path, "check_generate.json")):
                # 3. Generate for check prompts(temperature = 1)
                check_records = []
                check_samples = []
                for i in range(self.n):
                    query_temp, gene_usage_temp = self.generating_component_selfcheckgpt(content, table_schema_dic, dataset_path,
                                                                                         self.check_temperature)
                    check_records.append({"TargetQuery": query_temp, "usage": gene_usage_temp})
                    check_samples.append(query_temp)
                ## 3. Generate for metamorphic prompts ,# 4. Detect hallucination
                with open(os.path.join(index_dic_path, "check_generate.json"), "w", encoding="utf-8") as w:
                    json.dump(check_records, w, indent=4)
            else:
                check_samples = []
                with open(os.path.join(index_dic_path, "check_generate.json"), "r", encoding="utf-8") as r:
                    check_records_temp = json.load(r)
                for item in check_records_temp:
                    check_samples.append(item["TargetQuery"])

            # 4. Detect hallucination(selfcheckgpt)
            if not os.path.exists(os.path.join(index_dic_path, "pred_real.json")):
                selfcheckgpt_caller = SelfCheckGPTCaller(self.selfcheckgpt_model)
                success = True
                try:
                    mean_scores, scores, pred_flag = selfcheckgpt_caller.get_predict_scores(
                        sampled_passages=check_samples,
                        passage=query,
                        threshold=self.threshold)
                except Exception as e:
                    print(f"Error during hallucination detection: {str(e)}")
                    success = False
                if not success:
                    print(f"SelfCheckGPT failed for index {index}, skipping further processing.")
                    pred_flag = not real_flag  # selfcheckgpt，
                    mean_scores = 0.0
                    scores = np.array([])
                ## (pred,real),selfcheckgptscores
                if type(scores) is np.ndarray:
                    scores = scores.tolist()  # scores
                with open(os.path.join(index_dic_path, "pred_real.json"), "w", encoding="utf-8") as w:
                    json.dump(
                        {"pred_flag": pred_flag, "real_flag": real_flag, "mean_scores": mean_scores, "scores": scores},
                        w,
                        indent=4)

            # 7.
            with open(os.path.join(index_dic_path, "input.json"), "w", encoding="utf-8") as w:
                json.dump(content, w, indent=4)
            print((pred_flag, real_flag))
            print(f"End Process：{str(index)}")

        # "pred_real.json"，
        pred_real_list = []
        for i in range(item_num):
            if not os.path.isdir(os.path.join(output_dic_path, str(i))):
                continue

            with open(os.path.join(output_dic_path, str(i), "pred_real.json"), "r", encoding="utf-8") as r:
                temp = json.load(r)
                pred_real_list.append([temp["pred_flag"], temp["real_flag"]])

            is_hallucination = bool(temp["mean_scores"] > self.threshold)
            if is_hallucination != temp["pred_flag"]:
                pred_real_list.append([is_hallucination, temp["real_flag"]])
                temp["pred_flag"] = is_hallucination
                with open(os.path.join(output_dic_path, str(i), "pred_real.json"), "w", encoding="utf-8") as w:
                    json.dump(temp, w, indent=4)
        evaluation_res = self.evaluation(pred_real_list)

        # 8.
        with open(os.path.join(output_dic_path, "evaluation.json"), "w", encoding="utf-8") as w:
            json.dump(evaluation_res, w, indent=4)

    def generating_component(self, content, table_schema_dic, dataset_dic, temperature_) -> Tuple[
        str, dict, Tuple[list, int, str]]:
        db_id = str(content["db_id"])  # ，
        origin_db_path = os.path.join(dataset_dic, table_schema_dic, db_id, f"{db_id}.sqlite")
        target_folder = os.path.join(dataset_dic, "..", "spider_data_db_temp", table_schema_dic, db_id)
        os.makedirs(target_folder, exist_ok=True)
        shutil.copy(origin_db_path, target_folder)
        db_path = os.path.join(target_folder, f"{db_id}.sqlite")

        gpt = GPTClient(
            model_name=self.model_name,
            llm_type=self.llm_type,
            temperature=temperature_,
            api_key=os.getenv("OPENAI_API_KEY"),
            api_base=os.getenv("OPENAI_API_BASE"),
            url=self.url,
            stream=self.stream
        )
        db = SqliteConnector(db_path=db_path)
        prompt_generator = NumberSignCOTPrompt()
        sql_gen = DefaultSQLGenerator(llm_client=gpt, db_connector=db, prompt_generator=prompt_generator,
                                      metadata=content)
        sql_gen.prompt_messages_construct()
        query, usage = sql_gen.generate_target_query()
        result, rowcount, err = sql_gen.execute_target_query()
        db.close()
        if os.path.exists(db_path):
            os.remove(db_path)
        return query, usage, (result, rowcount, err)

    def generating_component_selfcheckgpt(self, content, table_schema_dic, dataset_dic, temperature_) -> Tuple[
        str, dict]:
        db_id = str(content["db_id"])  # ，
        origin_db_path = os.path.join(dataset_dic, table_schema_dic, db_id, f"{db_id}.sqlite")
        target_folder = os.path.join(dataset_dic, "..", "spider_data_db_temp", table_schema_dic, db_id)
        os.makedirs(target_folder, exist_ok=True)
        shutil.copy(origin_db_path, target_folder)
        db_path = os.path.join(target_folder, f"{db_id}.sqlite")
        gpt = GPTClient(
            model_name=self.model_name,
            llm_type=self.llm_type,
            temperature=temperature_,
            api_key=os.getenv("OPENAI_API_KEY"),
            api_base=os.getenv("OPENAI_API_BASE"),
            url=self.url,
            stream=self.stream
        )
        db = SqliteConnector(db_path=db_path)
        prompt_generator = NumberSignCOTPrompt()
        sql_gen = DefaultSQLGenerator(llm_client=gpt, db_connector=db, prompt_generator=prompt_generator,
                                      metadata=content)
        sql_gen.prompt_messages_construct()
        query, usage = sql_gen.generate_target_query()
        db.close()
        if os.path.exists(db_path):
            os.remove(db_path)
        return query, usage

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
