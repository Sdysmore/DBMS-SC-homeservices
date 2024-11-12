import streamlit as st
import pymysql
from pymysql.err import MySQLError

# Connect to MySQL database
def create_connection():
    try:
        connection = pymysql.connect(
            host="localhost",
            user="root",
            password="gaharabg",  
            database="home_services",
            cursorclass=pymysql.cursors.DictCursor
        )
        return connection
    except MySQLError as e:
        st.error(f"Error connecting to MySQL: {e}")
        return None

# Create the OrderDeletionLog table and trigger for logging order deletions
def create_trigger():
    conn = create_connection()
    cursor = conn.cursor()
    try:
        # Create OrderDeletionLog table if not exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS OrderDeletionLog (
                log_id INT AUTO_INCREMENT PRIMARY KEY,
                order_id INT NOT NULL,
                deletion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Drop the trigger if it already exists
        cursor.execute("DROP TRIGGER IF EXISTS log_order_deletion")
        
        # Create the trigger for logging order deletions
        cursor.execute("""
            CREATE TRIGGER log_order_deletion
            AFTER DELETE ON Orders
            FOR EACH ROW
            BEGIN
                INSERT INTO OrderDeletionLog (order_id) VALUES (OLD.order_id);
            END;
        """)
        
        conn.commit()
    except MySQLError as e:
        st.error(f"Error creating trigger: {e}")
    finally:
        cursor.close()
        conn.close()

# Register a new user
def register_user(name, email, password):
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO Users (name, email, password) VALUES (%s, %s, %s)", (name, email, password))
        conn.commit()
        st.success("Registration successful! Please log in.")
    except MySQLError as e:
        st.error(f"Error: {e}")
    finally:
        cursor.close()
        conn.close()

# Login function
def login_user(email, password):
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM Users WHERE email = %s AND password = %s", (email, password))
        user = cursor.fetchone()
        if user:
            st.session_state["user_id"] = user["user_id"]
            st.session_state["name"] = user["name"]
            st.success("Logged in successfully!")
        else:
            st.error("Incorrect email or password.")
    finally:
        cursor.close()
        conn.close()

# Display available services
def display_services():
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM Services")
        services = cursor.fetchall()
        for service in services:
            st.write(f"**{service['service_name']}** - ${service['price']}")
            st.write(f"{service['description']}")
            extra_info = st.text_input(f"Extra info for {service['service_name']}", key=f"extra_info_{service['service_id']}")
            if st.button(f"Order {service['service_name']}", key=service['service_id']):
                place_order(st.session_state["user_id"], service["service_id"], extra_info)
    except MySQLError as e:
        st.error(f"Error: {e}")
    finally:
        cursor.close()
        conn.close()

# Place an order with extra info
def place_order(user_id, service_id, extra_info):
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO Orders (user_id, service_id) VALUES (%s, %s)", (user_id, service_id))
        order_id = cursor.lastrowid
        
        # Store extra info in an additional table (e.g., OrderDetails)
        if extra_info:
            cursor.execute("INSERT INTO OrderDetails (order_id, extra_info) VALUES (%s, %s)", (order_id, extra_info))
        conn.commit()
        st.success("Order placed successfully!")
    except MySQLError as e:
        st.error(f"Error: {e}")
    finally:
        cursor.close()
        conn.close()

def view_order_history(user_id):
    conn = create_connection()
    cursor = conn.cursor()
    try:
        # Fetch individual orders for the user with extra info
        cursor.execute(""" 
            SELECT Orders.order_id, Services.service_name, Orders.order_date, OrderDetails.extra_info, Services.price
            FROM Orders 
            JOIN Services ON Orders.service_id = Services.service_id
            LEFT JOIN OrderDetails ON Orders.order_id = OrderDetails.order_id
            WHERE Orders.user_id = %s
        """, (user_id,))
        orders = cursor.fetchall()
        
        # Display each order with details
        for order in orders:
            st.write(f"**{order['service_name']}** ordered on {order['order_date']} - ${order['price']}")
            st.write(f"Extra info: {order['extra_info']}")
            if st.button(f"Update {order['service_name']} Order", key=f"update_{order['order_id']}"):
                update_order(order['order_id'], order['extra_info'])
            if st.button(f"Delete {order['service_name']} Order", key=f"delete_{order['order_id']}"):
                delete_order(order['order_id'])
        
        # Nested query to calculate the sum of all orders for the user
        cursor.execute("""
            SELECT SUM(Services.price) AS total_spent
            FROM Orders 
            JOIN Services ON Orders.service_id = Services.service_id
            WHERE Orders.user_id = %s
        """, (user_id,))
        total_spent = cursor.fetchone()['total_spent']
        
        # Display total amount spent
        st.write(f"**Total Amount Spent:** ${total_spent:.2f}")
        
    except MySQLError as e:
        st.error(f"Error: {e}")
    finally:
        cursor.close()
        conn.close()

# Update an order with new extra info
def update_order(order_id, current_extra_info):
    new_extra_info = st.text_input("Update Extra Info", value=current_extra_info, key=f"update_info_{order_id}")
    if st.button(f"Save Update for Order {order_id}", key=f"save_{order_id}"):
        conn = create_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE OrderDetails SET extra_info = %s WHERE order_id = %s", (new_extra_info, order_id))
            conn.commit()
            st.success("Order updated successfully!")
        except MySQLError as e:
            st.error(f"Error: {e}")
        finally:
            cursor.close()
            conn.close()

# Delete an order
def delete_order(order_id):
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM Orders WHERE order_id = %s", (order_id,))
        cursor.execute("DELETE FROM OrderDetails WHERE order_id = %s", (order_id,))  # Delete associated extra info
        conn.commit()
        st.success("Order deleted successfully.")
    except MySQLError as e:
        st.error(f"Error: {e}")
    finally:
        cursor.close()
        conn.close()

# Main Streamlit app
def main():
    st.title("Home Services Platform")

    # Call create_trigger to set up the trigger when the app initializes
    create_trigger()

    if "user_id" not in st.session_state:
        st.sidebar.title("Authentication")
        auth_choice = st.sidebar.radio("Choose Action", ["Login", "Register"])

        if auth_choice == "Register":
            st.sidebar.subheader("Create a new account")
            name = st.sidebar.text_input("Name")
            email = st.sidebar.text_input("Email")
            password = st.sidebar.text_input("Password", type="password")
            if st.sidebar.button("Register"):
                register_user(name, email, password)

        elif auth_choice == "Login":
            st.sidebar.subheader("Login to your account")
            email = st.sidebar.text_input("Email")
            password = st.sidebar.text_input("Password", type="password")
            if st.sidebar.button("Login"):
                login_user(email, password)
    else:
        st.sidebar.write(f"Welcome, {st.session_state['name']}")
        if st.sidebar.button("Logout"):
            st.session_state.clear()

        menu = ["Services", "Order History"]
        choice = st.sidebar.selectbox("Menu", menu)

        if choice == "Services":
            st.subheader("Available Services")
            display_services()

        elif choice == "Order History":
            st.subheader("Your Order History")
            view_order_history(st.session_state["user_id"])

if __name__ == "__main__":
    main()
