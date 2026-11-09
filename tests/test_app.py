# Tests use a fake in-memory "database" so MySQL is not needed
# and your real data is never changed.
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import app as app_module


class FakeDB:
    LOW_STOCK_LIMIT = 10

    def __init__(self):
        self.rows = []

    def get_products(self, search=""):
        return [r for r in self.rows if search.lower() in r["name"].lower()]

    def get_product(self, product_id):
        for r in self.rows:
            if r["id"] == product_id:
                return r

    def add_product(self, name, category, quantity, price):
        self.rows.append({"id": len(self.rows) + 1, "name": name,
                          "category": category, "quantity": quantity, "price": price})

    def update_product(self, product_id, name, category, quantity, price):
        self.get_product(product_id).update(name=name, category=category,
                                            quantity=quantity, price=price)

    def delete_product(self, product_id):
        self.rows = [r for r in self.rows if r["id"] != product_id]


class AppTests(unittest.TestCase):
    def setUp(self):
        self.fake = FakeDB()
        self.real_db = app_module.db
        app_module.db = self.fake          # swap in the fake database
        self.client = app_module.app.test_client()

    def tearDown(self):
        app_module.db = self.real_db

    def add(self, name="Pen", quantity="50", price="1.50"):
        return self.client.post("/products/add", follow_redirects=True, data={
            "name": name, "category": "Stationery", "quantity": quantity, "price": price})

    def test_dashboard_opens(self):
        self.assertEqual(self.client.get("/").status_code, 200)

    def test_add_valid_product(self):
        response = self.add()
        self.assertIn(b"Pen", response.data)
        self.assertEqual(len(self.fake.rows), 1)

    def test_negative_quantity(self):
        response = self.add(quantity="-1")
        self.assertIn(b"Quantity cannot be negative", response.data)
        self.assertEqual(len(self.fake.rows), 0)

    def test_negative_price(self):
        response = self.add(price="-5")
        self.assertIn(b"Price cannot be negative", response.data)
        self.assertEqual(len(self.fake.rows), 0)

    def test_bad_numbers(self):
        for quantity, price in [("abc", "1"), ("99999999999", "1"), ("1", "nan"), ("1", "1e99")]:
            self.add(quantity=quantity, price=price)
        self.assertEqual(len(self.fake.rows), 0)

    def test_edit_product(self):
        self.add()
        self.client.post("/products/1/edit", data={
            "name": "Pen", "category": "Stationery", "quantity": "20", "price": "2.00"})
        self.assertEqual(self.fake.rows[0]["quantity"], 20)

    def test_delete_product(self):
        self.add()
        self.client.post("/products/1/delete")
        self.assertEqual(len(self.fake.rows), 0)

    def test_low_stock_warning(self):
        self.add(quantity="3")
        self.assertIn(b"Low-stock alert", self.client.get("/products").data)
        self.assertIn(b"Low Stock", self.client.get("/products").data)
        self.assertIn(b"Low Stock", self.client.get("/").data)

    def test_no_warning_at_10(self):
        self.add(quantity="10")
        self.assertNotIn(b"Low-stock alert", self.client.get("/products").data)
        self.assertNotIn(b"Low Stock", self.client.get("/products").data)

    def test_show_only_low_stock(self):
        self.add(name="Pen", quantity="50")
        self.add(name="Glue", quantity="2")
        data = self.client.get("/products?filter=low").data
        self.assertIn(b"Glue", data)
        self.assertNotIn(b">Pen<", data)

    def test_search(self):
        self.add(name="Pen")
        self.add(name="Notebook")
        response = self.client.get("/products?q=note")
        self.assertIn(b"Notebook", response.data)
        self.assertNotIn(b">Pen<", response.data)


if __name__ == "__main__":
    unittest.main()
