import streamlit as st
import pandas as pd

from db_function import (
    connect_to_db,
    get_basic_info,
    get_additional_tables,
    get_categories,
    get_suppliers,
    add_new_manual_id,
    get_all_products,
    get_product_history,
    place_reorder,
    get_pending_reorders,
    mark_reorder_as_received,
)


# ─────────────────────────────────────────────
# DB Connection (cached so it doesn't reconnect
# on every Streamlit rerun)
# ─────────────────────────────────────────────
@st.cache_resource
def get_connection():
    return connect_to_db()


db = get_connection()
cursor = db.cursor(dictionary=True)

# ─────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────
st.sidebar.title("Inventory Management Dashboard")
options = st.sidebar.radio("Select Option:", ["Basic Information", "Operational Task"])

# ─────────────────────────────────────────────
# Main Title
# ─────────────────────────────────────────────
st.title("Inventory and Supply Chain Dashboard")


# ═════════════════════════════════════════════
# BASIC INFORMATION PAGE
# ═════════════════════════════════════════════
if options == "Basic Information":
    st.header("Basic Metrics")

    # Fetch basic info from DB
    basic_info = get_basic_info(cursor)
    keys = list(basic_info.keys())

    # Row 1 – first 3 metrics
    cols = st.columns(3)
    for i in range(3):
        cols[i].metric(label=keys[i], value=basic_info[keys[i]])

    # Row 2 – next 3 metrics
    cols = st.columns(3)
    for i in range(3, 6):
        cols[i - 3].metric(label=keys[i], value=basic_info[keys[i]])

    st.divider()

    # Detailed tables
    tables = get_additional_tables(cursor)
    for label, data in tables.items():
        st.header(label)
        df = pd.DataFrame(data)
        st.dataframe(df)
        st.divider()


# ═════════════════════════════════════════════
# OPERATIONAL TASKS PAGE
# ═════════════════════════════════════════════
elif options == "Operational Task":
    st.header("Operational Tasks")
    selected_task = st.selectbox(
        "Choose a Task",
        ["Add New Product", "Product History", "Place Reorder", "Receive Reorder"],
    )

    # ──────────────────────────────────────────
    # 1. ADD NEW PRODUCT
    # ──────────────────────────────────────────
    if selected_task == "Add New Product":
        st.header("Add New Product")

        categories = get_categories(cursor)
        supplier = get_suppliers(cursor)

        with st.form("Add_Product_Form"):
            product_name     = st.text_input("Enter Product Name")
            product_category = st.selectbox("Category", categories)
            product_price    = st.number_input("Enter Product Price", min_value=0.00)
            product_stock    = st.number_input("Enter Stock Quantity", min_value=0, step=1)
            product_level    = st.number_input("Reorder Level", min_value=0, step=1)

            supplier_ids  = [s["supplier_id"]   for s in supplier]
            supplier_name = [s["supplier_name"] for s in supplier]
            supplier_id   = st.selectbox(
                "Select Supplier",
                options=supplier_ids,
                format_func=lambda x: supplier_name[supplier_ids.index(x)],
            )

            submitted = st.form_submit_button("Add Product")

            if submitted:
                if not product_name:
                    st.error("Please enter the Product Name.")
                else:
                    try:
                        add_new_manual_id(
                            cursor,
                            db,
                            product_name,
                            product_category,
                            product_price,
                            product_stock,
                            product_level,
                            supplier_id,
                        )
                        # FIX: added f-prefix so variable is interpolated
                        st.success(f"Product '{product_name}' added successfully!")
                    except Exception as e:
                        # FIX: added f-prefix so exception is shown
                        st.error(f"Error adding the product: {e}")

    # ──────────────────────────────────────────
    # 2. PRODUCT HISTORY
    # ──────────────────────────────────────────
    # FIX: changed "if" → "elif" to avoid evaluating all blocks every run
    elif selected_task == "Product History":
        st.header("Product Inventory History")

        products      = get_all_products(cursor)
        product_names = [p["product_name"] for p in products]
        product_ids   = [p["product_id"]   for p in products]

        selected_product_name = st.selectbox("Select a Product", options=product_names)

        if selected_product_name:
            selected_product_id = product_ids[product_names.index(selected_product_name)]
            history_data = get_product_history(cursor, selected_product_id)

            if history_data:
                df = pd.DataFrame(history_data)
                st.dataframe(df)
            else:
                st.info("No history found for the selected product.")

    # ──────────────────────────────────────────
    # 3. PLACE REORDER
    # ──────────────────────────────────────────
    # FIX: changed "if" → "elif"
    elif selected_task == "Place Reorder":
        st.header("Place Reorder")

        products      = get_all_products(cursor)
        product_names = [p["product_name"] for p in products]
        product_ids   = [p["product_id"]   for p in products]

        selected_product_name = st.selectbox("Select a Product", options=product_names)
        reorder_qty = st.number_input("Reorder Quantity", min_value=0, step=1)

        # FIX: button label typo fixed ("Placed" → "Place")
        if st.button("Place Reorder"):
            if not selected_product_name:
                st.error("Please select a product.")
            # FIX: changed < 0 → <= 0 so zero-quantity orders are also blocked
            elif reorder_qty <= 0:
                st.error("Reorder quantity must be greater than 0.")
            else:
                selected_product_id = product_ids[product_names.index(selected_product_name)]
                try:
                    place_reorder(cursor, db, selected_product_id, reorder_qty)
                    st.success(
                        f"Order placed for '{selected_product_name}' "
                        f"with quantity {reorder_qty}."
                    )
                except Exception as e:
                    st.error(f"Error placing reorder: {e}")

    # ──────────────────────────────────────────
    # 4. RECEIVE REORDER
    # ──────────────────────────────────────────
    # FIX: changed "if" → "elif"
    elif selected_task == "Receive Reorder":
        st.header("Mark Reorder as Received")

        pending_reorders = get_pending_reorders(cursor)

        if not pending_reorders:
            st.info("No pending orders to receive.")
        else:
            # FIX: removed unused reorder_ids list
            reorder_map = {
                f"ID {r['reorder_id']} - {r['product_name']}": r["reorder_id"]
                for r in pending_reorders
            }
            reorder_labels = list(reorder_map.keys())

            selected_label = st.selectbox(
                "Select Reorder to Mark as Received", options=reorder_labels
            )

            if selected_label:
                selected_reorder_id = reorder_map[selected_label]

                if st.button("Mark as Received"):
                    try:
                        mark_reorder_as_received(cursor, db, selected_reorder_id)
                        st.success(f"Reorder {selected_reorder_id} marked as received.")
                    except Exception as e:
                        st.error(f"Error marking as received: {e}")