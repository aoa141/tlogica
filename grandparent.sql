WITH t_1_Parent AS (SELECT * FROM (

    SELECT
      'Alice' AS parent,
      'Bob' AS child
   UNION ALL

    SELECT
      'Bob' AS parent,
      'Carol' AS child

) AS UNUSED_TABLE_NAME  )
SELECT
  Parent.parent AS grandparent,
  t_0_Parent.child AS grandchild
FROM
  t_1_Parent AS Parent, t_1_Parent AS t_0_Parent
WHERE
  (t_0_Parent.parent = Parent.child);