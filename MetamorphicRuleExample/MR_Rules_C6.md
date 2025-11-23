## C6: Condition Logic Hallucination
### QMR-1: Intent Perturbation & Reversal
|     | Original question                                        | Equivalent question                                                     | Superset question                                       | Subset question                                            |
| --- | -------------------------------------------------------- | ----------------------------------------------------------------------- | ------------------------------------------------------- | ---------------------------------------------------------- |
| 1   | Find users aged between 18 and 25 and are female.        | Show all female users with age in the range of 18 to 25.                | Show users who are female or aged between 18 and 25.    | Show users who are female and aged between 20 and 22.      |
| 2   | Show users with income over 5000 and living in NY or LA. | Display all users earning more than 5000 whose city is either NY or LA. | Show users with income over 5000 or living in NY or LA. | Display users with income over 8000 and living only in NY. |
### QMR-2: Logical Decomposition
|     | Original question                                                                         | Equivalent question                                                                                                                                                                               |
| --- | ----------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Find employees with salary greater than 5000 and less than 10000.                         | Find employees with salary greater than 5000 and less than 10000. CoT Steps:Filter employees with salary > 5000. Filter employees with salary < 10000.                                            |
| 2   | Retrieve students who are either from New York or from Los Angeles and are older than 18. | Retrieve students who are either from New York or from Los Angeles and are older than 18. CoT Steps:Filter students with city = 'New York' OR city = 'Los Angeles'.Filter students with age > 18. |
| 3   | Show products priced below 100 or above 1000, but only those in stock.                    | Show products priced below 100 or above 1000, but only those in stock. CoT Steps:Filter products with price < 100 OR price > 1000. Filter products with stock > 0.                                |
### QMR-3: Constraint Explicitization
|     | Original question                                      | Equivalent question                                                                                                                                                                                                             |
| --- | ------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Find users aged between 18 and 25 and are female.      | Find users aged between 18 and 25 and are female. Explicit constraints about Condition Expression: Find users whose age is greater than or equal to 18 and less than or equal to 25, and whose gender is explicitly female.     |
| 2   | Show employees whose salary is between 5000 and 10000. | Show employees whose salary is between 5000 and 10000. Explicit constraints about Condition Expression: Show employees whose salary is greater than or equal to 5000 and less than or equal to 10000, inclusive of both bounds. |
### QMR-4: Error-Type Reflection
**1. Equivalent**
``` python
metamorphic_question = f"{self.question}\n" + \  
f"### Important rules: 1.After generating the query, you must verify whether the query introduces a {hallu_type_name} hallucination." + \  
"2. If the query introduces such error, fix it automatically." + \  
"3. The final output must only be the corrected query, with no explanation.\n"
```