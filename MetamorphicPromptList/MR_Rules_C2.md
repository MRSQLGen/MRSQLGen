## C2: Limit Error
### QMR-3: Constraint Explicitization
**1. Equivalent**

```python
prompt = (  
  
    f"Rewrite the following question into {n} equivalent questions,which include both original question and explicit constraints about LIMIT, making all implicit constraints about LIMIT explicit."    f"You should reformulate vague or underspecified instructions into precise control parameters,without changing the query's overall meaning or result set.\n\n"  
  
    f"Example 1:\n"  
    f"Original question: List the top 10 best-selling products\n"  
    f"Equivalent question: List the top 10 best-selling products.Explicit constraints about LIMIT: Best-selling means the products with the highest total sales, ordered by sales in descending order.Return only the top 10.\n"  
  
    f"Example 2:\n"  
    f"Original question: Show the top 5 students with highest GPA\n"  
    f"Equivalent question: Show the top 5 students with highest GPA. Explicit constraints about LIMIT: List students ranked by GPA in descending order, returning only the top 5.\n"  
  
    f"Example 3:\n"  
    f"Original question: List the 2nd page of results, 10 per page\n"  
    f"Equivalent question: List the 2nd page of results, 10 per page. Explicit constraints about LIMIT: This means there exist 10 results per page.Retrieve results ordered in descending order, skip the first 10, and return the next 10.\n"  
  
    f"Example 4:\n"  
    f"Original question: Return the top 3 most expensive products\n"  
    f"Equivalent question: Return the top 3 most expensive products. Explicit constraints about LIMIT: Order products by price in descending order, returning only the top 3.\n"  
  
    f"Now generate {n} equivalent questions for the following question:\n"  
    f"Question: {self.question}\n"  
    f"Do not include any explanations in your response. Just return the {n} equivalent questions, each separated by a newline.")
```


### QMR-4: Error-Type Reflection
**1. Equivalent**
``` python
metamorphic_question = f"{self.question}\n" + \  
f"### Important rules: 1.After generating the query, you must verify whether the query introduces a {hallu_type_name} hallucination." + \  
"2. If the query introduces such error, fix it automatically." + \  
"3. The final output must only be the corrected query, with no explanation.\n"
```
