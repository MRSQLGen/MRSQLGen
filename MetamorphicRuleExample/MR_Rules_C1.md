## C1: Operator Misuse
### QMR-1: Intent Perturbation & Reversal
|     | Original question                                                                                      | Equivalent question                                                                     | Superset question                                                                                           | Subset question                                                                     |
| --- | ------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| 1   | Show each employee and their total compensation(positive number), calculated as `base_salary + bonus`. | Display all employees with `total_compensation = base_salary + bonus`(positive number). | Display all employees with `total_compensation = base_salary + bonus`, including employees with zero bonus. | Display employees with `total_compensation = base_salary + bonus` and bonus > 1000. |
| 2   | Find employees with a salary greater than 5000.                                                        | Retrieve all employees whose salary is strictly above five thousand dollars.            | Find employees with a salary greater than or equal to 4000.                                                 | Find employees with a salary greater than 6000.                                     |
| 3   | Find customers who are from New York or Los Angeles.                                                   | Retrieve customers whose city is either New York or Los Angeles.                        | Find customers who are from New York, Los Angeles, or Chicago.                                              | Find customers who are from New York only.                                          |
### QMR-4: Error-Type Reflection
**1. Equivalent**
``` python
metamorphic_question = f"{self.question}\n" + \  
f"### Important rules: 1.After generating the query, you must verify whether the query introduces a {hallu_type_name} hallucination." + \  
"2. If the query introduces such error, fix it automatically." + \  
"3. The final output must only be the corrected query, with no explanation.\n"
```