-- Create the database
CREATE DATABASE IF NOT EXISTS home_services;
USE home_services;

-- Create Users table
CREATE TABLE IF NOT EXISTS Users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create Services table
CREATE TABLE IF NOT EXISTS Services (
    service_id INT AUTO_INCREMENT PRIMARY KEY,
    service_name VARCHAR(100) NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create Orders table
CREATE TABLE IF NOT EXISTS Orders (
    order_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    service_id INT NOT NULL,
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (service_id) REFERENCES Services(service_id) ON DELETE CASCADE
);

-- Create OrderDetails table
CREATE TABLE IF NOT EXISTS OrderDetails (
    order_id INT PRIMARY KEY,
    extra_info TEXT,
    FOREIGN KEY (order_id) REFERENCES Orders(order_id) ON DELETE CASCADE
);

-- Create OrderDeletionLog table
CREATE TABLE IF NOT EXISTS OrderDeletionLog (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    deletion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create trigger for logging order deletions
DELIMITER //

CREATE TRIGGER log_order_deletion
AFTER DELETE ON Orders
FOR EACH ROW
BEGIN
    INSERT INTO OrderDeletionLog (order_id) VALUES (OLD.order_id);
END//

-- Stored procedure for user registration
CREATE PROCEDURE RegisterUser(
    IN p_name VARCHAR(100),
    IN p_email VARCHAR(100),
    IN p_password VARCHAR(255)
)
BEGIN
    INSERT INTO Users (name, email, password)
    VALUES (p_name, p_email, p_password);
END//

-- Stored procedure for user login
CREATE PROCEDURE LoginUser(
    IN p_email VARCHAR(100),
    IN p_password VARCHAR(255)
)
BEGIN
    SELECT * FROM Users 
    WHERE email = p_email AND password = p_password;
END//

-- Stored procedure to get all services
CREATE PROCEDURE GetServices()
BEGIN
    SELECT * FROM Services;
END//

-- Stored procedure to place an order
CREATE PROCEDURE PlaceOrder(
    IN p_user_id INT,
    IN p_service_id INT,
    IN p_extra_info TEXT
)
BEGIN
    DECLARE new_order_id INT;
    
    START TRANSACTION;
    
    INSERT INTO Orders (user_id, service_id)
    VALUES (p_user_id, p_service_id);
    
    SET new_order_id = LAST_INSERT_ID();
    
    IF p_extra_info IS NOT NULL THEN
        INSERT INTO OrderDetails (order_id, extra_info)
        VALUES (new_order_id, p_extra_info);
    END IF;
    
    COMMIT;
    
    SELECT new_order_id AS order_id;
END//

-- Stored procedure to view order history with total spent
CREATE PROCEDURE ViewOrderHistory(
    IN p_user_id INT
)
BEGIN
    SELECT 
        o.order_id,
        s.service_name,
        o.order_date,
        od.extra_info,
        s.price,
        (SELECT SUM(s2.price) 
         FROM Orders o2 
         JOIN Services s2 ON o2.service_id = s2.service_id 
         WHERE o2.user_id = p_user_id) AS total_spent
    FROM Orders o
    JOIN Services s ON o.service_id = s.service_id
    LEFT JOIN OrderDetails od ON o.order_id = od.order_id
    WHERE o.user_id = p_user_id;
END//


-- Stored procedure to update order
CREATE PROCEDURE UpdateOrder(
    IN p_order_id INT,
    IN p_extra_info TEXT
)
BEGIN
    UPDATE OrderDetails
    SET extra_info = p_extra_info
    WHERE order_id = p_order_id;
END//

-- Stored procedure to delete order
CREATE PROCEDURE DeleteOrder(
    IN p_order_id INT
)
BEGIN
    START TRANSACTION;
    
    DELETE FROM OrderDetails
    WHERE order_id = p_order_id;
    
    DELETE FROM Orders
    WHERE order_id = p_order_id;
    
    COMMIT;
END//

DELIMITER ;