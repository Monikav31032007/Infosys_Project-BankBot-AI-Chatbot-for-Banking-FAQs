# database/init_sample_data.py

from database.db import init_db
from database import bank_crud

def seed():
    init_db()

    # Users
    bank_crud.create_user("Monika", "1111")
    bank_crud.create_user("Priya", "1234")
    bank_crud.create_user("Neha", "5678")

    # Monika’s accounts 
    bank_crud.create_account("Monika", "700001", "Rani",   "savings", 90000, "1111")
    bank_crud.create_account("Monika", "700002", "Malar",  "current", 35000, "1111")
    bank_crud.create_account("Monika", "700003", "Arun",   "checking",25000, "1111")
    bank_crud.create_account("Monika", "700004", "Raj",    "business",45000, "1111")
    bank_crud.create_account("Monika", "700005", "Pravin", "savings", 30000, "1111")

    # Priya’s accounts
    bank_crud.create_account("Priya", "100001", "Sneha",  "savings", 50000, "1234")
    bank_crud.create_account("Priya", "100002", "Divya",  "current", 20000, "1234")
    bank_crud.create_account("Priya", "100003", "Rahul", "checking",15000, "1234")

    # Neha’s accounts
    bank_crud.create_account("Neha", "200001", "Meera",   "savings", 30000, "5678")
    bank_crud.create_account("Neha", "200002", "Shalini",  "business",18000, "5678")
    bank_crud.create_account("Neha", "200003", "Suresh",   "current", 22000, "5678")

    # Cards 
    bank_crud.add_card("700001", "debit",  "1111")
    bank_crud.add_card("700002", "credit", "1111")
    bank_crud.add_card("700003", "debit",  "1111")  
    bank_crud.add_card("700004", "credit", "1111")
    bank_crud.add_card("700005", "debit",  "1111")
    bank_crud.add_card("100001", "debit",  "1234")
    bank_crud.add_card("200001", "credit", "8888")

    print("✅ Database initialized with users Monika/Alice/Bob and multiple named accounts each.")

if __name__ == "__main__":
    seed()
