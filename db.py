import mysql.connector

LOW_STOCK_LIMIT = 10


def connect():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="inventory_management",
    )


def get_products(search=""):
    conn = connect()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM products WHERE name LIKE %s ORDER BY name",
                   ("%" + search + "%",))
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_product(product_id):
    conn = connect()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
    row = cursor.fetchone()
    conn.close()
    return row


def add_product(name, category, quantity, price):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO products (name, category, quantity, price) VALUES (%s, %s, %s, %s)",
        (name, category, quantity, price))
    conn.commit()
    conn.close()


def update_product(product_id, name, category, quantity, price):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE products SET name=%s, category=%s, quantity=%s, price=%s WHERE id=%s",
        (name, category, quantity, price, product_id))
    conn.commit()
    conn.close()


def delete_product(product_id):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM products WHERE id = %s", (product_id,))
    conn.commit()
    conn.close()
