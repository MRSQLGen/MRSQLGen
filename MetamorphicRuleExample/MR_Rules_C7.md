## C7: Aggregation Function Misuse
### QMR-2: Logical Decomposition
|     | Original question                          | Equivalent question                                                                                                                       |
| --- | ------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Calculate total quantity of ordered items. | Calculate total quantity of ordered items. CoT Steps:Retrieve all orders. Extract the field order_quantity.Apply SUM over order_quantity. |
| 2   | What is the average price of products.     | What is the average price of products. CoT Steps:Retrieve all products. Extract the field price.Apply AVG over price.                     |
| 3   | Find total sales amount for each region.   | Find total sales amount for each region. CoT Steps:Retrieve all orders. Group orders by region. For each region, apply SUM over sales.    |
### QMR-4: Error-Type Reflection
**1. Equivalent**
``` python
metamorphic_question = f"{self.question}\n" + \  
f"### Important rules: 1.After generating the query, you must verify whether the query introduces a {hallu_type_name} hallucination." + \  
"2. If the query introduces such error, fix it automatically." + \  
"3. The final output must only be the corrected query, with no explanation.\n"
```