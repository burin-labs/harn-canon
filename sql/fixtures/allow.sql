SELECT id,name FROM users;

SELECT o.id,u.name
FROM orders o 
INNER JOIN users u ON o.user_id = u.user_id
