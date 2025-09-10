## C1: Operator Misuse
### QMR-1: Intent Perturbation & Reversal

**1. Equivalent**

```python
prompt = (  
    f"Generate {n} simple English questions that are semantically equivalent to the following question but different from each other, and whose corresponding SQL queries would also be logically equivalent. "    f"You must achieve this by modifying only the arithmetic, comparison, or logical operation descriptions without changing the query's overall meaning or result set.\n\n"  
  
    f"Example 1:\n"  
    f"Original question: Show each employee and their total compensation(positive number), calculated as `base_salary + bonus`.\n"  
    f"Equivalent question: Display all employees with `total_compensation = base_salary + bonus`(positive number).\n"  
  
    f"Example 2:\n"  
    f"Original question: Find employees with a salary greater than 5000.\n"  
    f"Equivalent question: Retrieve all employees whose salary is strictly above five thousand dollars.\n"  
  
    f"Example 3:\n"  
    f"Original question: Find customers who are from New York or Los Angeles.\n"  
    f"Equivalent question:Retrieve customers whose city is either New York or Los Angeles.\n"  
  
    f"Now generate {n} equivalent questions for the following question:\n"  
    f"Question: {self.question}\n"  
    f"Do not include any explanations in your response. Just return the {n} equivalent questions, each separated by a newline.")
```

**2. Superset**
```python
prompt = (  
    f"Generate {n} simple English questions whose corresponding SQL queries would return a superset of the original query's result set. "    f"i.e., the generated query should include all results of the original query and potentially more. "    f"The generated questions must be obtained by modifying only the arithmetic, comparison, or logical operation descriptions in the given question to relax or broaden the conditions, "    f"thus expanding the scope of the returned data, without changing other parts of the question.\n\n"  
  
    f"Example 1:\n"  
    f"Original question:Show each employee and their total compensation(positive number), calculated as `base_salary + bonus`.\n"  
    f"Superset question: Display all employees with `total_compensation = base_salary + bonus`, including employees with zero bonus.\n"  
  
    f"Example 2:\n"  
    f"Original question: Find employees with a salary greater than 5000.\n"  
    f"Superset question: Find employees with a salary greater than or equal to 4000.\n"  
  
    f"Example 3:\n"  
    f"Original question: Find videos longer than 10 minutes.\n"  
    f"Superset question: Find customers who are from New York, Los Angeles, or Chicago.\n"  
  
    f"Now generate {n} superset questions for the following question:\n"  
    f"Question: {self.question}\n"  
    f"Please only return the {n} superset questions separated by newlines, without any explanations or additional text.")
```

**3. Subset**

```python
prompt = (  
    f"Generate {n} simple English questions whose corresponding SQL queries would return a subset of the original query's result set. "    f"i.e., the generated query should include only a portion of the result of the original query. "    f"The generated questions must be obtained by modifying only the arithmetic, comparison, or logical operation descriptions in the given question to tighten or strengthen the conditions, "    f"thus narrowing the scope of the returned data, without changing other parts of the question.\n\n"  
  
    f"Example 1:\n"  
    f"Original question: Show each employee and their total compensation(positive number), calculated as `base_salary + bonus`.\n"  
    f"Subset question: Display employees with `total_compensation = base_salary + bonus` and bonus > 1000.\n"  
  
    f"Example 2:\n"  
    f"Original question: Find employees with a salary greater than 5000.\n"  
    f"Subset question: Find employees with a salary greater than 6000.\n"  
  
    f"Example 3:\n"  
    f"Original question: Find customers who are from New York or Los Angeles.\n"  
    f"Subset question: Find customers who are from New York only.\n"  
  
    f"Now generate {n} subset questions for the following question:\n"  
    f"Question: {self.question}\n"  
    f"Please only return the {n} subset questions separated by newlines, without any explanations or additional text.")
```

### QMR-4: Error-Type Reflection
**1. Equivalent**
``` python
metamorphic_question = f"{self.question}\n" + \  
f"### Important rules: 1.After generating the query, you must verify whether the query introduces a {hallu_type_name} hallucination." + \  
"2. If the query introduces such error, fix it automatically." + \  
"3. The final output must only be the corrected query, with no explanation.\n"
```