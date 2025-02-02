CREATE TABLE inventario (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL UNIQUE,
    cantidad INT DEFAULT 0,
    precio DECIMAL(10, 2)
);

CREATE TABLE ventas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    total DECIMAL(10, 2),
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE productos_vendidos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    venta_id INT,
    producto VARCHAR(255),
    cantidad INT,
    precio DECIMAL(10, 2),
    FOREIGN KEY (venta_id) REFERENCES ventas(id)
);

INSERT INTO inventario (nombre, cantidad, precio) VALUES 
('Arroz', 100, 1.20),
('Azúcar', 50, 0.85),
('Aceite', 30, 2.50);
