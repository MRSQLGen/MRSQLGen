import shutil
from typing import Tuple, List

from app.gpt_client import GPTClient
from app.DAIL_SQL_Prompt.PromptReprTemplate import NumberSignCOTPrompt
from app.sql_generator import DefaultSQLGenerator
from app.Baseline.llm_as_a_judge import LLMAsAJudgeCaller
from app.dbms_connectors.implements.sqlite_connector import SqliteConnector
from app.Tools.load_table_schema import load_database_table_schema
from app.evaluation_manager import EvaluationManager
from app.MR_checker.MRChecker_factory import get_mr_checker_by_sql_type
import os
import json

class LLM_As_A_Judge_Runner:
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
        self.sql_type = sql_type.upper()
        self.strict = strict
        self.llm_judge = LLMAsAJudgeCaller()


    def model_wrapper(self, prompt: str):
        gpt_client = GPTClient(
            model_name=self.model_name,
            llm_type=self.llm_type,
            temperature=self.temperature,
            api_key=os.getenv("OPENAI_API_KEY"),
            api_base=os.getenv("OPENAI_API_BASE"),
            url=self.url,
            stream=self.stream
        )

        formatted_prompt = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ]

        response, usage = gpt_client.generate(formatted_prompt)

        return response, usage

    def run(self, input_json_path: str, dataset_name:str, dataset_path: str, output_dic_path: str, num_examples: int):
        output_dic_path = os.path.join(output_dic_path, f"llm_as_a_judge_{dataset_name}_{self.model_name.replace(':', '-')}")
        os.makedirs(output_dic_path, exist_ok=True)
        if not os.path.exists(input_json_path):
            return

        # 0. ，
        with open(os.path.join(output_dic_path, "config.json"), "w", encoding="utf-8") as w:
            config = {
                "model_name": self.model_name,
                "temperature": self.temperature,
                "input_json_path": input_json_path,
                "output_dic_path": output_dic_path,
                "num_examples": num_examples
            }
            json.dump(config, w, indent=4)

        #
        with open(input_json_path, "r", encoding="utf-8") as r:
            contents = json.load(r)

        # 2.
        for i, item in enumerate(contents[:num_examples]):
            #
            index_dic_path = os.path.join(output_dic_path, str(item["index"]))
            if os.path.exists(os.path.join(index_dic_path, "pred_real.json")):
                continue

            index = item["index"]
            print(f"Start Process：{str(index)}")

            os.makedirs(index_dic_path, exist_ok=True)

            table_schema, table_schema_dic = load_database_table_schema(dataset_path, item["db_id"])
            item["tables"] = table_schema
            gold_sql = item['query']

            try:
                #  LLM  SQL
                generated_sql, origin_gene_usage, target_result = self.generating_component(item, table_schema_dic,dataset_path, self.temperature)
                #  Judge  +
                result = self.llm_judge.get_predict_type(
                    question=item['question'],
                    generated_sql=generated_sql,
                    schema_str=item["tables"],
                    model=self.model_wrapper,
                )
                pred_flag = result.get('pred', True)

                # 5. Execute ground truth
                ground_result = self.execute_ground_truth(item, table_schema_dic, dataset_path)

                # 6. Compare target with ground truth
                checker = get_mr_checker_by_sql_type(
                    hallu_type="basic",
                    sqlite_exec_one=target_result,
                    sqlite_exec_two=ground_result,
                    sql_type=self.sql_type
                )
                real_flag = not checker.check(mode="equivalent", strict=self.strict)  # ：

                # 7.
                ##
                with open(os.path.join(index_dic_path, "input.json"), "w", encoding="utf-8") as w:
                    json.dump(item, w, indent=4)
                ##  Generate for original prompt
                target_result, target_rowcount, target_err = target_result
                TargetResult_json = {"result": str(target_result), "rowcount": target_rowcount, "err": target_err}
                ground_result, ground_rowcount, ground_err = ground_result
                GroundResult_json = {"result": str(ground_result), "rowcount": ground_rowcount, "err": ground_err}
                with open(os.path.join(index_dic_path, "origin_generate.json"), "w", encoding="utf-8") as w:
                    json.dump({"TargetQuery": generated_sql, "usage": origin_gene_usage, "TargetResult": TargetResult_json,
                               "GroundQuery": gold_sql,"GroundResult": GroundResult_json, "real": real_flag}, w, indent=4)
                ## 3. Generate for metamorphic prompts ,# 4. Detect hallucination
                with open(os.path.join(index_dic_path, "check_generate.json"), "w", encoding="utf-8") as w:
                    json.dump(result, w, indent=4)
                ## (pred,real)
                with open(os.path.join(index_dic_path, "pred_real.json"), "w", encoding="utf-8") as w:
                    json.dump(
                        {"pred_flag": pred_flag, "real_flag": real_flag}, w, indent=4)
            except Exception as e:
                print(f" Error at example {i}: {e}")
                continue

            print(f"End Process：{str(index)}")

        # "pred_real.json"，
        pred_real_list = []
        for i in range(num_examples):
            if not os.path.isdir(os.path.join(output_dic_path,str(i))):
                continue

            # #  origin_generate  TargetQuery
            # with open(os.path.join(output_dic_path,str(i),"origin_generate.json"), "r", encoding="utf-8") as r:
            #     temp = json.load(r)
            #     if len(temp["TargetResult"]["err"]) != 0: # err，，
            #         continue

            with open(os.path.join(output_dic_path,str(i),"pred_real.json"), "r", encoding="utf-8") as r:
                temp = json.load(r)
            if type(temp["pred_flag"]) != bool:
                # shutil.rmtree(os.path.join(output_dic_path,str(i)))
                continue
            pred_real_list.append([temp["pred_flag"], temp["real_flag"]])

        evaluation_res = self.evaluation(pred_real_list)

        # 8.
        with open(os.path.join(output_dic_path, "evaluation.json"), "w", encoding="utf-8") as w:
            json.dump(evaluation_res, w, indent=4)

    def generating_component(self, content, table_schema_dic, dataset_dic, temperature_) -> Tuple[str, dict, Tuple[list, int, str]]:
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
        sql_gen = DefaultSQLGenerator(llm_client=gpt, db_connector=db, prompt_generator=prompt_generator, metadata=content)
        sql_gen.prompt_messages_construct()
        query, usage = sql_gen.generate_target_query()
        result, rowcount, err = sql_gen.execute_target_query()
        db.close()
        if os.path.exists(db_path):
            os.remove(db_path)
        return query, usage, (result, rowcount, err)

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
