## C7: Aggregation Function Misuse
### QMR-2: Logical Decomposition
**1. Equivalent**

``` python
prompt = (  
    f"Rewrite the following question into {n} equivalent questions, which include both original question and logically decomposed step-by-step CoT instructions. "    f"Each rewritten version must preserve the original question's meaning and result set, but explicitly decompose its logic into smaller steps (especially Aggregation Function, e.g., total, average, how many, max). "      
    f"Your rewrites should focus only on logical decomposition, not on rephrasing or paraphrasing individual words.\n\n"  
  
    f"Example 1:\n"  
    f"Original question: Calculate total quantity of ordered items\n"  
    f"Equivalent question:Calculate total quantity of ordered items. CoT Steps:Retrieve all orders. Extract the field order_quantity.Apply SUM over order_quantity.\n"  
  
    f"Example 2:\n"  
    f"Original question: What is the average price of products\n"  
    f"Equivalent question: What is the average price of products. CoT Steps:Retrieve all products. Extract the field price.Apply AVG over price.\n"  
  
    f"Example 3:\n"  
    f"Original question: Find total sales amount for each region\n"  
    f"Equivalent question: Find total sales amount for each region. CoT Steps:Retrieve all orders. Group orders by region. For each region, apply SUM over sales.\n"  
  
    f"Now generate {n} equivalent questions for the following question:\n"  
    f"Question: {self.question}\n"  
    f"Do not include any explanations in your response. Ensure that return total {n} equivalent questions, each separated by a newline, totally {n} lines.")
```
### QMR-4: Error-Type Reflection
**1. Equivalent**
``` python
metamorphic_question = f"{self.question}\n" + \  
f"### Important rules: 1.After generating the query, you must verify whether the query introduces a {hallu_type_name} hallucination." + \  
"2. If the query introduces such error, fix it automatically." + \  
"3. The final output must only be the corrected query, with no explanation.\n"
```