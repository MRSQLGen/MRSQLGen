To enable targeted prompt transformation, we construct a structured Hallucination Knowledge Base (HKB) that captures empirical hallucination patterns in LLM-generated SQL queries. The HKB serves as the foundation for selecting appropriate metamorphic rules, linking common failure modes with prompt-level transformation strategies. 

The construction of the HKB is grounded in our annotated hallucination corpus. Each entry (x, q, H ) consists of three elements: (1) the natural language prompt x, (2) the corresponding LLMgenerated SQL query q, and (3) a set of hallucination types H identified in q. To ensure consistent comparison and retrieval, both the prompt x and query q are preprocessed through a standardization pipeline that normalizes surface-level variations while preserving semantic structure. We detail this standardization process in Section 5.2. The hallucination types are based on a taxonomy derived from our empirical analysis. Since hallucinations often co-occur, H is represented as a set rather than a single label. These features allow us to embed the HKB into a searchable latent space, supporting similarity-based retrieval of past failure cases during inference. In later stages, this knowledge base allows us to retrieve the most relevant hallucination types for a new prompt and apply corresponding metamorphic transformation rules tailored to those hallucination risks.

#  The scale of HKB
10,181

Spider is a cross-domain dataset comprising 10,181 natural language questions over 200 databases. In our empirical study (Section 4), we used half of it to build the HKB. So, HKB contains 5,000 annotated cases.

* Number of cases: 5000, 
* Storage space: 
* Storage format: 
* Hallucination types: 


{  
    "index": 0,  
    "node_type": {  
        "Operator": true,  
        "LIMIT": false,  
        "Join": false,  
        "ColumnNameOPLiteral": true,  
        "Column": true,  
        "ConditionExpression": true,  
        "AggregationFunction": true,  
        "Distinct": false,  
        "OrderBy": false,  
        "GroupBy": false  
    },  
    "question": "How many [NOUN] of the [NOUN] are older than [NUMBER] ?",  
    "query": "SELECT COUNT(*) FROM [TableName] WHERE [ColumnName] > [Integer]"  
},