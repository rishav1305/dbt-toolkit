-- Singular test: {{ test_description }}
-- Returns rows that violate the assertion (0 rows = pass).

SELECT *
FROM {{ ref('{{ model_name }}') }}
WHERE {{ condition }}
