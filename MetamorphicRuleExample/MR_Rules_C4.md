## C4: Violating Value Specification
### QMR-1: Intent Perturbation & Reversal
|     | Original question                            | Equivalent question                                       | Superset question                                                                                         | Subset question                                          |
| --- | -------------------------------------------- | --------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- | -------------------------------------------------------- |
| 1   | Show all female customers.                   | Get all customers who are women.                          | Display all customers who are female or male. Retrieve all female customers who are over 30 years old. d. | Retrieve all female customers who are over 30 years old. |
| 2   | Find users who signed up after January 2020. | Find users who signed up after 2020-01.                   | Find users who signed up after January 2019.                                                              | Find users who signed up after February 2020.            |
| 3   | Find videos longer than 10 minutes.          | Retrieve all videos with a duration longer than 00:10:00. | Find videos longer than 5 minutes.                                                                        | Find videos longer than 15 minutes.                      |
### QMR-4: Error-Type Reflection
**1. Equivalent**
``` python
metamorphic_question = f"{self.question}\n" + \  
f"### Important rules: 1.After generating the query, you must verify whether the query introduces a {hallu_type_name} hallucination." + \  
"2. If the query introduces such error, fix it automatically." + \  
"3. The final output must only be the corrected query, with no explanation.\n"
```