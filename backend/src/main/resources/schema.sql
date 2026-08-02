DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS addresses;
DROP TABLE IF EXISTS cart_items;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(20) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    email VARCHAR(100) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE products (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    stock INT NOT NULL DEFAULT 0,
    description TEXT,
    image_url VARCHAR(500),
    images TEXT COMMENT 'JSON array of image URLs',
    version INT NOT NULL DEFAULT 0 COMMENT 'optimistic lock',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE cart_items (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    product_id BIGINT NOT NULL,
    quantity INT NOT NULL DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_user_product (user_id, product_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE addresses (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    receiver_name VARCHAR(20) NOT NULL,
    phone VARCHAR(11) NOT NULL,
    province VARCHAR(50) NOT NULL,
    city VARCHAR(50) NOT NULL,
    district VARCHAR(50) NOT NULL,
    detail VARCHAR(100) NOT NULL,
    is_default TINYINT(1) DEFAULT 0,
    deleted TINYINT(1) DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE orders (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    order_no VARCHAR(20) NOT NULL UNIQUE,
    user_id BIGINT NOT NULL,
    status ENUM('PENDING','PAID','SHIPPED','RECEIVED','CANCELLED','REFUNDED') NOT NULL DEFAULT 'PENDING',
    total_amount DECIMAL(10,2) NOT NULL,
    address_snapshot TEXT COMMENT 'JSON snapshot of address at order time',
    remark VARCHAR(200),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE order_items (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    order_id BIGINT NOT NULL,
    product_id BIGINT NOT NULL,
    product_name VARCHAR(200) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    quantity INT NOT NULL,
    subtotal DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Seed test products
INSERT INTO products (name, price, stock, description, image_url) VALUES
('智能手机 Pro Max', 5999.00, 100, '旗舰智能手机，高性能处理器', 'https://picsum.photos/400/300?random=1'),
('无线蓝牙耳机', 299.00, 500, '主动降噪无线蓝牙耳机', 'https://picsum.photos/400/300?random=2'),
('轻薄笔记本电脑', 4999.00, 50, '14英寸轻薄本，适合办公学习', 'https://picsum.photos/400/300?random=3'),
('机械键盘 RGB', 399.00, 200, 'Cherry轴体机械键盘，RGB背光', 'https://picsum.photos/400/300?random=4'),
('USB-C充电器 65W', 129.00, 0, 'GaN氮化镓快充充电器（库存已售罄）', 'https://picsum.photos/400/300?random=5');

-- Seed test user (password: Test@123456 BCrypt encoded)
INSERT INTO users (username, password, email) VALUES
('testuser1', '$2b$10$OxwqutE.YSmA0VQqqHK5QOqKVTcQNr7J9JA8y9z8fAtssvnauekg.', 'test@example.com');
-- Password: Test@123456 (BCrypt hash generated via Python bcrypt, rounds=10)
