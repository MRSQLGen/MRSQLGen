# Validating LLM-Generated SQL Queries Through Metamorphic Prompting
## 1 Description
MRSQLGen is a **reference-free** hallucination detection framework for LLM-generated SQL. Based on **metamorphic prompting paradigm**, it rewrites input prompts using task-specific transformation rules and validates queries by checking behavioral consistency across multiple executions.  Each transformation corresponds to a **metamorphic relationship (MR)** that defines the expected relation between results, and inconsistencies are aggregated using a majority-vote strategy to robustly flag hallucinations—without relying on ground-truth SQL.

We evaluate MRSQLGen on **Spider** and **Bird** benchmarks with five representative LLMs, including **GPT-4o**. Results show that MRSQLGen consistently **outperforms state-of-the-art hallucination detection methods, achieving higher precision and recall** in identifying hallucinated SQL queries.
## 2 Usage
### 2.1 Environment Setup
To set up the environment for running MRSQLGen, please follow the instructions below:
1. Download the MRSQLGen Tool : 
```bash
git clone https://github.com/MRSQLGen/MRSQLGen.git
cd MRSQLGen
```
2. Install the required dependencies listed in requirements.txt:
```bash
pip install -r requirements.txt 
```
### 2.2 Data Preparation
1. (Optional) Download the datasets:
	* [SPIDER](Datasets%20and%20Baselines.md#spider)
	* [BIRD](Datasets%20and%20Baselines.md#bird)
2. (Optional) Datasets Preprocess :
	* SPIDER : 
	``` shell
	python -m app.Tools.process_database_schema --data_dic "app/datasets/spider_data"
	```
	* BIRD :  
	``` shell
	python -m app.Tools.process_database_schema --data_dic "app/datasets/bird_data"
	```
### 2.3 LLM Deployment
1. Deploy the large language models (LLMs) to be tested, supported LLMs are:
	- gpt-4o
	- gpt-4o-mini
	- deepseek-coder-v2:16b
	- qwen2.5-coder:14b
	- codellama:13b-instruct
> Note: The three open source LLMs (`deepseek-coder-v2:16b`, `qwen2.5-coder:14b`, `codellama:13b-instruct`) can be deployed through Ollama.
2. Fill in the LLM model configuration information in the [llm_model_configs](app/configs/llm_model_configs) folder.
### 2.4 Hallucination Detection
To run **MRSQLGen Tool** with **a specific Large Language Model** on dataset **SPIDER or BIRD**, use the provided [run_mrsqlgen.py](app/Run/run_mrsqlgen.py) script. We also fill in some configuration information for demos in the [mrsqlgen_configs](app/configs/mrsqlgen_configs) folder. The script accepts several arguments to control the process:

| Argument                  | Description                                                                                                |
| ------------------------- | ---------------------------------------------------------------------------------------------------------- |
| `--llm_model_config_file` | Path to the JSON file specifying the LLM model configuration (e.g., api_key, model_name).                  |
| `--runner_config_file`    | Path to the JSON file containing the runner configuration (e.g., temperature, threshold).                  |
| `--input_json`            | Path to the input JSON file containing dataset samples(e.g., SPIDER or BIRD).                              |
| `--dataset_name`          | Name of the dataset (e.g., `bird`, `spider`).                                                              |
| `--dataset_path`          | Path to the dataset directory where schema and related files are stored(e.g., `bird_data`, `spider_data`). |
| `--output_dic_path`       | Path to the directory where output results and evaluation results will be saved.                           |
| `--num_examples`          | Number of examples to run for the experiment.                                                              |
#### 2.4.1 BIRD
```bash
cd MRSQLGen

python -m app.Run.run_mrsqlgen \
	--llm_model_config_file "app/configs/llm_model_configs/gpt-4o-mini.json" \
	--runner_config_file "app/configs/mrsqlgen_configs/bird-demo.json" \
	--input_json "datasets/bird_data/dev.json" \
	--dataset_name "bird" \
	--dataset_path "datasets/bird_data" \
	--output_dic_path "MRSQLGenResults" \
	--num_examples 50
```
#### 2.4.2 SPIDER
```bash
cd MRSQLGen

python -m app.Run.run_mrsqlgen \
	--llm_model_config_file "app/configs/llm_model_configs/gpt-4o-mini.json" \
	--runner_config_file "app/configs/mrsqlgen_configs/spider-demo.json" \
	--input_json "datasets/spider_data/dev.json" \
	--dataset_name "spider" \
	--dataset_path "datasets/spider_data" \
	--output_dic_path "MRSQLGenResults" \
	--num_examples 50
```

### 2.5 Evaluation
The execution code is located in [evaluation_manager.py](app/evaluation_manager.py). Experiment evaluation results are stored in their  `--output_dic_path`, including: 

| File                            | Description                                                                                                       |
| ------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| `config.json`                   | JSON file recording the runner configuration.                                                                     |
| `evaluation.json`               | JSON file containing the main evaluation results of input samples (e.g., SPIDER, BIRD).                           |
| `ablation_evaluation.json`      | JSON file containing the ablation experiments' evaluation results of input samples (e.g., SPIDER, BIRD).          |
| `type_identify_evaluation.json` | JSON file containing the evaluation results of [Hallucination Type Retrieval](app/hallucination_type_retrieval) . |
