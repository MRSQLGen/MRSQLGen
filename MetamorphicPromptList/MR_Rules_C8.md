## C8: Distinct Error
### QMR-3: Constraint Explicitization
**1. Equivalent**

``` python
prompt = (  
    f"Rewrite the following question into {n} equivalent questions,which include both original question and explicit constraints about DISTINCT,  making all implicit constraints about DISTINCT explicit."    f"You should reformulate vague or underspecified instructions into precise control parameters, without changing the query's overall meaning or result set.\n\n"  
  
    f"Example 1:\n"  
    f"Original question: List all unique customer cities.\n"  
    f"Equivalent question: List all unique customer cities. Explicit constraints about DISTINCT: List all customer cities, but only return each city once without duplicates (i.e., enforce DISTINCT).\n"  
  
    f"Example 2:\n"  
    f"Original question: Show all product categories.\n"  
    f"Equivalent question: Show all product categories. Explicit constraints about DISTINCT: Show all product categories, allowing duplicates if multiple products share the same category (do not add DISTINCT).\n"  
  
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