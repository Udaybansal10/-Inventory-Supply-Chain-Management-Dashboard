import mysql.connector


# creating a function out of it
def connect_to_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="new_schema"
    )


def get_basic_info(cursor):
    queries = {
        "Total Suppliers": "select count(*) as Total_Supplier from suppliers",

        "Total products": "select count(*) as total_products from products",

        "Total Category Dealing": "select count(distinct category) as total_categories from products",

        "Total sales made in last 3 months (quantity * price)": """
        select round(sum(abs(se.change_quantity) * p.price), 2) as Total_sales_value_last_3_months
        from stock_entries se
        join products p
        on p.product_id = se.product_id
        where se.change_type = "Sale"
        and se.entry_date >=
        (select date_sub(max(entry_date), interval 3 month) from stock_entries)
        """,

        "Total restock made in last 3 months (quantity * price)": """
        select round(sum(abs(se.change_quantity) * p.price), 2) as Total_sales_value_last_3_months
        from stock_entries se
        join products p
        on p.product_id = se.product_id
        where se.change_type = "Restock"
        and se.entry_date >=
        (select date_sub(max(entry_date), interval 3 month) from stock_entries)
        """,

        "Below Reorder and No Pending Reorders": """
        select count(*)
        from products p
        where p.stock_quantity < p.reorder_level
        and product_id not in
        (select distinct product_id
        from reorders
        where status = "Pending")
        """

    }

    result = {}
    for label, query in queries.items():
        cursor.execute(query)
        row = cursor.fetchone()
        result[label] = list(row.values())[0]

    return result


def get_additional_tables(cursor):

    queries  = {
    "Suppliers and their contact details" : "select supplier_name, contact_name, email, phone from suppliers",

    "Product with their suppliers and current stock" : """ select 
    p.product_name,
    s.supplier_name,
    p.stock_quantity,
    p.reorder_level
    from products p 
    join suppliers s
    on s.supplier_id = p.supplier_id
    order by p.product_name ASC
    """,

    "Product needing Reorder" : """select 
    product_id,
    product_name,
    stock_quantity,
    reorder_level
    from products 
    where stock_quantity < reorder_level
    """
    }

    table = {}
    for label, query in queries.items():
        cursor.execute(query)
        table[label] = cursor.fetchall()
    return table

def add_new_manual_id(cursor, db, p_name, p_category, p_price, p_stock, p_reorder, p_supplier):
    procedure_call = "call AddNewproductManualID(%s, %s,%s,%s,%s,%s)"
    params = (p_name, p_category, p_price, p_stock, p_reorder, p_supplier)
    cursor.execute(procedure_call, params)
    db.commit()

def get_categories(cursor):
        cursor.execute("select Distinct category from products order by category asc")
        rows = cursor.fetchall()
        return [row["category"] for row in rows]

def get_suppliers(cursor):
        cursor.execute("select supplier_id, supplier_name from suppliers order by supplier_name asc")
        return cursor.fetchall()

def get_all_products(cursor):
    cursor.execute("select product_id, product_name from products order by product_name")
    return cursor.fetchall()

def get_product_history(cursor, product_id):
    query = "select * from product_inventory_history where product_id = %s order by activity_date desc"
    cursor.execute(query, (product_id,))
    return cursor.fetchall()

def place_reorder(cursor, db, product_id, reorder_quantity):
    query = """
            insert into reorders (reorder_id, product_id, reorder_quantity, reorder_date, status)
            select
                max(reorder_id) +1,
                %s,
                %s,
                curdate(),
                "Ordered"
                from reorders   
            """
    cursor.execute(query, (product_id, reorder_quantity))
    db.commit()

def get_pending_reorders(cursor):
     query = """Select r.reorder_id, p.product_name
                from reorders r join products p 
                on p.product_id = r.product_id
             """
     cursor.execute(query)
     return cursor.fetchall()


def mark_reorder_as_received(cursor, db, reorder_id):
    cursor.callproc("MarkReorderAsReceived", [reorder_id])
    db.commit()