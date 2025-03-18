import sys
import mysql.connector
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QTextEdit, QPushButton, 
    QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView
)
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt

# MySQL Database Connection
def connect_db():
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",  # Change if needed
            password="root",  # Change if needed
            database="billing_db"
        )
        print("✅ Connected to MySQL!")
        return connection
    except mysql.connector.Error as e:
        print("❌ Error connecting to MySQL:", e)
        sys.exit(1)

class BillingApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Billing System")
        self.setGeometry(100, 100, 600, 500)

        # Apply styles
        self.setStyleSheet("""
            QWidget {
                background-color: #ADD8E6;  /* Light Blue Background */
                color: black;  /* All Text Black */
                font-family: Arial;
            }
            QLabel {
                color: black; 
                font-size: 12px;
                font-weight: bold;
            }
            QLineEdit, QTextEdit {
                background: white;
                color: black;
                padding: 5px;
                border-radius: 5px;
                border: 1px solid gray;
            }
            QPushButton {
                background-color: #007ACC; /* Blue Buttons */
                color: white;
                padding: 8px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #005A9E;
            }
            QPushButton#clear_btn {
                background-color: #E74C3C; /* Red Button */
            }
            QPushButton#clear_btn:hover {
                background-color: #C0392B;
            }
            QTableWidget {
                background-color: white;
                color: black;
                border: 1px solid gray;
            }
        """)

        self.db = connect_db()
        self.layout = QVBoxLayout()
        self.initUI()
        self.setLayout(self.layout)

    def initUI(self):
        # Header
        self.header = QLabel("Billing Management System")
        self.header.setFont(QFont("Arial", 16, QFont.Bold))
        self.header.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.header)

        # Input Fields (With Placeholders)
        self.name_input = self.create_input("Customer Name:", "Enter full name")
        self.phone_input = self.create_input("Phone:", "Enter mobile number")
        self.email_input = self.create_input("Email:", "Enter email address")
        self.amount_input = self.create_input("Total Amount:", "Enter total bill amount")

        # Items Purchased (With Placeholder)
        self.items_input = QTextEdit()
        self.items_input.setPlaceholderText("Enter items purchased (e.g., 2x Milk, 1x Bread)")
        self.layout.addWidget(QLabel("Items Purchased:"))
        self.layout.addWidget(self.items_input)

        # Buttons
        btn_layout = QHBoxLayout()
        self.submit_btn = self.create_button("💾 Save Bill", "#007ACC", self.save_bill)
        self.view_btn = self.create_button("📜 View Bills", "#007ACC", self.view_bills)
        self.clear_btn = QPushButton("❌ Clear All Bills")
        self.clear_btn.setObjectName("clear_btn")
        self.clear_btn.clicked.connect(self.clear_all_bills)
        
        btn_layout.addWidget(self.submit_btn)
        btn_layout.addWidget(self.view_btn)
        btn_layout.addWidget(self.clear_btn)
        self.layout.addLayout(btn_layout)

        # Table for Bills
        self.bill_table = QTableWidget()
        self.bill_table.setColumnCount(4)
        self.bill_table.setHorizontalHeaderLabels(["Bill ID", "Customer Name", "Purchased Items", "Total Amount"])
        self.bill_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.layout.addWidget(self.bill_table)

    def create_input(self, label, placeholder):
        """Create input fields with labels and placeholders"""
        lbl = QLabel(label)
        lbl.setFont(QFont("Arial", 10))
        
        input_field = QLineEdit()
        input_field.setPlaceholderText(placeholder)  # ✅ Placeholder applied

        self.layout.addWidget(lbl)
        self.layout.addWidget(input_field)
        return input_field

    def create_button(self, text, color, func):
        """Create styled buttons"""
        btn = QPushButton(text)
        btn.clicked.connect(func)
        return btn

    def save_bill(self):
        """Save a new bill to the database"""
        name = self.name_input.text().strip()
        phone = self.phone_input.text().strip()
        email = self.email_input.text().strip()
        items = self.items_input.toPlainText().strip()
        total_amount = self.amount_input.text().strip()

        if not (name and phone and email and items and total_amount):
            print("⚠️ All fields are required!")
            return

        try:
            cursor = self.db.cursor()

            # Insert customer if not exists
            cursor.execute("SELECT id FROM customers WHERE phone = %s", (phone,))
            result = cursor.fetchone()

            if result:
                customer_id = result[0]
            else:
                cursor.execute(
                    "INSERT INTO customers (name, phone, email) VALUES (%s, %s, %s)",
                    (name, phone, email),
                )
                self.db.commit()
                customer_id = cursor.lastrowid

            # Insert bill
            cursor.execute(
                "INSERT INTO bills (customer_id, items, total_amount) VALUES (%s, %s, %s)",
                (customer_id, items, total_amount),
            )
            self.db.commit()
            print("✅ Bill saved successfully!")
            cursor.close()
            self.clear_fields()
        except mysql.connector.Error as e:
            print("❌ Error saving bill:", e)

    def view_bills(self):
        """Fetch and display all bills"""
        try:
            cursor = self.db.cursor()
            cursor.execute("""
                SELECT b.id, c.name, b.items, b.total_amount 
                FROM bills b 
                JOIN customers c ON b.customer_id = c.id
            """)
            bills = cursor.fetchall()
            cursor.close()

            self.bill_table.setRowCount(len(bills))
            for row_idx, row_data in enumerate(bills):
                for col_idx, value in enumerate(row_data):
                    self.bill_table.setItem(row_idx, col_idx, QTableWidgetItem(str(value)))

            print("📜 Bills loaded successfully!")
        except mysql.connector.Error as e:
            print("❌ Error fetching bills:", e)

    def clear_all_bills(self):
        """Delete all bills from the database"""
        try:
            cursor = self.db.cursor()
            cursor.execute("DELETE FROM bills")
            self.db.commit()
            cursor.close()

            # Clear the table display
            self.bill_table.setRowCount(0)
            print("❌ All bills deleted successfully!")
        except mysql.connector.Error as e:
            print("❌ Error deleting bills:", e)

    def clear_fields(self):
        """Clear all input fields after saving"""
        self.name_input.clear()
        self.phone_input.clear()
        self.email_input.clear()
        self.items_input.clear()
        self.amount_input.clear()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = BillingApp()
    window.show()
    sys.exit(app.exec())
