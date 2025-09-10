import torch
import re

class LLMAsAJudgeCaller:
    def __init__(self, model_name='gpt-3.5-turbo'):
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


    def get_predict_type(self, question: str, generated_sql: str, schema_str: str, model) -> dict:
        """Main entry: let the model score and determine whether it is a hallucination"""
        # Call the model to obtain the score and hallucination judgment text
        eval_result, usage = self.evaluate_sql_output(question, schema_str, generated_sql, model)

        # Hallucination detection: check whether a hallucination judgment was returned.
        # If not, return "Unknown" and mark as not evaluated.
        try:
            hallucination_detected = re.search(r"Hallucination Detected: (Yes|No)", eval_result).group(1).strip().lower()
        except AttributeError:
            hallucination_detected = "unknown"

        if hallucination_detected == "unknown":
            hallucinated = "Unknown"
        else:
            hallucinated = hallucination_detected == "yes"

        return {
            "pred": hallucinated,
            "explanation": eval_result,
            "usage": usage
        }

    def evaluate_sql_output(self, question: str, schema_text: str, generated_sql: str, model) -> str:
        prompt = f"""
        You are an expert in evaluating SQL queries. Please evaluate the following SQL query based on two criteria:

        (1) **Semantic Correctness**: Does the SQL query accurately represent the intent of the natural language question? 
        Check for logical consistency and ensure the query answers the user's question as expected.

        (2) **Structural Correctness**: Is the SQL query syntactically valid and logically sound based on the provided database schema? 
        Ensure the query follows correct SQL syntax, references the correct tables and columns, and adheres to proper SQL practices.

        After evaluating the above criteria, please determine if the generated SQL query exhibits any **hallucination**. 
        A hallucination is when the SQL query does not reflect the intent of the question or introduces incorrect logic.

        ### Database Schema:
        {schema_text}

        ### Question:
        {question}

        ### Generated SQL:
        {generated_sql}
        
        ### Important:
        Please provide a score from 1 to 5 for each aspect and determine whether the SQL query has any **hallucination** or not. 
        You should respond only with "Yes" or "No": **Yes** if hallucination is detected, or **"No"** if no hallucination is detected. 
    
        Format your answer like this:

        Hallucination Detected: Z (Yes/No)   
        Explanation: ...
        """
        return model(prompt)