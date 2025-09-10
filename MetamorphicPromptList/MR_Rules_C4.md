## C4: Violating Value Specification
### QMR-1: Intent Perturbation & Reversal
**1. Equivalent**

```python
prompt = (  
    f"Generate {n} simple English questions that are semantically equivalent to the following question but different from each other, "    f"and whose corresponding SQL queries would also be logically equivalent. "    f"You must achieve this by modifying only the wording of the value descriptions without introducing unrelated values or numbers.\n\n"  
  
    f"Example 1:\n"  
    f"Original question: Show all female customers.\n"  
    f"Equivalent question: Get all customers who are women.\n"  
  
    f"Example 2:\n"  
    f"Original question: Find users who signed up after January 2020.\n"  
    f"Equivalent question: Find users who signed up after 2020-01.\n"  
  
    f"Example 3:\n"  
    f"Original question: Find videos longer than 10 minutes.\n"  
    f"Equivalent question: Retrieve all videos with a duration longer than 00:10:00.\n"  
  
    f"Now generate {n} equivalent questions for the following question:\n"  
    f"Question: {self.question}\n"  
    f"Do not include any explanations. Just return the {n} equivalent questions, each separated by a newline.")
```

**2. Superset**

```python
prompt = (  
    f"Generate {n} simple English questions whose corresponding SQL queries would return a superset of the original query's result set, "    f"i.e., the generated query should include all results of the original query and potentially more. "    f"You must achieve this by relaxing or broadening the value descriptions, without introducing unrelated values or numbers.\n"  
    f"thus expanding the scope of the returned data, without changing other parts of the question.\n\n"  
  
    f"Example 1:\n"  
    f"Original question: Show all female customers.\n"  
    f"Superset question: Display all customers who are female or male.\n"  
  
    f"Example 2:\n"  
    f"Original question: Find users who signed up after January 2020.\n"  
    f"Superset question: Find users who signed up after January 2019.\n"  
  
    f"Example 3:\n"  
    f"Original question: Find videos longer than 10 minutes.\n"  
    f"Superset question: Find videos longer than 5 minutes.\n"  
  
    f"Now generate {n} superset questions for the following question:\n"  
    f"Question: {self.question}\n"  
    f"Please only return the {n} superset questions separated by newlines, without any explanations or additional text.")
```

**3. Subset**

```python
prompt = (  
    f"Generate {n} simple English questions whose corresponding SQL queries would return a subset of the original query's result set, "    f"i.e., the generated query should include only a portion of the result of the original query. "    f"You must achieve this by tightening or narrowing the value descriptions, without introducing unrelated values or numbers.\n\n"  
    f"thus narrowing the scope of the returned data, without changing other parts of the question.\n\n"  
  
    f"Example 1:\n"  
    f"Original question: Show all female customers.\n"  
    f"Subset question: Retrieve all female customers who are over 30 years old.\n"  
  
    f"Example 2:\n"  
    f"Original question: Find users who signed up after January 2020.\n"  
    f"Subset question: Find users who signed up after February 2020.\n"  
  
    f"Example 3:\n"  
    f"Original question: Find videos longer than 10 minutes.\n"  
    f"Subset question: Find videos longer than 15 minutes.\n"  
  
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