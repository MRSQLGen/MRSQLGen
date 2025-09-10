import os
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
import json
import torch
import numpy as np
from selfcheckgpt.modeling_selfcheck import SelfCheckBERTScore, SelfCheckMQAG, SelfCheckNgram, SelfCheckNLI
import spacy
nlp = spacy.load("en_core_web_sm")

def extract_questions_queries_from_file(file_path):
    """
    :param file_path:
    :return: [[question1,query1],[question2,query2],...]
    question = prompt， query = real_query
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File Not Exists: {file_path}")
    if not file_path.lower().endswith('.json'):
        raise ValueError("must be JSON")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                f.seek(0)
                data = [json.loads(line) for line in f if line.strip()]

        if not isinstance(data, list):
            raise ValueError("JSON")

        results = []
        for item in data:
            if isinstance(item, dict):
                question = item.get("question")
                query = item.get("query")

                if question and query:
                    results.append((question.strip(), query.strip()))

        return results

    except Exception as e:
        raise RuntimeError(f"File Error: {str(e)}") from e


class SelfCheckGPTCaller:
    def __init__(self, model_name):
        self.model_name = model_name
        self.device = self.setup_environment()

    def setup_environment(self):
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        if device.type == "cuda":
            print(f"Using GPU: {torch.cuda.get_device_name(0)}")
            print("Visible devices:", torch.cuda.device_count())
            print("Current device id:", torch.cuda.current_device())
            print("Current device name:", torch.cuda.get_device_name(torch.cuda.current_device()))
        else:
            print("Using CPU")
        return device

    def get_predict_scores(self, sampled_passages, passage=None, threshold=None):
        """
        :param model_name:(bertscore/mqag/ngram/nli/prompt)
        :param initial_sentences
        :param sampled_passages
        :param passage: (MQAG/Ngram)
        :return:
        """
        model_item = self.get_model()
        if not model_item:
            raise ValueError(f"Unsupported model: {self.model_name}")

        sentences = [sent.text.strip() for sent in nlp(passage).sents]  # spacy sentence tokenization

        if self.model_name.lower() == "bertscore":
            scores = model_item.predict(sentences=sentences, sampled_passages=sampled_passages)
            # return self._extract_first_score(scores)
            mean_scores = self._extract_mean_score(scores)
            is_hallucination = bool(mean_scores > threshold)
            return mean_scores,scores, is_hallucination

        elif self.model_name.lower() == "mqag":
            scores = model_item.predict(
                sentences=sentences,
                passage=passage,
                sampled_passages=sampled_passages,
                num_questions_per_sent=5,
                scoring_method='bayes_with_alpha',
                beta1=0.8,
                beta2=0.8
            )
            # return self._extract_first_score(scores)
            mean_scores = self._extract_mean_score(scores)
            is_hallucination = bool(mean_scores > threshold)
            return mean_scores,scores, is_hallucination

        elif self.model_name.lower() == "ngram":
            result_dict = model_item.predict(
                sentences=sentences,
                passage=passage,
                sampled_passages=sampled_passages
            )
            if 'sent_level' in result_dict and 'max_neg_logprob' in result_dict['sent_level']:
                scores = result_dict['sent_level']['max_neg_logprob']
                # return self._extract_first_score(scores)
                mean_scores = self._extract_mean_score(scores)
                is_hallucination = bool(mean_scores > threshold)
                return mean_scores, scores, is_hallucination
            else:
                raise ValueError("Invalid Ngram result structure")

        elif self.model_name.lower() == "nli":
            print(sentences)
            print(sampled_passages)
            scores = model_item.predict(
                sentences=sentences,
                sampled_passages=sampled_passages
            )
            # return self._extract_first_score(scores)
            mean_scores = self._extract_mean_score(scores)
            is_hallucination = bool(mean_scores > threshold)
            return mean_scores, scores, is_hallucination

        elif self.model_name.lower() == "prompt":
            scores = model_item.predict(
                sentences=sentences,
                sampled_passages=sampled_passages
            )
            # return self._extract_first_score(scores)
            mean_scores = self._extract_mean_score(scores)
            is_hallucination = bool(mean_scores > threshold)
            return mean_scores, scores, is_hallucination

    def get_model(self):
        model_name = self.model_name
        if model_name.lower() == "bertscore":
            return SelfCheckBERTScore(rescale_with_baseline=True)
        elif model_name.lower() == "mqag":
            return SelfCheckMQAG(device=self.device)
        elif model_name.lower() == "ngram":
            return SelfCheckNgram(n=1)
        elif model_name.lower() == "nli":
            return SelfCheckNLI(device=self.device)
        else:
            print("selfcheckgpt doesn't support this model!")
        print("get model:"+model_name)


    def _extract_mean_score(self, scores):
        return np.mean(scores)

    def _extract_first_score(self, scores):
        if isinstance(scores, np.ndarray):
            if scores.size > 0:
                return float(scores[0])

        elif isinstance(scores, list):
            if len(scores) > 0:
                if isinstance(scores[0], np.generic):
                    return float(scores[0])
                return float(scores[0])

        elif isinstance(scores, (int, float)):
            return float(scores)

        return 0.0


def run_tests(test_data):
    results = {}
    models_config = {
        # "bertscore": {"threshold": 0.3, "requires_passage": False}, # 0,1
        # "mqag": {"threshold": 0.5, "requires_passage": True},  # 0,1
        # "ngram": {"threshold": 4.0, "requires_passage": True},  # 0
        "nli": {"threshold": 0.8, "requires_passage": False}, # 0,1
        # "prompt": {"threshold": 0.5, "requires_passage": False}
    }

    for model_name, config in models_config.items():
        print(f"\n{'=' * 30} {model_name.upper()} TEST {'=' * 30}")

        kwargs = {
            "passage": test_data["passage"],
            "sampled_passages": test_data["generated_queries"],
            "threshold" : config["threshold"]
        }
        try:
            selfcheckgpt_caller = SelfCheckGPTCaller(model_name)
            mean_scores, scores, is_hallucination = selfcheckgpt_caller.get_predict_scores(**kwargs)
            print(f"{model_name} mean score: {mean_scores:.4f} \n{model_name} score: {str(scores)} \nis_hallucination:{str(is_hallucination)}")
        except Exception as e:
            print(f"Error during {model_name} test: {str(e)}")




