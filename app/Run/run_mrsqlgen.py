import os
from app.experiment_runner import ExperimentRunner
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--llm_model_config_file", type=str, required=True)
    parser.add_argument("--runner_config_file", type=str, required=True)
    parser.add_argument("--input_json", type=str, required=True)
    parser.add_argument("--dataset_name", type=str, required=True)
    parser.add_argument("--dataset_path", type=str, required=True)
    parser.add_argument("--output_dic_path", type=str, required=True)
    parser.add_argument("--num_examples", type=int, required=True)

    args = parser.parse_args()

    runner = ExperimentRunner(
        llm_model_config_file=args.llm_model_config_file,
        runner_config_file=args.runner_config_file,
    )
    runner.run(args.input_json, args.dataset_name, args.dataset_path, args.output_dic_path, args.num_examples)
