📦 Inventory & Supply Chain Management Dashboard
An interactive Streamlit-based dashboard connected to a MySQL database that enables real-time inventory monitoring, stock health analysis, supplier management, and automated reorder workflows.

📌 Project Overview
The Inventory & Supply Chain Management Dashboard provides a data-driven interface for managing product inventory across multiple suppliers and categories.
It helps answer critical operational questions such as:

How many products are below reorder level with no pending orders?
What is the total sales and restock value in the last 3 months?
Which products are fast-moving vs. dead stock?
What is the full activity history for a given product?
How can we place and receive reorders seamlessly?

The dashboard converts raw transactional data into actionable business intelligence that supports smarter supply chain decisions.

🛠 Tech Stack
ToolPurpose🐍 PythonCore application logic🌐 StreamlitInteractive dashboard UI🗄️ MySQLRelational database backend🔗 mysql-connector-pythonDatabase connectivity🐼 PandasData manipulation and display⚙️ Stored ProceduresAutomated transactional operations👁️ SQL ViewsProduct inventory history tracking

📂 Project Structure
inventory-dashboard/
│
├── app.py               # Main Streamlit application
├── db_function.py       # All database query functions
├── sql.sql              # Full SQL schema, views, and stored procedures
└── README.md            # Project documentation

📊 Dashboard Features
🔵 Basic Information Page
Displays 6 real-time KPI metrics:

✅ Total Suppliers
✅ Total Products
✅ Total Categories
✅ Total Sales Value (last 3 months)
✅ Total Restock Value (last 3 months)
✅ Products below reorder level with no pending reorder

Also includes detailed tables for:

Supplier contact details
Products with supplier mapping and current stock
Products needing immediate reorder


🟠 Operational Tasks Page
Four fully functional operational workflows:
➕ 1. Add New Product

Input product name, category, price, stock quantity, reorder level, and supplier
Triggers AddNewProductManualID stored procedure
Automatically creates shipment and stock entry records in a single transaction

📋 2. Product History

Select any product from a dropdown
Displays full activity history from the product_inventory_history view
Covers stock entries (sales, restocks) and supplier shipments

🔁 3. Place Reorder

Select a product and specify reorder quantity
Inserts a new reorder record with Ordered status
Validates that quantity must be greater than 0

✅ 4. Receive Reorder

Lists all pending reorders
Marks selected reorder as Received via MarkReorderAsReceived stored procedure
Automatically updates stock quantity, creates shipment and stock entry records


🗄️ Database Design

Tables
Table : products
Description : Product master data (name, category, price, stock, reorder level, supplier)

Table : suppliers
Description : Supplier details (name, contact, email, phone)

Table : stock_entries
Description : All stock movements (sales, restocks)

Table : shipments
Description : Supplier delivery records





📈 Key SQL Analytical Queries

Dead Stock Detection — Products with no stock movement in the last 3 months
Fast Moving Products — Top 10 products by total sales quantity
Sales & Restock Value — Revenue and procurement cost analysis over rolling 3-month window
Stock Health Check — Products below reorder level with no active pending reorder


⚙️ Setup & Installation
1. Clone the Repository
bashgit clone https://github.com/yourusername/inventory-dashboard.git
cd inventory-dashboard
2. Install Dependencies
bashpip install streamlit pandas mysql-connector-python
3. Configure Database Connection
In db_function.py, update your MySQL credentials:
pythondef connect_to_db():
    return mysql.connector.connect(
        host="localhost",
        user="your_username",
        password="your_password",
        database="new_schema"
    )
4. Set Up the Database
Run the SQL file in your MySQL client:
sqlSOURCE sql.sql;
5. Run the App
bashstreamlit run app.py

💼 Business Impact
This dashboard supports multiple stakeholders:
StakeholderBenefit📦 Inventory ManagersReal-time stock health monitoring and reorder alerts🚚 Supply Chain TeamsEnd-to-end reorder placement and receipt tracking📊 Data AnalystsKPI tracking, sales trends, and supplier performance💼 Business LeadersData-driven decisions on procurement and stock strategy
