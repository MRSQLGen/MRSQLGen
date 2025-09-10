## 1 Datasets
### 1.1 SPIDER
Spider is a cross-domain dataset comprising 10,181 natural language questions over 200 databases. Please download the [Spider1.0](https://yale-lily.github.io//spider) dataset from this [link](https://drive.google.com/file/d/1403EGqzIDoHMdQF4c9Bkyl7dZLZ5Wt6J/view) and extract it into the directory `MRSQLGen/datasets/spider_data`.

The data content and format is introduced in this link: [taoyds/spider: data-content-and-format](https://github.com/taoyds/spider?tab=readme-ov-file#data-content-and-format).
### 1.2 BIRD
Bird is a recent and more challenging NL2SQL benchmark. It consists of 10,962 text-SQL pairs across 95 databases and includes more complex SQL structures. Please download the `train.zip` and `dev.zip` from  [BIRD-bench](https://bird-bench.github.io/) and extract them into the directory `MRSQLGen/datasets/bird_data`.

The data content and format is introduced in this link:  [DAMO-ConvAI/bird](https://github.com/AlibabaResearch/DAMO-ConvAI/tree/main/bird#dataset-introduction).

### 1.3 Structure of the Dataset Directory
Below is the structure of the dataset directory:
```swift
datasets/
├── bird_data/
│   ├── dev_databases/
│   ├── train_databases/
│   ├── dev.json
│   ├── dev.sql
│   ├── dev_tables.json
│   ├── dev_tied_append.json
│   ├── train.json
│   ├── train_gold.sql
│   └── train_tables.json
├── spider_data/
│   ├── database/
│   ├── test_database/
│   ├── README.txt
│   ├── tables.json
│   ├── test.json
│   ├── test_gold.sql
│   ├── test_tables.json
│   ├── train_gold.sql
│   ├── train_others.json
└   └── train_spider.json
```
## 2 Baselines
### 2.1 SelfCheckGPT
SelfCheckGPT is a state-of-the-art confidence-based hallucination detector originally designed for open-ended text generation. Following the original setup, we use **a sampling temperature of 1.0** and apply a threshold-based rule to classify a query as hallucinated if its sampled variants show low consistency **(selfcheckgpt_model="nli",threshold=0.5, N=10)**. The execution code of SelfCheckGPT is located in [selfcheckgpt](app/selfcheckgpt_runner.py).

To run **SelfCheckGPT Tool** with **a specific Large Language Model** on dataset **SPIDER or BIRD**, use the provided [run_selfcheckgpt.py](app/Run/run_selfcheckgpt.py) script. We also fill in some configuration information for demos in the [selfcheckgpt_configs](app/configs/selfcheckgpt_configs) folder. The script accepts several arguments to control the process:

| Argument                  | Description                                                                                                |
| ------------------------- | ---------------------------------------------------------------------------------------------------------- |
| `--llm_model_config_file` | Path to the JSON file specifying the LLM model configuration (e.g., api_key, model_name).                  |
| `--runner_config_file`    | Path to the JSON file containing the runner configuration (e.g., temperature, threshold).                  |
| `--input_json`            | Path to the input JSON file containing dataset samples(e.g., SPIDER or BIRD).                              |
| `--dataset_name`          | Name of the dataset (e.g., `bird`, `spider`).                                                              |
| `--dataset_path`          | Path to the dataset directory where schema and related files are stored(e.g., `bird_data`, `spider_data`). |
| `--output_dic_path`       | Path to the directory where output results and evaluation results will be saved.                           |
| `--num_examples`          | Number of examples to run for the experiment.                                                              |
#### 2.1.1 BIRD
```bash
cd MRSQLGen

python -m app.Run.run_selfcheckgpt \
	--llm_model_config_file "app/configs/llm_model_configs/gpt-4o-mini.json" \
	--runner_config_file "app/configs/selfcheckgpt_configs/bird-demo.json" \
	--input_json "datasets/bird_data/dev.json" \
	--dataset_name "bird" \
	--dataset_path "datasets/bird_data" \
	--output_dic_path "BaselineResults" \
	--num_examples 50
```
#### 2.1.2 SPIDER
```bash
cd MRSQLGen

python -m app.Run.run_selfcheckgpt \
	--llm_model_config_file "app/configs/llm_model_configs/gpt-4o-mini.json" \
	--runner_config_file "app/configs/selfcheckgpt_configs/spider-demo.json" \
	--input_json "datasets/spider_data/dev.json" \
	--dataset_name "spider" \
	--dataset_path "datasets/spider_data" \
	--output_dic_path "BaselineResults" \
	--num_examples 50
```
### 2.2 LLM-as-a-Judge
LLM-as-a-Judge leverages the LLM itself to reflect on and assess the hallucination of its generated output. The execution code of LLM-as-a-judge is located in [llm-as-a-judge](app/llm_as_a_judge_runner.py).

To run **LLM-as-a-Judge Tool** with **a specific Large Language Model** on dataset **SPIDER or BIRD**, use the provided [run_llm_as_a_judge.py](app/Run/run_llm_as_a_judge.py) script. We also fill in some configuration information for demos in the [llm_as_a_judge_configs](app/configs/llm_as_a_judge_configs) folder. The script accepts several arguments to control the process:

| Argument                  | Description                                                                                                |
| ------------------------- | ---------------------------------------------------------------------------------------------------------- |
| `--llm_model_config_file` | Path to the JSON file specifying the LLM model configuration (e.g., api_key, model_name).                  |
| `--runner_config_file`    | Path to the JSON file containing the runner configuration (e.g., temperature, threshold).                  |
| `--input_json`            | Path to the input JSON file containing dataset samples(e.g., SPIDER or BIRD).                              |
| `--dataset_name`          | Name of the dataset (e.g., `bird`, `spider`).                                                              |
| `--dataset_path`          | Path to the dataset directory where schema and related files are stored(e.g., `bird_data`, `spider_data`). |
| `--output_dic_path`       | Path to the directory where output results and evaluation results will be saved.                           |
| `--num_examples`          | Number of examples to run for the experiment.                                                              |
#### 2.2.1 BIRD
```bash
cd MRSQLGen

python -m app.Run.run_llm_as_a_judge \
	--llm_model_config_file "app/configs/llm_model_configs/gpt-4o-mini.json" \
	--runner_config_file "app/configs/llm_as_a_judge_configs/bird-demo.json" \
	--input_json "datasets/bird_data/dev.json" \
	--dataset_name "bird" \
	--dataset_path "datasets/bird_data" \
	--output_dic_path "BaselineResults" \
	--num_examples 50

```
#### 2.2.2 SPIDER
```bash
cd MRSQLGen

python -m app.Run.run_llm_as_a_judge \
	--llm_model_config_file "app/configs/llm_model_configs/gpt-4o-mini.json" \
	--runner_config_file "app/configs/llm_as_a_judge_configs/spider-demo.json" \
	--input_json "datasets/spider_data/dev.json" \
	--dataset_name "spider" \
	--dataset_path "datasets/spider_data" \
	--output_dic_path "BaselineResults" \
	--num_examples 50
```