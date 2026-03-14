{{
  config(
    materialized='{{ materialization }}',
    tags=['{{ tag }}'],
  )
}}

-- {{ model_description }}

WITH source AS (
    SELECT *
    FROM {{ source_ref }}
)

SELECT
    *
FROM source
