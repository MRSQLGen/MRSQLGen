
import json

from markdown_it.rules_block import table


class BasicPrompt(object):
    def __init__(self, *args, **kwargs):
        # used to avoid empty init function in 0-shot prompt
        pass

    def format_target(self, example: dict):
        return self.format_question(example) + "\nSELECT "

    def format_question(self, example: dict):
        raise NotImplementedError()

    def get_extra_info(self, example: dict):
        bird_evidence = example.get('evidence', '')

        tables =  example.get('tables', [])
        table_description_str = ""
        # for table in tables:
        #     table_description = table.get('description', [])
        #     table_description_temp = "\n".join(table_description)
        #     table_description_str += f"# Table [{table.get('name')}]'s Description:[{table_description_temp}]\n"

        if bird_evidence == '':
            return None
        else:
            return f"{table_description_str}\n### Evidence:{bird_evidence}"




class TextPrompt(BasicPrompt):
    template_info = "Given the following database schema:\n" \
                  "{}"
    template_question = "Answer the following: {}"

    def format_question(self, example: dict):
        schemas = "\n".join([f"{_.name}: {', '.join(_.schema)}" for _ in example["tables"]])

        prompt_info = self.template_info.format(schemas)
        prompt_extra_info = self.get_extra_info(example["db_id"])
        prompt_question = self.template_question.format(example["question"])

        if prompt_extra_info is None or prompt_extra_info == "":
            prompt_components = [prompt_info,prompt_question]
        else:
            prompt_components = [prompt_info, prompt_extra_info, prompt_question]

        prompt = "\n".join(prompt_components)
        return prompt


class NumberSignPrompt(BasicPrompt):
    template_info = "### Complete sqlite SQL query only and with no explanation\n" \
                    "### SQLite SQL tables, with their properties:\n" \
                    "#\n" \
                    "{}\n" \
                    "#"
    template_question = "### {}"

    def format_question(self, example: dict):
        schemas = "\n".join([f"# {_.name}({', '.join(_.schema)})" for _ in example["tables"]])

        prompt_info = self.template_info.format(schemas)
        prompt_extra_info = self.get_extra_info(example["db_id"])
        prompt_question = self.template_question.format(example["question"])

        if prompt_extra_info is None or prompt_extra_info == "":
            prompt_components = [prompt_info,prompt_question]
        else:
            prompt_components = [prompt_info, prompt_extra_info, prompt_question]

        prompt = "\n".join(prompt_components)
        return prompt


class BaselinePrompt(BasicPrompt):
    template_info = "{}\nForeign_keys={}\n"
    template_question = "Q: \"{}\""

    def format_question(self, example: dict):
        # schemas
        schemas = "\n".join([f"Table {_.name}, columns = {_.schema}" for _ in example["tables"]]).replace("'", "")
        # foreign_keys
        foreign_keys = list()
        for table in example["tables"]:
            for pair_str in table["table_info"]["foreign_key"]:
                a, b = [_.strip() for _ in pair_str[1:-1].split(",")]
                foreign_keys.append(f"{a}={b}")

        # format prompt
        prompt_info = self.template_info.format(schemas, str(foreign_keys).replace("'", ""))
        prompt_extra_info = self.get_extra_info(example["db_id"])
        prompt_question = self.template_question.format(example["question"])

        if prompt_extra_info is None or prompt_extra_info == "":
            prompt_components = [prompt_info,prompt_question]
        else:
            prompt_components = [prompt_info, prompt_extra_info, prompt_question]

        prompt = "".join(prompt_components)
        return prompt

    def format_target(self, example: dict):
        return self.format_question(example) + "\nA: SELECT "


class InstructionPrompt(BasicPrompt):
    template_info = (
        "Below is an instruction that describes a task, paired with an input that provides further context. "
        "Write a response that appropriately completes the request.\n\n"
        "### Instruction:\nWrite a sql to answer the question \"{}\"\n\n### Input:\n{}\n"
    )
    template_question = "### Response:"

    def format_question(self, example: dict):
        schemas = "\n".join([f"{_.name}({', '.join(_.schema)})" for _ in example["tables"]])

        prompt_info = self.template_info.format(example["question"], schemas)
        prompt_extra_info = self.get_extra_info(example["db_id"])
        prompt_question = self.template_question

        if prompt_extra_info is None or prompt_extra_info == "":
            prompt_components = [prompt_info, prompt_question]
        else:
            # TODO: extra_info should be after info
            prompt_components = [prompt_info, prompt_extra_info, prompt_question]

        prompt = "\n".join(prompt_components)
        return prompt


class TextWithForeignKeyPrompt(BasicPrompt):
    template_info = "Given the following database schema:\n" \
                    "{} \n" \
                    "And their foreign keys:\n" \
                    "{}"
    template_question = "Answer the following: {}"

    def format_question(self, example: dict):
        schemas = "\n".join([f"{_.name}: {', '.join(_.schema)}" for _ in example["tables"]])
        # foreign_keys
        foreign_keys = list()
        for table in example["tables"]:
            for pair_str in table["table_info"]["foreign_key"]:
                a, b = [_.strip() for _ in pair_str[1:-1].split(",")]
                foreign_keys.append(f"{a}={b}")
        foreign_keys = f"{', '.join(foreign_keys)}"

        prompt_info = self.template_info.format(schemas, foreign_keys)
        prompt_extra_info = self.get_extra_info(example["db_id"])
        prompt_question = self.template_question.format(example["question"])

        if prompt_extra_info is None or prompt_extra_info == "":
            prompt_components = [prompt_info,prompt_question]
        else:
            prompt_components = [prompt_info, prompt_extra_info, prompt_question]

        prompt = "\n".join(prompt_components)
        return prompt


class NumberSignWithForeignKeyPrompt(BasicPrompt):
    template_info = "### Complete sqlite SQL query only and with no explanation\n" \
                    "### SQLite SQL tables, with their properties:\n" \
                    "#\n" \
                    "{}\n" \
                    "#\n" \
                    "### Their foreign keys:\n" \
                    "#\n" \
                    "{}\n" \
                    "#"
    template_question = "### {}"

    def format_question(self, example: dict):
        schemas = "\n".join([f"# {_.name}({', '.join(_.schema)})" for _ in example["tables"]])
        # foreign_keys
        foreign_keys = list()
        for table in example["tables"]:
            for pair_str in table["table_info"]["foreign_key"]:
                a, b = [_.strip() for _ in pair_str[1:-1].split(",")]
                foreign_keys.append(f"{a}={b}")
        foreign_keys = f"# Foreign_keys=({', '.join(foreign_keys)})"

        prompt_info = self.template_info.format(schemas, foreign_keys)
        prompt_extra_info = self.get_extra_info(example["db_id"])
        prompt_question = self.template_question.format(example["question"])

        if prompt_extra_info is None or prompt_extra_info == "":
            prompt_components = [prompt_info, prompt_question]
        else:
            prompt_components = [prompt_info, prompt_extra_info, prompt_question]

        prompt = "\n".join(prompt_components)
        return prompt


class BaselineWithoutForeignKeyPrompt(BasicPrompt):
    template_info = "{}\n"
    template_question = "Q: \"{}\""

    def format_question(self, example: dict):
        # schemas
        schemas = "\n".join([f"Table {_.name}, columns = {_.schema}" for _ in example["tables"]]).replace("'", "")

        # format prompt
        prompt_info = self.template_info.format(schemas)
        prompt_extra_info = self.get_extra_info(example["db_id"])
        prompt_question = self.template_question.format(example["question"])

        if prompt_extra_info is None or prompt_extra_info == "":
            prompt_components = [prompt_info,prompt_question]
        else:
            prompt_components = [prompt_info, prompt_extra_info, prompt_question]

        prompt = "".join(prompt_components)
        return prompt

    def format_target(self, example: dict):
        return self.format_question(example) + "\nA: SELECT "


class InstructionWithForeignKeyPrompt(BasicPrompt):
    template_info = (
        "Below is an instruction that describes a task, paired with an input that provides further context. "
        "Write a response that appropriately completes the request.\n\n"
        "### Instruction:\nWrite a sql to answer the question \"{}\"\n\n### Input:\n{}\nForeign Keys:{}\n"
    )
    template_question = "### Response:"

    def format_question(self, example: dict):
        schemas = "\n".join([f"{_.name}({', '.join(_.schema)})" for _ in example["tables"]])
        # foreign_keys
        foreign_keys = list()
        for table in example["tables"]:
            for pair_str in table["table_info"]["foreign_key"]:
                a, b = [_.strip() for _ in pair_str[1:-1].split(",")]
                foreign_keys.append(f"{a}={b}")
        foreign_keys = f"{', '.join(foreign_keys)}"

        prompt_info = self.template_info.format(example["question"], schemas, foreign_keys)
        prompt_extra_info = self.get_extra_info(example["db_id"])
        prompt_question = self.template_question

        if prompt_extra_info is None or prompt_extra_info == "":
            prompt_components = [prompt_info, prompt_question]
        else:
            # TODO: extra_info should be after info
            prompt_components = [prompt_info, prompt_extra_info, prompt_question]

        prompt = "\n".join(prompt_components)
        return prompt




class TextWithRulePrompt(BasicPrompt):
    template_info = "Given the following database schema:\n" \
                  "{}"
    template_question = "Answer the following with no explanation: {}"

    def format_question(self, example: dict):
        schemas = "\n".join([f"{_.name}: {', '.join(_.schema)}" for _ in example["tables"]])

        prompt_info = self.template_info.format(schemas)
        prompt_extra_info = self.get_extra_info(example["db_id"])
        prompt_question = self.template_question.format(example["question"])

        if prompt_extra_info is None or prompt_extra_info == "":
            prompt_components = [prompt_info,prompt_question]
        else:
            prompt_components = [prompt_info, prompt_extra_info, prompt_question]

        prompt = "\n".join(prompt_components)
        return prompt


class NumberSignWithoutRulePrompt(BasicPrompt):
    template_info = "### Complete sqlite SQL query\n" \
                    "### SQLite SQL tables, with their properties:\n" \
                    "#\n" \
                    "{}\n" \
                    "#"
    template_question = "### {}"

    def format_question(self, example: dict):
        schemas = "\n".join([f"# {_.name}({', '.join(_.schema)})" for _ in example["tables"]])

        prompt_info = self.template_info.format(schemas)
        prompt_extra_info = self.get_extra_info(example["db_id"])
        prompt_question = self.template_question.format(example["question"])

        if prompt_extra_info is None or prompt_extra_info == "":
            prompt_components = [prompt_info,prompt_question]
        else:
            prompt_components = [prompt_info, prompt_extra_info, prompt_question]

        prompt = "\n".join(prompt_components)
        return prompt


class InstructionWithRulePrompt(BasicPrompt):
    template_info = (
        "Below is an instruction that describes a task, paired with an input that provides further context. "
        "Write a response that appropriately completes the request.\n\n"
        "### Instruction:\nWrite a sql only and with no explanation to answer the question \"{}\"\n\n### Input:\n{}\n"
    )
    template_question = "### Response:"

    def format_question(self, example: dict):
        schemas = "\n".join([f"{_.name}({', '.join(_.schema)})" for _ in example["tables"]])

        prompt_info = self.template_info.format(example["question"], schemas)
        prompt_extra_info = self.get_extra_info(example["db_id"])
        prompt_question = self.template_question

        if prompt_extra_info is None or prompt_extra_info == "":
            prompt_components = [prompt_info, prompt_question]
        else:
            # TODO: extra_info should be after info
            prompt_components = [prompt_info, prompt_extra_info, prompt_question]

        prompt = "\n".join(prompt_components)
        return prompt


class TextCOTPrompt(BasicPrompt):
    template_info = "Given the following database schema:\n" \
                  "{}"
    template_question = "Let's think step by step. Answer the following: {}"

    def format_question(self, example: dict):
        schemas = "\n".join([f"{_.name}: {', '.join(_.schema)}" for _ in example["tables"]])

        prompt_info = self.template_info.format(schemas)
        prompt_extra_info = self.get_extra_info(example["db_id"])
        prompt_question = self.template_question.format(example["question"])

        if prompt_extra_info is None or prompt_extra_info == "":
            prompt_components = [prompt_info,prompt_question]
        else:
            prompt_components = [prompt_info, prompt_extra_info, prompt_question]

        prompt = "\n".join(prompt_components)
        return prompt

    def format_target(self, example: dict):
        return self.format_question(example)


class NumberSignCOTPrompt(BasicPrompt):
    """
    This class generates Chain-of-Thought style prompts used for Text-to-SQL tasks,
    following the format proposed in the DIAL-SQL paper.

    Prompt ：
    -----------------------------------
    ### Let's think step by step. Complete sqlite SQL query only and with no explanation
    ### SQLite SQL tables, with their properties:
    #
    # table1(column1, column2)
    # table2(column1, column2)
    #
    ### What is the total number of users in the table?
    -----------------------------------
    """

    # Template for general instruction and schema display
    template_info = "### Let's think step by step. Complete sqlite SQL query only and with no explanation\n" \
                    "### SQLite SQL tables, with their properties:\n" \
                    "#\n" \
                    "{}\n" \
                    "#"

    # Template for the actual natural language question
    template_question = "### {}"

    def format_question(self, example: dict):
        """
        Generate the full prompt string from an input example.

        Args:
            example (dict): ：
                - "question": （e.g., "How many users are there?"）
                - "tables": ，：
                    {
                        "name": ,
                        "schema": （e.g., ["id", "name"]）
                    }
                - "db_id": ，

        Returns:
            str:  Prompt
        """

        schemas = "\n".join([f"# {table['name']}({', '.join(table['schema'])})" for table in example["tables"]])
        # schema_list = []
        # for table in example["tables"]:
        #     table_name = table['name']
        #     schema_str = ", ".join(table['schema'])
        #     db_desc = table.get('database_description', '')
        #     db_desc = "Database Description:" + db_desc if db_desc != '' else ''
        #     table_description = f"# {table_name}({schema_str})\n{db_desc}"
        #     schema_list.append(table_description)
        # schemas = "\n".join(schema_list)

        prompt_info = self.template_info.format(schemas)
        prompt_extra_info = self.get_extra_info(example)
        prompt_question = self.template_question.format(example["question"])  #  template_question{}question

        if prompt_extra_info is None or prompt_extra_info == "":
            prompt_components = [prompt_info,prompt_question]
        else:
            prompt_components = [prompt_info, prompt_extra_info, prompt_question]

        prompt = "\n".join(prompt_components)
        return prompt

    def format_target(self, example: dict):
        return self.format_question(example)


class InstructionCOTPrompt(BasicPrompt):
    template_info = (
        "Below is an instruction that describes a task, paired with an input that provides further context. "
        "Write a response that appropriately completes the request.\n\n"
        "### Instruction:\nLet's think step by step. Write a sql to answer the question \"{}\"\n\n### Input:\n{}\n"
    )
    template_question = "### Response:"

    def format_question(self, example: dict):
        schemas = "\n".join([f"{_.name}({', '.join(_.schema)})" for _ in example["tables"]])

        prompt_info = self.template_info.format(example["question"], schemas)
        prompt_extra_info = self.get_extra_info(example["db_id"])
        prompt_question = self.template_question

        if prompt_extra_info is None or prompt_extra_info == "":
            prompt_components = [prompt_info, prompt_question]
        else:
            # TODO: extra_info should be after info
            prompt_components = [prompt_info, prompt_extra_info, prompt_question]

        prompt = "\n".join(prompt_components)
        return prompt

    def format_target(self, example: dict):
        return self.format_question(example)


class CBRPrompt(BasicPrompt):
    template_info = "# The following are the table names and column names needed to generate SQL:\n" \
                    "Tables: {}\n" \
                    "Columns: *, {}\n" \
                    "Foreign keys: {}"
    template_question = '# translate "{}" into SQL query only and with no explanation:'

    def format_question(self, example: dict):
        tables = ", ".join([f"{_.name}" for _ in example["tables"]])
        columns = ", ".join([f"{_.name}.{col}" for _ in example["tables"] for col in _.schema])
        # foreign_keys
        foreign_keys = list()
        for table in example["tables"]:
            for pair_str in table["table_info"]["foreign_key"]:
                a, b = [_.strip() for _ in pair_str[1:-1].split(",")]
                foreign_keys.append(f"{a}={b}")
        foreign_keys = f"{', '.join(foreign_keys)}"

        prompt_info = self.template_info.format(tables, columns, foreign_keys)
        prompt_extra_info = self.get_extra_info(example["db_id"])
        prompt_question = self.template_question.format(example["question"])

        if prompt_extra_info is None or prompt_extra_info == "":
            prompt_components = [prompt_info,prompt_question]
        else:
            prompt_components = [prompt_info, prompt_extra_info, prompt_question]

        prompt = "\n".join(prompt_components)
        return prompt