
from src.database.repository import DatabaseRepository


repository = DatabaseRepository()

try:
    print("Repository initialized successfully!")

    customer = repository.get_customer("CUST0001")

    print("Customer lookup result:", customer)

    print(
        "Event EVT000001 processed:",
        repository.is_event_processed("EVT000001")
    )

finally:
    repository.close()
    print("Repository connection closed.")
