## C8: Distinct Error
### QMR-3: Constraint Explicitization
|     | Original question                | Equivalent question                                                                                                                                                                    |
| --- | -------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | List all unique customer cities. | List all unique customer cities. Explicit constraints about DISTINCT: List all customer cities, but only return each city once without duplicates (i.e., enforce DISTINCT).            |
| 2   | Show all product categories.     | Show all product categories. Explicit constraints about DISTINCT: Show all product categories, allowing duplicates if multiple products share the same category (do not add DISTINCT). |
### QMR-4: Error-Type Reflection
**1. Equivalent**
``` python
metamorphic_question = f"{self.question}\n" + \  
f"### Important rules: 1.After generating the query, you must verify whether the query introduces a {hallu_type_name} hallucination." + \  
"2. If the query introduces such error, fix it automatically." + \  
"3. The final output must only be the corrected query, with no explanation.\n"
```