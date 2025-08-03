-- Create database and use it
DROP DATABASE IF EXISTS food_order_system;
CREATE DATABASE food_order_system;
USE food_order_system;

-- Create tables
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(15),
    address TEXT,
    city VARCHAR(50),
    state VARCHAR(50),
    pincode VARCHAR(10),
    gender ENUM('Male', 'Female', 'Other'),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);

CREATE TABLE items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    category_id INT,
    description TEXT,
    is_available BOOLEAN DEFAULT TRUE,
    rating FLOAT DEFAULT 0,
    calories INT,
    preparation_time INT COMMENT 'in minutes',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES categories(id)
);

CREATE TABLE cart (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    item_id INT,
    quantity INT DEFAULT 1,
    added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (item_id) REFERENCES items(id)
);

CREATE TABLE orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    total_amount DECIMAL(10,2),
    delivery_address TEXT,
    special_instructions TEXT,
    order_status ENUM('Pending', 'Confirmed', 'Preparing', 'Out for Delivery', 'Delivered', 'Cancelled') DEFAULT 'Pending',
    order_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE order_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT,
    item_id INT,
    quantity INT,
    price DECIMAL(10,2),
    item_name VARCHAR(100),
    item_category VARCHAR(50),
    FOREIGN KEY (order_id) REFERENCES orders(id),
    FOREIGN KEY (item_id) REFERENCES items(id)
);

CREATE TABLE payment (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT,
    method VARCHAR(50),
    status ENUM('Pending', 'Completed', 'Failed') DEFAULT 'Completed',
    transaction_id VARCHAR(100),
    paid_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders(id)
);

-- Insert sample data
INSERT INTO categories (name) VALUES 
('Appetizers'),
('Main Course'),
('Beverages'),
('Desserts'),
('Fast Food');

INSERT INTO items (name, price, category_id, description, rating, calories, preparation_time) VALUES 
('Chicken Wings', 299.00, 1, 'Spicy buffalo chicken wings with ranch dip', 4.5, 350, 15),
('Garlic Bread', 149.00, 1, 'Crispy bread with garlic butter and herbs', 4.2, 280, 10),
('Margherita Pizza', 399.00, 2, 'Classic pizza with tomato, mozzarella and basil', 4.6, 550, 20),
('Chicken Biryani', 449.00, 2, 'Aromatic basmati rice with spiced chicken', 4.8, 650, 35),
('Paneer Butter Masala', 329.00, 2, 'Rich and creamy paneer in tomato gravy', 4.4, 420, 25),
('Cola', 49.00, 3, 'Chilled cola drink', 4.0, 150, 2),
('Fresh Lime Water', 79.00, 3, 'Refreshing lime water with mint', 4.3, 20, 5),
('Chocolate Brownie', 199.00, 4, 'Warm chocolate brownie with vanilla ice cream', 4.7, 380, 12),
('Burger Combo', 249.00, 5, 'Chicken burger with fries and drink', 4.1, 720, 18),
('French Fries', 129.00, 5, 'Crispy golden french fries', 4.0, 320, 8);

INSERT INTO users (name, email, phone, gender, city, state) VALUES 
('Test User', 'test@example.com', '9876543210', 'Male', 'Mumbai', 'Maharashtra');

-- Add some cart items for testing
INSERT INTO cart (user_id, item_id, quantity) VALUES 
(1, 3, 1),
(1, 6, 2);