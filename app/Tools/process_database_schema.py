import os
import json
import pandas as pd
import chardet  # pip install chardet
import argparse
current_file_path = os.path.abspath(__file__)
current_dir = os.path.dirname(current_file_path)

def process_table_schema(db: dict):
    table_schema_list = []

    table_names = db["table_names_original"]
    column_names = db["column_names_original"]
    column_types = db["column_types"]

    # column_name,。indextable_schema
    for index in range(len(column_names)):
        column_name = column_names[index]
        table_index, name = column_name[0], column_name[1]
        if table_index < 0:
            continue
        if len(table_schema_list) <= table_index:
            table_schema_list.append({})  # table_schema_listtable_schema，{}
        if "name" not in table_schema_list[table_index]:
            table_schema_list[table_index]["name"] = table_names[table_index]
        if "schema" not in table_schema_list[table_index]:
            table_schema_list[table_index]["schema"] = [name+":"+column_types[index]]
        else:
            table_schema_list[table_index]["schema"].append(name + ":" + column_types[index])
    return table_schema_list


def spider_process_tables_definition_json(data_dic, file:str):
    """
    table schema jsondb，table schema
    """
    with open(os.path.join(data_dic, file), "r", encoding="utf-8") as r:
        contents = json.load(r)
    if not contents:
        return

    database_sub_dic = os.listdir(os.path.join(data_dic, "database"))
    test_database_sub_dic = os.listdir(os.path.join(data_dic, "test_database"))
    for db in contents:
        table_schema_list = process_table_schema(db)
        db_name = db["db_id"]

        # databasedb,tableschema
        if db_name in database_sub_dic:
            temp = os.path.join(data_dic, "database", db_name, "schema.json")
            if not os.path.exists(temp):
                with open(temp, "w", encoding="utf-8") as w:
                    json.dump(table_schema_list, w, indent=4)

        # test_databasedb,tableschema
        if db_name in test_database_sub_dic:
            temp = os.path.join(data_dic, "test_database", db_name, "schema.json")
            if not os.path.exists(temp):
                with open(temp, "w", encoding="utf-8") as w:
                    json.dump(table_schema_list, w, indent=4)

def read_csv_any_encoding(path, sep=","):
    with open(path, "rb") as f:
        raw_data = f.read(100)
        encoding = chardet.detect(raw_data)["encoding"] or "utf-8"
    try:
        return pd.read_csv(path, sep=sep, encoding=encoding)
    except UnicodeDecodeError:
        return pd.read_csv(path, sep=sep, encoding="latin1")


def enumerate_data(input_file):
   with open(input_file,"r",encoding="utf-8") as r:
       contents = json.load(r)

   for index in range(len(contents)):
      contents[index]["index"] = index
      if "SQL" in contents[index]:
         contents[index]["query"] = contents[index]["SQL"]

   with open(input_file, "w", encoding="utf-8") as w:
      json.dump(contents, w, indent=4)

def bird_process_tables_definition_json(data_dic,file:str):
    """
    table schema jsondb，table schema
    """
    with open(os.path.join(data_dic, file), "r", encoding="utf-8") as r:
        contents = json.load(r)
    if not contents:
        return

    dev_database_sub_dic = os.listdir(os.path.join(data_dic, "dev_databases"))
    train_database_sub_dic = os.listdir(os.path.join(data_dic, "train_databases"))
    for db in contents:
        table_schema_list = process_table_schema(db)
        db_name = db.get("db_id","")

        if db_name in dev_database_sub_dic:
            for item in table_schema_list:
                description_csv = os.path.join(data_dic, "dev_databases", db_name, "database_description", f"{item['name']}.csv")
                if not os.path.exists(description_csv):
                    continue
                df = read_csv_any_encoding(description_csv, ",")
                table_description = []
                for _, row in df.iterrows():
                    column_name = row["original_column_name"]
                    column_description = row['column_description']
                    value_description = row['value_description']
                    table_description.append(f"{column_name}: {column_description}; {value_description}")
                item['description'] = table_description
            temp = os.path.join(data_dic, "dev_databases", db_name, "schema.json")
            with open(temp, "w", encoding="utf-8") as w:
                json.dump(table_schema_list, w, indent=4)


        if db_name in train_database_sub_dic:
            for item in table_schema_list:
                description_csv = os.path.join(data_dic, "train_databases", db_name, "database_description", f"{item['name']}.csv")
                if not os.path.exists(description_csv):
                    continue
                df = read_csv_any_encoding(description_csv, ",")
                table_description = []
                for _, row in df.iterrows():
                    column_name = row["original_column_name"]
                    column_description = row['column_description']
                    value_description = row['value_description']
                    table_description.append(f"{column_name}: {column_description}; {value_description}")
                item['description'] = table_description
            temp = os.path.join(data_dic, "train_databases", db_name, "schema.json")
            with open(temp, "w", encoding="utf-8") as w:
                json.dump(table_schema_list, w, indent=4)

def spider_process(data_dic):
    print("Start processing spider")
    # dev.json
    if os.path.exists(os.path.join(data_dic, "dev.json")):
        print("exist")
        enumerate_data(os.path.join(data_dic, "dev.json"))

    # test.json
    if os.path.exists(os.path.join(data_dic, "test.json")):
        enumerate_data(os.path.join(data_dic, "test.json"))

    # train_others.json
    if os.path.exists(os.path.join(data_dic, "train_others.json")):
        enumerate_data(os.path.join(data_dic, "train_others.json"))

    # train_spider.json
    if os.path.exists(os.path.join(data_dic, "train_spider.json")):
        enumerate_data(os.path.join(data_dic, "train_spider.json"))

    # tables.json
    if os.path.exists(os.path.join(data_dic, "tables.json")):
        spider_process_tables_definition_json(data_dic, "tables.json")

    # test_tables.json
    if os.path.exists(os.path.join(data_dic, "test_tables.json")):
        spider_process_tables_definition_json(data_dic, "test_tables.json")
    print("End processing spider")

def bird_process(data_dic):
    print("Start processing bird")
    # dev.json
    if os.path.exists(os.path.join(data_dic, "dev.json")):
        enumerate_data(os.path.join(data_dic, "dev.json"))

    # dev_tied_append.json
    if os.path.exists(os.path.join(data_dic, "dev_tied_append.json")):
        enumerate_data(os.path.join(data_dic, "dev_tied_append.json"))

    # train.json
    if os.path.exists(os.path.join(data_dic, "train.json")):
        enumerate_data(os.path.join(data_dic, "train.json"))

    # dev_tables.json
    if os.path.exists(os.path.join(data_dic, "dev_tables.json")):
        bird_process_tables_definition_json(data_dic, "dev_tables.json")

    # train_tables.json
    if os.path.exists(os.path.join(data_dic, "train_tables.json")):
        bird_process_tables_definition_json(data_dic, "train_tables.json")
    print("Start processing bird")

def datasets_process(data_dic):
    if "spider" in data_dic.lower():
        spider_process(os.path.join(data_dic))
    elif "bird" in data_dic.lower():
        bird_process(data_dic)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_dic", type=str, required=True)
    args = parser.parse_args()
    datasets_process(
        data_dic=args.data_dic
    )