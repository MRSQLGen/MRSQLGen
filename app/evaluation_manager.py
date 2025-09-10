from typing import List, Tuple

class EvaluationManager:
    """
    Evaluation Manager (EvaluationManager)
    ======================================
    Used to calculate typical binary classification evaluation metrics based on a set of (pred, real) values,
    suitable for hallucination detection evaluation tasks of LLM-generated SQL.

    This class evaluates the performance of a hallucination detection system using
    classic binary classification metrics.

    - pred: Model prediction of whether hallucination exists (1 = hallucination, 0 = normal)
    - real: Ground truth of whether hallucination exists (1 = hallucination, 0 = normal)
    """

    def __init__(self, pred_real_list: List[Tuple[bool, bool]]):
        """
        Initialize the EvaluationManager and compute confusion matrix.

        :param pred_real_list: A list of tuples containing (pred, real)
            - pred: Model detection result of hallucination (1 or 0)
            - real: Ground truth of hallucination (1 or 0)
        """

        self.pred_real_list = pred_real_list

        # ：、、、
        self.TP = 0  # True Positive：，
        self.FP = 0  # False Positive：，
        self.TN = 0  # True Negative：，
        self.FN = 0  # False Negative：，
        self.total = 0  #

        self._compute_confusion_matrix()

    def _compute_confusion_matrix(self):
        for pred, real in self.pred_real_list:
            if real == 1 and pred == 1:
                self.TP += 1
            elif real == 0 and pred == 1:
                self.FP += 1
            elif real == 0 and pred == 0:
                self.TN += 1
            elif real == 1 and pred == 0:
                self.FN += 1
            else:
                raise ValueError(f"Invalid pred/real values: pred={pred}, real={real}")
        self.total = self.TP + self.TN + self.FP + self.FN


    def accuracy(self) -> float:
        return (self.TP + self.TN) / self.total if self.total > 0 else 0.0

    def recall(self) -> float:
        denom = self.TP + self.FN
        return self.TP / denom if denom > 0 else 0.0

    def false_positive_rate(self) -> float:
        denom = self.FP + self.TN
        return self.FP / denom if denom > 0 else 0.0

    def precision(self) -> float:
        denom = self.TP + self.FP
        return self.TP / denom if denom > 0 else 0.0

    def f1_score(self) -> float:
        p = self.precision()
        r = self.recall()
        denom = p + r
        return 2 * (p * r) / denom if denom > 0 else 0.0

    def summary(self) -> dict:
        return {
            "TP": self.TP,
            "FP": self.FP,
            "TN": self.TN,
            "FN": self.FN,
            "TOTAL": self.total,
            "accuracy": self.accuracy(),
            "recall": self.recall(),
            "false_positive_rate": self.false_positive_rate(),
            "precision": self.precision(),
            "f1_score": self.f1_score(),
        }
