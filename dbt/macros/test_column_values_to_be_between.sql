{% test column_values_to_be_between(model, column_name, min_value=none, max_value=none) %}

select *
from {{ model }}
where {{ column_name }} < {{ min_value }}
{% if max_value is not none %}
   or {{ column_name }} > {{ max_value }}
{% endif %}

{% endtest %}
