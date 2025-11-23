import shutil
from typing import Tuple, List
import time
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
        test_llm_model_config_file: str,
        judge_llm_model_config_file: str,
        runner_config_file: str,
        sql_type: str = "SELECT",
        strict: bool = True
    ):
        if not os.path.exists(test_llm_model_config_file):
            print(f"{test_llm_model_config_file} doesn't exist.")
            return
        if not os.path.exists(judge_llm_model_config_file):
            print(f"{judge_llm_model_config_file} doesn't exist.")
            return

        with open(test_llm_model_config_file, "r", encoding="utf-8") as r:
            test_llm_model_config = json.load(r)

        self.test_model_name = test_llm_model_config.get('model_name', 'gpt-4o-mini')
        self.test_llm_type = test_llm_model_config.get('llm_type', 'general-purpose')
        self.test_url = test_llm_model_config.get('url', '')
        self.test_stream = test_llm_model_config.get('stream', '')

        with open(judge_llm_model_config_file, "r", encoding="utf-8") as r:
            judge_llm_model_config = json.load(r)
        self.judge_model_name = judge_llm_model_config.get('model_name', 'gpt-4o-mini')
        self.judge_llm_type = judge_llm_model_config.get('llm_type', 'general-purpose')
        self.judge_url = judge_llm_model_config.get('url', '')
        self.judge_stream = judge_llm_model_config.get('stream', '')


        if not os.path.exists(runner_config_file):
            print(f"{runner_config_file} doesn't exist.")
            return
        with open(runner_config_file, "r", encoding="utf-8") as r:
            runner_config = json.load(r)

        self.test_temperature = runner_config.get('test_temperature',0.0)
        self.judge_temperature = runner_config.get('judge_temperature',0.0)
        self.sql_type = sql_type.upper()
        self.strict = strict
        self.llm_judge = LLMAsAJudgeCaller()

        # 0.75s: gpt = GPTClient
        os.environ["OPENAI_API_KEY"] = test_llm_model_config.get('api_key', '')
        os.environ["OPENAI_API_BASE"] = test_llm_model_config.get('api_base', '')
        self.gpt_generating_component = GPTClient(
            model_name=self.test_model_name,
            llm_type=self.test_llm_type,
            temperature= self.test_temperature,
            api_key=os.getenv("OPENAI_API_KEY"),
            api_base=os.getenv("OPENAI_API_BASE"),
            url=self.test_url,
            stream=self.test_stream
        )

        os.environ["OPENAI_API_KEY"] = judge_llm_model_config.get('api_key', '')
        os.environ["OPENAI_API_BASE"] = judge_llm_model_config.get('api_base', '')
        self.gpt_model_wrapper = GPTClient(
            model_name=self.judge_model_name,
            llm_type=self.judge_llm_type,
            temperature=self.judge_temperature,
            api_key=os.getenv("OPENAI_API_KEY"),
            api_base=os.getenv("OPENAI_API_BASE"),
            url=self.judge_url,
            stream=self.judge_stream
        )

    def model_wrapper(self, prompt: str):
        formatted_prompt = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ]

        response, usage = self.gpt_model_wrapper.generate(formatted_prompt)
        print(self.gpt_model_wrapper.model_name)

        return response, usage

    def run(self, input_json_path: str, dataset_name:str, dataset_path: str, output_dic_path: str, num_examples: int):
        output_dic_path = os.path.join(output_dic_path, f"llm_as_a_judge_{dataset_name}_{self.test_model_name.replace(':', '-')}_{self.judge_model_name.replace(':', '-')}")
        os.makedirs(output_dic_path, exist_ok=True)
        if not os.path.exists(input_json_path):
            return

        with open(os.path.join(output_dic_path, "config.json"), "w", encoding="utf-8") as w:
            config = {
                "test_model_name": self.test_model_name,
                "test_temperature": self.test_temperature,
                "judge_model_name": self.judge_model_name,
                "judge_temperature": self.judge_temperature,
                "input_json_path": input_json_path,
                "output_dic_path": output_dic_path,
                "num_examples": num_examples
            }
            json.dump(config, w, indent=4)

        with open(input_json_path, "r", encoding="utf-8") as r:
            contents = json.load(r)

        for i, item in enumerate(contents[:num_examples]):
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
                if not os.path.exists(os.path.join(index_dic_path, "origin_generate.json")):
                    generated_sql, origin_gene_usage, target_result = self.generating_component(item, table_schema_dic,dataset_path, self.test_temperature)

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

                    ##  Generate for original prompt
                    target_result, target_rowcount, target_err = target_result
                    TargetResult_json = {"result": str(target_result), "rowcount": target_rowcount, "err": target_err}
                    ground_result, ground_rowcount, ground_err = ground_result
                    GroundResult_json = {"result": str(ground_result), "rowcount": ground_rowcount, "err": ground_err}
                    with open(os.path.join(index_dic_path, "origin_generate.json"), "w", encoding="utf-8") as w:
                        json.dump({"TargetQuery": generated_sql, "usage": origin_gene_usage,
                                   "TargetResult": TargetResult_json,
                                   "GroundQuery": gold_sql, "GroundResult": GroundResult_json, "real": real_flag}, w,
                                  indent=4)
                else:
                    with open(os.path.join(index_dic_path, "origin_generate.json"), "r", encoding="utf-8") as r:
                        temp = json.load(r)
                        generated_sql = temp["TargetQuery"]
                        real_flag = temp["real"]


                start = time.perf_counter() # start llm-as-a-judge,start

                result = self.llm_judge.get_predict_type(
                    question=item['question'],
                    generated_sql=generated_sql,
                    schema_str=item["tables"],
                    model=self.model_wrapper,
                )
                pred_flag = result.get('pred', True)
                ## 3. Generate for metamorphic prompts ,# 4. Detect hallucination
                with open(os.path.join(index_dic_path, "check_generate.json"), "w", encoding="utf-8") as w:
                    json.dump(result, w, indent=4)

                end = time.perf_counter() # get the pred_flag, end



                with open(os.path.join(index_dic_path, "input.json"), "w", encoding="utf-8") as w:
                    json.dump(item, w, indent=4)


                ## (pred,real)
                with open(os.path.join(index_dic_path, "pred_real.json"), "w", encoding="utf-8") as w:
                    json.dump({"pred_flag": pred_flag, "real_flag": real_flag}, w, indent=4)
                ## time
                if not os.path.exists(os.path.join(index_dic_path, "time.json")):
                    with open(os.path.join(index_dic_path, "time.json"), "w", encoding="utf-8") as w:
                        json.dump({"time": (end - start)*10}, w, indent=4)
            except Exception as e:
                print(f" Error at example {i}: {e}")
                continue

            print(f"End Process：{str(index)}")

        # token cost
        token_cnt_total = []
        for i, item in enumerate(contents[:num_examples]):
            token_cnt_temp = 0
            index_dic_path = os.path.join(output_dic_path, str(item["index"]))
            with open(os.path.join(index_dic_path, "origin_generate.json"), "r", encoding="utf-8") as r:
                origin_generate_temp = json.load(r)
            token_cnt_temp += origin_generate_temp["usage"][2]

            with open(os.path.join(index_dic_path, "check_generate.json"), "r", encoding="utf-8") as r:
                check_generate_temp = json.load(r)
            token_cnt_temp = token_cnt_temp + check_generate_temp["usage"][2]*10
            token_cnt_total.append(token_cnt_temp)

        with open(os.path.join(output_dic_path,"token_cost.json"),"w", encoding="utf-8") as w:
            json.dump({"token_list": token_cnt_total, "average_token": sum(token_cnt_total)/num_examples},w,indent=4)

        # time cost
        # time_total = []
        # for i, item in enumerate(contents[:num_examples]):
        #     index_dic_path = os.path.join(output_dic_path, str(item["index"]))
        #     with open(os.path.join(index_dic_path, "time.json"), "r", encoding="utf-8") as r:
        #         time_temp = json.load(r)
        #     time_total.append(time_temp["time"])
        # with open(os.path.join(output_dic_path,"time_cost.json"),"w", encoding="utf-8") as w:
        #     json.dump({"time_list": time_total, "average_token": sum(time_total)/num_examples},w,indent=4)


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

        db = SqliteConnector(db_path=db_path)
        prompt_generator = NumberSignCOTPrompt()
        sql_gen = DefaultSQLGenerator(llm_client=self.gpt_generating_component, db_connector=db, prompt_generator=prompt_generator, metadata=content)
        sql_gen.prompt_messages_construct()

        print(self.gpt_generating_component.model_name)
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
