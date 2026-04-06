USE new_schema;

-- SECTION 1: MASTER DATA

-- 1. Total Suppliers
SELECT COUNT(*) AS total_suppliers
FROM suppliers;

-- 2. Total Products
SELECT COUNT(*) AS total_products
FROM products;

-- 3. Total Categories
SELECT COUNT(DISTINCT category) AS total_categories
FROM products;

-- 4. Suppliers and Their Contact Details
SELECT supplier_name, contact_name, email, phone
FROM suppliers;

-- 5. Products with Their Suppliers and Current Stock
SELECT
    p.product_name,
    s.supplier_name,
    p.stock_quantity,
    p.reorder_level
FROM products p
JOIN suppliers s ON s.supplier_id = p.supplier_id
ORDER BY p.product_name ASC;


-- ============================================================
-- SECTION 2: STOCK HEALTH
-- ============================================================

-- 6. Products Needing Reorder (below reorder level)
SELECT
    product_id,
    product_name,
    stock_quantity,
    reorder_level
FROM products
WHERE stock_quantity < reorder_level;


-- 7. Below Reorder Level with No Pending Reorder (action required)
SELECT COUNT(*) AS needs_reorder_no_pending
FROM products p
WHERE p.stock_quantity < p.reorder_level
AND product_id NOT IN (
    SELECT DISTINCT product_id
    FROM reorders
    WHERE status = 'Pending'
);


-- 8. Dead Stock Products (no movement in last 3 months) — count
SELECT COUNT(*) AS dead_stock_products
FROM (
    SELECT p.product_id
    FROM products p
    LEFT JOIN stock_entries s ON p.product_id = s.product_id
    GROUP BY p.product_id
    HAVING MAX(s.entry_date) < (
        SELECT DATE_SUB(MAX(entry_date), INTERVAL 3 MONTH)
        FROM stock_entries
    )
    OR MAX(s.entry_date) IS NULL
) dead_stock;


-- 9. Dead Stock Products — detail with days since last movement
SELECT
    p.product_id,
    p.product_name,
    MAX(s.entry_date) AS last_entry,
    DATEDIFF(
        (SELECT MAX(entry_date) FROM stock_entries),
        MAX(s.entry_date)
    ) AS days_since_last_movement
FROM products p
LEFT JOIN stock_entries s ON p.product_id = s.product_id
GROUP BY p.product_id, p.product_name
HAVING MAX(s.entry_date) < (
    SELECT DATE_SUB(MAX(entry_date), INTERVAL 3 MONTH)
    FROM stock_entries
)
OR MAX(s.entry_date) IS NULL;


-- 10. Top 10 Fast Moving Products
SELECT
    p.product_id,
    p.product_name,
    SUM(ABS(s.change_quantity)) AS total_sales
FROM products p
JOIN stock_entries s ON s.product_id = p.product_id
WHERE s.change_type = 'Sale'
GROUP BY p.product_id, p.product_name
ORDER BY total_sales DESC
LIMIT 10;


-- ============================================================
-- SECTION 3: SALES & RESTOCK ANALYTICS (last 3 months)
-- ============================================================

-- 11. Total Sales Value — Last 3 Months
SELECT
    ROUND(SUM(ABS(se.change_quantity) * p.price), 2) AS total_sales_value_last_3_months
FROM stock_entries se
JOIN products p ON p.product_id = se.product_id
WHERE se.change_type = 'Sale'
AND se.entry_date >= (
    SELECT DATE_SUB(MAX(entry_date), INTERVAL 3 MONTH)
    FROM stock_entries
);


-- 12. Total Restock Value — Last 3 Months
SELECT
    ROUND(SUM(ABS(se.change_quantity) * p.price), 2) AS total_restock_value_last_3_months
FROM stock_entries se
JOIN products p ON p.product_id = se.product_id
WHERE se.change_type = 'Restock'
AND se.entry_date >= (
    SELECT DATE_SUB(MAX(entry_date), INTERVAL 3 MONTH)
    FROM stock_entries
);


-- ============================================================
-- SECTION 4: PRODUCT HISTORY VIEW
-- ============================================================

-- 13. Create or Replace Product Inventory History View
CREATE OR REPLACE VIEW product_inventory_history AS
SELECT
    product_id,
    product_name,
    supplier_id,
    activity_date,
    activity_type,
    quantity,
    source,
    supplier_name
FROM (
    -- Stock entries (sales, restocks)
    SELECT
        p.product_id,
        p.product_name,
        p.supplier_id,
        se.entry_date      AS activity_date,
        se.change_type     AS activity_type,
        se.change_quantity AS quantity,
        'Stock Entry'      AS source,
        NULL               AS supplier_name
    FROM stock_entries se
    JOIN products p ON se.product_id = p.product_id

    UNION ALL

    -- Shipments (supplier deliveries)
    SELECT
        p.product_id,
        p.product_name,
        p.supplier_id,
        s.shipment_date        AS activity_date,
        'Shipment'             AS activity_type,
        s.quantity_received    AS quantity,
        'Supplier Delivery'    AS source,
        sup.supplier_name
    FROM shipments s
    JOIN products p   ON s.product_id   = p.product_id
    JOIN suppliers sup ON s.supplier_id = sup.supplier_id
) AS history;


-- ============================================================
-- SECTION 5: STORED PROCEDURES
-- ============================================================

-- 15. Procedure: Add a New Product
DELIMITER $$

CREATE PROCEDURE AddNewProductManualID(
    IN p_name     VARCHAR(255),
    IN p_category VARCHAR(100),
    IN p_price    DECIMAL(10,2),
    IN p_stock    INT,
    IN p_reorder  INT,
    IN p_supplier INT
)
BEGIN
    DECLARE new_product_id  INT;
    DECLARE new_shipment_id INT;
    DECLARE new_entry_id    INT;

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
    END;

    START TRANSACTION;

    SELECT IFNULL(MAX(product_id), 0) + 1  INTO new_product_id  FROM products;
    SELECT IFNULL(MAX(shipment_id), 0) + 1 INTO new_shipment_id FROM shipments;
    SELECT IFNULL(MAX(entry_id), 0) + 1    INTO new_entry_id    FROM stock_entries;

    INSERT INTO products (product_id, product_name, category, price, stock_quantity, reorder_level, supplier_id)
    VALUES (new_product_id, p_name, p_category, p_price, p_stock, p_reorder, p_supplier);

    INSERT INTO shipments (shipment_id, product_id, supplier_id, quantity_received, shipment_date)
    VALUES (new_shipment_id, new_product_id, p_supplier, p_stock, CURDATE());

    INSERT INTO stock_entries (entry_id, product_id, change_quantity, change_type, entry_date)
    VALUES (new_entry_id, new_product_id, p_stock, 'Restock', CURDATE());

    COMMIT;
END $$

DELIMITER ;


-- 16. Procedure: Mark Reorder as Received
DELIMITER $$

CREATE PROCEDURE MarkReorderAsReceived(IN in_reorder_id INT)
BEGIN
    DECLARE prod_id         INT;
    DECLARE qty             INT;
    DECLARE sup_id          INT;
    DECLARE new_shipment_id INT;
    DECLARE new_entry_id    INT;

    START TRANSACTION;

    SELECT product_id, reorder_quantity
    INTO prod_id, qty
    FROM reorders
    WHERE reorder_id = in_reorder_id;

    SELECT supplier_id INTO sup_id
    FROM products
    WHERE product_id = prod_id;

    UPDATE reorders
    SET status = 'Received'
    WHERE reorder_id = in_reorder_id;

    UPDATE products
    SET stock_quantity = stock_quantity + qty
    WHERE product_id = prod_id;

    SELECT MAX(shipment_id) + 1 INTO new_shipment_id FROM shipments;
    INSERT INTO shipments (shipment_id, product_id, supplier_id, quantity_received, shipment_date)
    VALUES (new_shipment_id, prod_id, sup_id, qty, CURDATE());

    SELECT MAX(entry_id) + 1 INTO new_entry_id FROM stock_entries;
    INSERT INTO stock_entries (entry_id, product_id, change_quantity, change_type, entry_date)
    VALUES (new_entry_id, prod_id, qty, 'Restock', CURDATE());

    COMMIT;
END $$

DELIMITER ;


