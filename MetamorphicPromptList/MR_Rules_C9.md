## C9: OrderBy Misuse
### QMR-3: Constraint Explicitization

**1. Equivalent**

``` python
prompt = (  
    f"Rewrite the following question into {n} equivalent questions,which include both original question and explicit constraints about OrderBy,  making all implicit constraints about OrderBy explicit."    f"You should reformulate vague or underspecified instructions into precise control parameters, without changing the query's overall meaning or result set.\n\n"  
  
    f"Example 1:\n"  
    f"Original question: List products by price from high to low.\n"  
    f"Equivalent question: List products by price from high to low. Explicit constraints about OrderBy: List all products ordered by price in descending order, so that the most expensive products appear first.\n"  
  
    f"Example 2:\n"  
    f"Original question: List the top 10 students by GPA.\n"  
    f"Equivalent question: List the top 10 students by GPA. Explicit constraints about OrderBy: List the 10 students with the highest GPA, ordered by GPA in descending order, so the top students appear first.\n"  
  
    f"Example 3:\n"  
    f"Original question: Show products ordered by category then price.\n"  
    f"Equivalent question: Show products ordered by category then price. Explicit constraints about OrderBy: List all products ordered first by category in ascending order, and within each category ordered by price in descending order.\n\n"  
  
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