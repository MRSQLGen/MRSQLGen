## C10: GroupBy Misuse
### QMR-2: Logical Decomposition
|     | Original question                   | Equivalent question                                                                                                                                   |
| --- | ----------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Show total sales for each region.   | Show total sales for each region. CoT Steps:Retrieve all orders. Group orders by region. For each region, apply SUM over sales.                       |
| 2   | Count employees in each department. | Count employees in each department. CoT Steps:Retrieve all employees. Group employees by department. For each department, apply COUNT over employees. |
| 3   | Show the number of orders per day.  | Show the number of orders per day. CoT Steps:Retrieve all orders. Group orders by order_date. For each day, apply COUNT over order_id.                |
### QMR-4: Error-Type Reflection
**1. Equivalent**
``` python
metamorphic_question = f"{self.question}\n" + \  
f"### Important rules: 1.After generating the query, you must verify whether the query introduces a {hallu_type_name} hallucination." + \  
"2. If the query introduces such error, fix it automatically." + \  
"3. The final output must only be the corrected query, with no explanation.\n"
```