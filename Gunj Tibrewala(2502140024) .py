# 1. --- DATA ---
# Using a nested dictionary as required
# This holds the main inventory data.
inventory = {'A': {'pen': {'qty': 50, 'price': 10}, 'notebook': {'qty': 10, 'price': 40}},
             'B': {'pen': {'qty': 20, 'price': 10}, 'mouse': {'qty': 5, 'price': 150}}}

# This dictionary will track the total sales value for each store.
daily_sales = {'A': 0, 'B': 0}

# Define a low-stock threshold
LOW_STOCK_THRESHOLD = 10


# 2. --- CORE FUNCTIONS ---

def login():
    password = "miniproject"
    attempt = input("Enter password to access system (hint: miniproject): ")
    if attempt == password:
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

    # This line will crash if user enters text instead of a number
    quantity = int(quantity_str)

    if store not in inventory:
        print(f"Error: Store '{store}' not found.")
        return
    if item_name not in inventory[store]:
        print(f"Error: Item '{item_name}' not in store '{store}'.")
        return

    # Check stock
    if inventory[store][item_name]['qty'] >= quantity:
        # Process the sale
        price = inventory[store][item_name]['price']
        total_bill = price * quantity
        # Update stock quantity
        inventory[store][item_name]['qty'] -= quantity
        # Update daily sales total
        daily_sales[store] += total_bill
        # Print report as per sample output
        print(f" SELL {store} {item_name} x{quantity} -> ₹{total_bill} | {store}.{item_name}={inventory[store][item_name]['qty']}")
    else:
        print(f"Error: Insufficient stock. Only {inventory[store][item_name]['qty']} available.")


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

    # This line will crash if user enters text instead of a number
    quantity = int(quantity_str)

    # Validation
    if from_store not in inventory or to_store not in inventory:
        print("Error: One or both stores not found.")
        return
    if item_name not in inventory[from_store]:
        print(f"Error: Item '{item_name}' not in source store '{from_store}'.")
        return

    # Check stock
    if inventory[from_store][item_name]['qty'] >= quantity:
        # Process the transfer

        # 1. Decrease from source store
        inventory[from_store][item_name]['qty'] -= quantity

        # 2. Increase in destination store
        # Check if item already exists in the destination
        if item_name in inventory[to_store]:
            inventory[to_store][item_name]['qty'] += quantity
        else:
            # If not, add it (using the price from the source store)
            price = inventory[from_store][item_name]['price']
            inventory[to_store][item_name] = {'qty': quantity, 'price': price}

        print(f" TRANSFER {from_store}->{to_store} {item_name} x{quantity} | {from_store}.{item_name}={inventory[from_store][item_name]['qty']} | {to_store}.{item_name}={inventory[to_store][item_name]['qty']}")
    else:
        print(f"Error: Insufficient stock at '{from_store}' to transfer.")


# 3. --- 'TO-DO' FUNCTIONS (Your next steps) ---

def add_product():
    print("\n--- Add New Product ---")
    store = input("Enter store (A or B): ").upper()
    if store not in inventory:
        print(f"Error: Store '{store}' not found. Cannot add product.")
        return

    item_name = input("Enter new product name: ").lower()

    # Check if item already exists
    if item_name in inventory[store]:
        print(f"Error: '{item_name}' already exists in store '{store}'. Use 'Update Product' instead.")
        return

    # These lines will crash if user enters text
    qty = int(input(f"Enter quantity for {item_name}: "))
    price = float(input(f"Enter price for {item_name}: "))

    # Create the new nested dictionary entry
    inventory[store][item_name] = {'qty': qty, 'price': price}
    print(f"Success: Added {item_name} (x{qty}) to Store {store}.")


def low_stock_report():
    print(f"\n--- Low Stock Report (Threshold: < {LOW_STOCK_THRESHOLD}) ---")
    found_low_stock = False
    # We must loop through all stores, then all items in each store
    for store_name, store_items in inventory.items():
        for item_name, details in store_items.items():
            if details['qty'] < LOW_STOCK_THRESHOLD:
                print(f"  -> Store {store_name} | {item_name} | Quantity: {details['qty']}")
                found_low_stock = True

    if not found_low_stock:
        print("No items are currently low on stock.")


def total_value_report():
    print("\n--- Total Inventory Value Report ---")
    total_system_value = 0
    # Loop through each store
    for store_name, store_items in inventory.items():
        store_total_value = 0
        # Loop through each item in the store
        for item_name, details in store_items.items():
            item_value = details['qty'] * details['price']
            store_total_value += item_value

        print(f"  Store {store_name} Total Value: ₹{store_total_value}")
        total_system_value += store_total_value

    print("---------------------------------")
    print(f"TOTAL SYSTEM VALUE (All Stores): ₹{total_system_value}")


# 4. --- MAIN PROGRAM LOOP ---

def main_menu():
    if not login():
        return

    # This 'while True' loop keeps the menu running
    while True:
        show_menu()
        choice = input("Enter your choice (1-7): ")

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
            print("\n--- Current Inventory ---")
            print(inventory)
            print("\n--- Daily Sales Totals ---")
            print(daily_sales)
        elif choice == '7':
            print("Exiting program. Goodbye!")
            break
        else:
            # Handles invalid menu choices
            print("Invalid choice. Please enter a number from 1 to 7.")


if __name__ == "__main__":
    main_menu()