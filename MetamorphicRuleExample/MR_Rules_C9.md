## C9: OrderBy Misuse
### QMR-3: Constraint Explicitization
|     | Original question                             | Equivalent question                                                                                                                                                                                              |
| --- | --------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | List products by price from high to low.      | List products by price from high to low. Explicit constraints about OrderBy: List all products ordered by price in descending order, so that the most expensive products appear first.                           |
| 2   | List the top 10 students by GPA.              | List the top 10 students by GPA. Explicit constraints about OrderBy: List the 10 students with the highest GPA, ordered by GPA in descending order, so the top students appear first.                            |
| 3   | Show products ordered by category then price. | Show products ordered by category then price. Explicit constraints about OrderBy: List all products ordered first by category in ascending order, and within each category ordered by price in descending order. |
### QMR-4: Error-Type Reflection
**1. Equivalent**
``` python
metamorphic_question = f"{self.question}\n" + \  
f"### Important rules: 1.After generating the query, you must verify whether the query introduces a {hallu_type_name} hallucination." + \  
"2. If the query introduces such error, fix it automatically." + \  
"3. The final output must only be the corrected query, with no explanation.\n"
```