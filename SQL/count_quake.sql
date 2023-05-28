SELECT count(*)
FROM properties
WHERE time::date BETWEEN '{start}' AND '{end}'
    AND mag > 5
