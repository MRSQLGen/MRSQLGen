## C2: Limit Error
### QMR-3: Constraint Explicitization
|     | Original question                          | Equivalent question                                                                                                                                                                                              |
| --- | ------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | List the top 10 best-selling products.     | List the top 10 best-selling products.Explicit constraints about LIMIT: Best-selling means the products with the highest total sales, ordered by sales in descending order.Return only the top 10.               |
| 2   | Show the top 5 students with highest GPA.  | Show the top 5 students with highest GPA. Explicit constraints about LIMIT: List students ranked by GPA in descending order, returning only the top 5.                                                           |
| 3   | List the 2nd page of results, 10 per page. | List the 2nd page of results, 10 per page. Explicit constraints about LIMIT: This means there exist 10 results per page.Retrieve results ordered in descending order, skip the first 10, and return the next 10. |
| 4   | Return the top 3 most expensive products.  | Return the top 3 most expensive products. Explicit constraints about LIMIT: Order products by price in descending order, returning only the top 3.                                                               |
### QMR-4: Error-Type Reflection
**1. Equivalent**
``` python
metamorphic_question = f"{self.question}\n" + \  
f"### Important rules: 1.After generating the query, you must verify whether the query introduces a {hallu_type_name} hallucination." + \  
"2. If the query introduces such error, fix it automatically." + \  
"3. The final output must only be the corrected query, with no explanation.\n"
```
