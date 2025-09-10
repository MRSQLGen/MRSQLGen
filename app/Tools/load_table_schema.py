import os
import json
def load_database_table_schema(dataset_dic, db_name):
    if "spider" in dataset_dic.lower():
        file_database_temp = os.path.join(dataset_dic, "database", db_name, "schema.json")
        file_test_database_temp = os.path.join(dataset_dic, "test_database", db_name, "schema.json")
        if os.path.exists(file_database_temp):
            with open(file_database_temp, "r", encoding="utf-8") as r:
                return json.load(r), "database"
        if os.path.exists(file_test_database_temp):
            with open(file_test_database_temp, "r", encoding="utf-8") as r:
                return json.load(r), "test_database"

    if "bird" in dataset_dic.lower():
        file_database_temp = os.path.join(dataset_dic, "dev_databases", db_name, "schema.json")
        file_test_database_temp = os.path.join(dataset_dic, "bird_data", "train_database", db_name, "schema.json")
        if os.path.exists(file_database_temp):
            with open(file_database_temp, "r", encoding="utf-8") as r:
                return json.load(r), "dev_databases"
        if os.path.exists(file_test_database_temp):
            with open(file_test_database_temp, "r", encoding="utf-8") as r:
                return json.load(r), "train_databases"

