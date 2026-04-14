
import sqlite3

from typing import Optional

DB_PATH = "inventory.db"
LOW_STOCK_THRESHOLD = 10
PASSWORD = "mini_project"

def get_conn():
    conn = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():

    create_sql = """
    CREATE TABLE IF NOT EXISTS stores (
        id INTEGER PRIMARY KEY,
        code TEXT UNIQUE NOT NULL,
        name TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY,
        name TEXT UNIQUE NOT NULL,
        default_price REAL NOT NULL DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS store_inventory (
        id INTEGER PRIMARY KEY,
        store_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        qty INTEGER NOT NULL DEFAULT 0,
        price REAL NOT NULL DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(store_id, product_id),
        FOREIGN KEY(store_id) REFERENCES stores(id) ON DELETE CASCADE,
        FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS sales (
        id INTEGER PRIMARY KEY,
        store_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        unit_price REAL NOT NULL,
        total REAL NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(store_id) REFERENCES stores(id) ON DELETE CASCADE,
        FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS transfers (
        id INTEGER PRIMARY KEY,
        from_store_id INTEGER NOT NULL,
        to_store_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(from_store_id) REFERENCES stores(id) ON DELETE CASCADE,
        FOREIGN KEY(to_store_id) REFERENCES stores(id) ON DELETE CASCADE,
        FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY,
        action TEXT NOT NULL,
        details TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """
    conn = get_conn()
    cur = conn.cursor()
    cur.executescript(create_sql)
    conn.commit()


    cur.execute("SELECT COUNT(*) as c FROM stores")
    count = cur.fetchone()["c"]
    if count == 0:

        seed_initial_data(conn)

    conn.close()


def seed_initial_data(conn):

    cur = conn.cursor()
    # Insert stores A and B
    cur.execute("INSERT INTO stores (code, name) VALUES (?, ?)", ("A", "Store A"))
    cur.execute("INSERT INTO stores (code, name) VALUES (?, ?)", ("B", "Store B"))

    # Helper to add product if not exists and return product_id
    def get_or_create_product(name, default_price):
        cur.execute("SELECT id FROM products WHERE name = ?", (name,))
        row = cur.fetchone()
        if row:
            return row["id"]
        cur.execute("INSERT INTO products (name, default_price) VALUES (?, ?)", (name, default_price))
        return cur.lastrowid

    # Map your in-memory inventory.
    # inventory = {'A': {'pen': {'qty': 50, 'price': 10}, 'notebook': {'qty': 10, 'price': 40}},
    #              'B': {'pen': {'qty': 20, 'price': 10}, 'mouse': {'qty': 5, 'price': 150}}}
    # Seed products
    pen_id = get_or_create_product("pen", 10)
    notebook_id = get_or_create_product("notebook", 40)
    mouse_id = get_or_create_product("mouse", 150)

    # find store ids
    cur.execute("SELECT id FROM stores WHERE code = 'A'")
    store_a = cur.fetchone()["id"]
    cur.execute("SELECT id FROM stores WHERE code = 'B'")
    store_b = cur.fetchone()["id"]

    # Insert inventory rows (store_inventory)
    cur.execute("INSERT INTO store_inventory (store_id, product_id, qty, price) VALUES (?, ?, ?, ?)",
                (store_a, pen_id, 50, 10))
    cur.execute("INSERT INTO store_inventory (store_id, product_id, qty, price) VALUES (?, ?, ?, ?)",
                (store_a, notebook_id, 10, 40))
    cur.execute("INSERT INTO store_inventory (store_id, product_id, qty, price) VALUES (?, ?, ?, ?)",
                (store_b, pen_id, 20, 10))
    cur.execute("INSERT INTO store_inventory (store_id, product_id, qty, price) VALUES (?, ?, ?, ?)",
                (store_b, mouse_id, 5, 150))

    conn.commit()


# ---------------------------
# Small utility functions
# ---------------------------
def get_store_id(conn, code: str) -> Optional[int]:
    code = code.upper()
    cur = conn.execute("SELECT id FROM stores WHERE code = ?", (code,))
    row = cur.fetchone()
    return row["id"] if row else None


def get_product_id(conn, name: str) -> Optional[int]:
    name = name.lower()
    cur = conn.execute("SELECT id FROM products WHERE name = ?", (name,))
    row = cur.fetchone()
    return row["id"] if row else None


def create_product(conn, name: str, default_price: float) -> int:
    name = name.lower()
    cur = conn.execute("INSERT OR IGNORE INTO products (name, default_price) VALUES (?, ?)", (name, default_price))
    conn.commit()
    # fetch id
    return get_product_id(conn, name)


def get_inventory_row(conn, store_id: int, product_id: int):
    cur = conn.execute(
        "SELECT id, qty, price FROM store_inventory WHERE store_id = ? AND product_id = ?",
        (store_id, product_id)
    )
    return cur.fetchone()


def upsert_inventory(conn, store_id: int, product_id: int, qty: int, price: float):
    """
    Insert new inventory for store+product or update existing qty/price.
    """
    cur = conn.cursor()
    cur.execute("SELECT id FROM store_inventory WHERE store_id = ? AND product_id = ?", (store_id, product_id))
    row = cur.fetchone()
    if row:
        cur.execute("UPDATE store_inventory SET qty = qty + ?, price = ?, updated_at = CURRENT_TIMESTAMP WHERE store_id = ? AND product_id = ?",
                    (qty, price, store_id, product_id))
    else:
        cur.execute("INSERT INTO store_inventory (store_id, product_id, qty, price) VALUES (?, ?, ?, ?)",
                    (store_id, product_id, qty, price))
    conn.commit()


# ---------------------------
# CLI action functions (DB backed)
# These mirror your original functions but use SQLite under the hood.
# ---------------------------

def login():
    attempt = input("Enter password to access system (hint: mini_project): ")
    if attempt == PASSWORD:
        print("Access Granted!")
        return True
    else:
        print("Access Denied. Exiting.")
        return False


def show_menu():
    print("\n--- Multi-Store Inventory System ---")
    print("1. Sell Item (e.g., SELL A notebook 2)")
    print("2. Transfer Stock (e.g., TRANSFER A B pen 10)")
    print("3. Check Low Stock Report")
    print("4. Check Total Inventory Value")
    print("5. Add New Product")
    print("6. Show All Inventory")
    print("7. Exit")


def sell_item():
    command = input("Enter command (SELL <store> <item> <qty>): ")
    parts = command.split()
    if len(parts) != 4 or parts[0].upper() != 'SELL':
        print("Invalid format. Use: SELL <store> <item> <quantity>")
        return

    _, store, item_name, quantity_str = parts
    store = store.upper()
    item_name = item_name.lower()

    try:
        quantity = int(quantity_str)
        if quantity <= 0:
            print("Quantity must be positive.")
            return
    except ValueError:
        print("Invalid quantity. Enter an integer.")
        return

    conn = get_conn()
    try:
        store_id = get_store_id(conn, store)
        if store_id is None:
            print(f"Error: Store '{store}' not found.")
            return

        product_id = get_product_id(conn, item_name)
        if product_id is None:
            print(f"Error: Item '{item_name}' not found in product list.")
            return

        inv = get_inventory_row(conn, store_id, product_id)
        if not inv:
            print(f"Error: Item '{item_name}' not in store '{store}'.")
            return

        if inv["qty"] < quantity:
            print(f"Error: Insufficient stock. Only {inv['qty']} available.")
            return

        unit_price = inv["price"]
        total = unit_price * quantity
        cur = conn.cursor()

        # Insert sale and update inventory in one transaction
        cur.execute("INSERT INTO sales (store_id, product_id, quantity, unit_price, total) VALUES (?, ?, ?, ?, ?)",
                    (store_id, product_id, quantity, unit_price, total))
        cur.execute("UPDATE store_inventory SET qty = qty - ?, updated_at = CURRENT_TIMESTAMP WHERE store_id = ? AND product_id = ?",
                    (quantity, store_id, product_id))
        cur.execute("INSERT INTO audit_logs (action, details) VALUES (?, ?)",
                    ("sell", f"STORE={store}, ITEM={item_name}, QTY={quantity}, TOTAL={total}"))
        conn.commit()

        # Fetch remaining qty for printing
        new_inv = get_inventory_row(conn, store_id, product_id)
        print(f" SELL {store} {item_name} x{quantity} -> ₹{total} | {store}.{item_name}={new_inv['qty']}")
    finally:
        conn.close()


def transfer_stock():
    command = input("Enter command (TRANSFER <from> <to> <item> <qty>): ")
    parts = command.split()
    if len(parts) != 5 or parts[0].upper() != 'TRANSFER':
        print("Invalid format. Use: TRANSFER <from_store> <to_store> <item> <quantity>")
        return

    _, from_store, to_store, item_name, quantity_str = parts
    from_store = from_store.upper()
    to_store = to_store.upper()
    item_name = item_name.lower()

    try:
        quantity = int(quantity_str)
        if quantity <= 0:
            print("Quantity must be positive.")
            return
    except ValueError:
        print("Invalid quantity. Enter an integer.")
        return

    conn = get_conn()
    try:
        from_id = get_store_id(conn, from_store)
        to_id = get_store_id(conn, to_store)
        if from_id is None or to_id is None:
            print("Error: One or both stores not found.")
            return

        product_id = get_product_id(conn, item_name)
        if product_id is None:
            print(f"Error: Item '{item_name}' not found in product list.")
            return

        inv_from = get_inventory_row(conn, from_id, product_id)
        if not inv_from or inv_from["qty"] < quantity:
            available = inv_from["qty"] if inv_from else 0
            print(f"Error: Insufficient stock at '{from_store}' to transfer. Available: {available}")
            return

        cur = conn.cursor()
        # Insert transfer record
        cur.execute("INSERT INTO transfers (from_store_id, to_store_id, product_id, quantity) VALUES (?, ?, ?, ?)",
                    (from_id, to_id, product_id, quantity))
        # Decrease source
        cur.execute("UPDATE store_inventory SET qty = qty - ?, updated_at = CURRENT_TIMESTAMP WHERE store_id = ? AND product_id = ?",
                    (quantity, from_id, product_id))
        # Increase destination: if exists update, else insert with same price as source
        dest = get_inventory_row(conn, to_id, product_id)
        if dest:
            cur.execute("UPDATE store_inventory SET qty = qty + ?, updated_at = CURRENT_TIMESTAMP WHERE store_id = ? AND product_id = ?",
                        (quantity, to_id, product_id))
        else:
            # use price from source
            price = inv_from["price"]
            cur.execute("INSERT INTO store_inventory (store_id, product_id, qty, price) VALUES (?, ?, ?, ?)",
                        (to_id, product_id, quantity, price))

        cur.execute("INSERT INTO audit_logs (action, details) VALUES (?, ?)",
                    ("transfer", f"{from_store}->{to_store}, ITEM={item_name}, QTY={quantity}"))
        conn.commit()

        # Print updated quantities similar to your original print
        inv_from_new = get_inventory_row(conn, from_id, product_id)
        inv_to_new = get_inventory_row(conn, to_id, product_id)
        print(f" TRANSFER {from_store}->{to_store} {item_name} x{quantity} | {from_store}.{item_name}={inv_from_new['qty']} | {to_store}.{item_name}={inv_to_new['qty']}")
    finally:
        conn.close()


def add_product():
    print("\n--- Add New Product ---")
    store = input("Enter store (A or B): ").upper()
    conn = get_conn()
    try:
        store_id = get_store_id(conn, store)
        if store_id is None:
            print(f"Error: Store '{store}' not found. Cannot add product.")
            return

        item_name = input("Enter new product name: ").lower()

        # If product exists in that store, prevent duplicate
        prod_id = get_product_id(conn, item_name)
        inv = None
        if prod_id:
            inv = get_inventory_row(conn, store_id, prod_id)
            if inv:
                print(f"Error: '{item_name}' already exists in store '{store}'. Use 'Update Product' instead.")
                return

        # parse qty and price
        try:
            qty = int(input(f"Enter quantity for {item_name}: "))
            price = float(input(f"Enter price for {item_name}: "))
            if qty < 0 or price < 0:
                print("Quantity and price must be non-negative.")
                return
        except ValueError:
            print("Invalid number for quantity or price.")
            return

        # ensure product record
        if not prod_id:
            prod_id = create_product(conn, item_name, price)
        else:
            # ensure default price is at least set/updated
            conn.execute("UPDATE products SET default_price = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                         (price, prod_id))
            conn.commit()

        # insert inventory row
        upsert_inventory(conn, store_id, prod_id, qty, price)
        conn.execute("INSERT INTO audit_logs (action, details) VALUES (?, ?)",
                     ("add_product", f"STORE={store}, ITEM={item_name}, QTY={qty}, PRICE={price}"))
        conn.commit()
        print(f"Success: Added {item_name} (x{qty}) to Store {store}.")

    finally:
        conn.close()


def low_stock_report():
    print(f"\n--- Low Stock Report (Threshold: < {LOW_STOCK_THRESHOLD}) ---")
    conn = get_conn()
    try:
        cur = conn.execute(
            """
            SELECT s.code as store_code, p.name as product, si.qty
            FROM store_inventory si
            JOIN stores s ON s.id = si.store_id
            JOIN products p ON p.id = si.product_id
            WHERE si.qty < ?
            ORDER BY s.code, p.name
            """,
            (LOW_STOCK_THRESHOLD,)
        )
        rows = cur.fetchall()
        if not rows:
            print("No items are currently low on stock.")
            return
        for r in rows:
            print(f"  -> Store {r['store_code']} | {r['product']} | Quantity: {r['qty']}")
    finally:
        conn.close()


def total_value_report():
    print("\n--- Total Inventory Value Report ---")
    conn = get_conn()
    try:
        cur = conn.execute(
            """
            SELECT s.code AS store_code, SUM(si.qty * si.price) AS store_value
            FROM store_inventory si
            JOIN stores s ON s.id = si.store_id
            GROUP BY si.store_id
            ORDER BY s.code
            """
        )
        rows = cur.fetchall()
        total_system_value = 0
        for r in rows:
            value = r["store_value"] if r["store_value"] is not None else 0
            print(f"  Store {r['store_code']} Total Value: ₹{int(value)}")
            total_system_value += value
        print("---------------------------------")
        print(f"TOTAL SYSTEM VALUE (All Stores): ₹{int(total_system_value)}")
    finally:
        conn.close()


def show_all_inventory():
    conn = get_conn()
    try:
        print("\n--- Current Inventory ---")
        cur = conn.execute(
            """
            SELECT s.code as store_code, p.name as product, si.qty, si.price
            FROM store_inventory si
            JOIN stores s ON s.id = si.store_id
            JOIN products p ON p.id = si.product_id
            ORDER BY s.code, p.name
            """
        )
        rows = cur.fetchall()
        if not rows:
            print("No inventory data.")
        else:
            current = {}
            for r in rows:
                code = r["store_code"]
                current.setdefault(code, {})
                current[code][r["product"]] = {"qty": r["qty"], "price": r["price"]}
            print(current)

        # Daily sales totals per store (today)
        print("\n--- Daily Sales Totals (today) ---")
        cur = conn.execute(
            """
            SELECT s.code AS store_code, COALESCE(SUM(sa.total), 0) AS total_sales
            FROM sales sa
            JOIN stores s ON s.id = sa.store_id
            WHERE DATE(sa.created_at) = DATE('now')
            GROUP BY sa.store_id
            ORDER BY s.code
            """
        )
        sales_rows = cur.fetchall()
        if not sales_rows:
            # show zeroes per existing store
            cur2 = conn.execute("SELECT code FROM stores ORDER BY code")
            all_stores = [r["code"] for r in cur2.fetchall()]
            sales_map = {c: 0 for c in all_stores}
            print(sales_map)
        else:
            sales_map = {r["store_code"]: int(r["total_sales"]) for r in sales_rows}
            # ensure stores with 0 sales are shown as well
            cur2 = conn.execute("SELECT code FROM stores ORDER BY code")
            for r in cur2.fetchall():
                if r["code"] not in sales_map:
                    sales_map[r["code"]] = 0
            print(sales_map)
    finally:
        conn.close()


# ---------------------------
# Main menu loop
# ---------------------------
def main_menu():
    # Initialize DB (creates file and seeds if needed)
    init_db()
    if not login():
        return

    while True:
        show_menu()
        choice = input("Enter your choice (1-7): ").strip()
        if choice == '1':
            sell_item()
        elif choice == '2':
            transfer_stock()
        elif choice == '3':
            low_stock_report()
        elif choice == '4':
            total_value_report()
        elif choice == '5':
            add_product()
        elif choice == '6':
            show_all_inventory()
        elif choice == '7':
            print("Exiting program. Goodbye!")
            break
        else:
            print("Invalid choice. Please enter a number from 1 to 7.")


if __name__ == "__main__":
    main_menu()
