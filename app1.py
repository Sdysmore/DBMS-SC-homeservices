import streamlit as st
import pymysql
from pymysql import MySQLError

# Connect to MySQL database using pymysql
def create_connection():
    connection = None
    try:
        connection = pymysql.connect(
            host="localhost",
            user="root",
            password="gaharabg",
            database="home_services"
        )
        st.write("Connected to MySQL database successfully.")
    except MySQLError as e:
        st.error(f"Error connecting to MySQL: {e}")
    return connection

# Register a new user without hashing password
def register_user(name, email, password, role="user"):
    conn = create_connection()
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO Users (name, email, password, role) VALUES (%s, %s, %s, %s)",
                           (name, email, password, role))
            conn.commit()
            st.success("Registration successful!")
        except MySQLError as e:
            st.error(f"Error: {e}")
        finally:
            cursor.close()
            conn.close()

# Display available services
def display_services():
    conn = create_connection()
    if conn:
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        try:
            cursor.execute("SELECT * FROM Services")
            services = cursor.fetchall()
            for service in services:
                st.write(f"Service Name: {service['service_name']}")
                st.write(f"Description: {service['description']}")
                st.write(f"Price: ${service['price']}")
                if st.button(f"Order {service['service_name']}"):
                    st.session_state["service_id"] = service["service_id"]
                    st.session_state["service_name"] = service["service_name"]
                    st.session_state["service_price"] = service["price"]
        except MySQLError as e:
            st.error(f"Error: {e}")
        finally:
            cursor.close()
            conn.close()

# Place an order
def place_order(user_id, service_id):
    conn = create_connection()
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO Orders (user_id, service_id) VALUES (%s, %s)", (user_id, service_id))
            conn.commit()
            st.success("Order placed successfully!")
        except MySQLError as e:
            st.error(f"Error: {e}")
        finally:
            cursor.close()
            conn.close()

# Fetch order history for a user
def get_order_history(user_id):
    conn = create_connection()
    order_history = []
    if conn:
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        try:
            cursor.execute("SELECT Orders.order_id, Services.service_name, Services.price FROM Orders "
                           "JOIN Services ON Orders.service_id = Services.service_id "
                           "WHERE Orders.user_id = %s", (user_id,))
            order_history = cursor.fetchall()
        except MySQLError as e:
            st.error(f"Error: {e}")
        finally:
            cursor.close()
            conn.close()
    return order_history

# Main Streamlit app
def main():
    st.title("Home Services Application")

    menu = ["Home", "Register", "Services", "Order History"]
    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "Home":
        st.subheader("Welcome to the Home Services Platform")
    
    elif choice == "Register":
        st.subheader("Register New User")
        name = st.text_input("Name")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        if st.button("Register"):
            register_user(name, email, password)
    
    elif choice == "Services":
        st.subheader("Available Services")
        display_services()
        if "service_id" in st.session_state:
            if st.button(f"Confirm Order for {st.session_state['service_name']}"):
                # Replace 1 with logged-in user ID (adjust as per user session management)
                place_order(user_id=1, service_id=st.session_state["service_id"])
    
    elif choice == "Order History":
        st.subheader("Your Orders")
        orders = get_order_history(user_id=1)  # Replace 1 with actual user_id after login
        if orders:
            for order in orders:
                st.write(f"Order ID: {order['order_id']}")

               st.write(f"Service: {order['service_name']}")
                st.write(f"Price: ${order['price']}")
                st.write("---")
        else:
            st.write("No orders found.")

if __name__ == "__main__":
    main()
