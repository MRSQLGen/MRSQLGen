## C10: GroupBy Misuse
### QMR-2: Logical Decomposition
**1. Equivalent**

``` python
prompt = (  
    f"Rewrite the following question into {n} equivalent questions, which include both original question and logically decomposed step-by-step CoT instructions. "    f"Each rewritten CoT steps must preserve the original question's meaning and result set, but explicitly decompose its logic into smaller steps (especially GroupBy, e.g., for each, split by, grouped by). "      
    f"Your rewrites should focus only on logical decomposition, not on rephrasing or paraphrasing individual words.\n\n"  
  
    f"Example 1:\n"  
    f"Original question: Show total sales for each region\n"  
    f"Equivalent question: Show total sales for each region. CoT Steps:Retrieve all orders. Group orders by region. For each region, apply SUM over sales.\n"  
  
    f"Example 2:\n"  
    f"Original question: Count employees in each department\n"  
    f"Equivalent question: Count employees in each department. CoT Steps:Retrieve all employees. Group employees by department. For each department, apply COUNT over employees.\n"  
  
    f"Example 3:\n"  
    f"Original question: Find all employees with salary above 5000\n"  
    f"Equivalent question: Find all employees with salary above 5000. CoT Steps:Retrieve all employees. Extract salary field. Filter employees where salary > 5000.\n"  
  
    f"Example 4:\n"  
    f"Original question: Show the number of orders per day\n"  
    f"Equivalent question: Show the number of orders per day. CoT Steps:Retrieve all orders. Group orders by order_date. For each day, apply COUNT over order_id.\n"  
  
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