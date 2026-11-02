
# import json
# from pathlib import Path
# from statistics import median


# BACKEND_DIR = Path(__file__).resolve().parents[2]
# DATA_DIR = BACKEND_DIR / "data"

# CONTACTS_PATH = DATA_DIR / "contacts_mock.json"
# HISTORY_PATH = DATA_DIR / "transaction_history_mock.json"


# def load_json_file(path: Path) -> dict:
#     """Load a JSON data file safely."""

#     if not path.exists():
#         raise FileNotFoundError(f"Data file not found: {path}")

#     try:
#         with path.open("r", encoding="utf-8") as file:
#             return json.load(file)
#     except json.JSONDecodeError as exc:
#         raise ValueError(f"Invalid JSON in {path.name}") from exc


# def get_user_records(user_id: str = "demo_user_001") -> tuple:
#     """Retrieve recipient and transaction records for a user."""

#     contacts_data = load_json_file(CONTACTS_PATH)
#     history_data = load_json_file(HISTORY_PATH)

#     if contacts_data.get("dataset_type") != "SYNTHETIC_DEMO_DATA":
#         raise ValueError("Unexpected contacts dataset type.")

#     if history_data.get("dataset_type") != "SYNTHETIC_DEMO_DATA":
#         raise ValueError("Unexpected transaction dataset type.")

#     contacts_user = next(
#         (
#             user for user in contacts_data.get("users", [])
#             if user.get("user_id") == user_id
#         ),
#         None,
#     )

#     history_user = next(
#         (
#             user for user in history_data.get("users", [])
#             if user.get("user_id") == user_id
#         ),
#         None,
#     )

#     if contacts_user is None or history_user is None:
#         raise ValueError("User profile or transaction history not found.")

#     return (
#         contacts_user.get("recipients", []),
#         history_user.get("transactions", []),
#     )


# def get_recipient_profile(
#     recipient_name: str,
#     user_id: str = "demo_user_001",
# ) -> dict:
#     """Find a recipient using their name or recipient ID."""

#     recipients, transactions = get_user_records(user_id)

#     search_value = recipient_name.strip().casefold()

#     if not search_value:
#         raise ValueError("Recipient name cannot be empty.")

#     # Match exact names, recipient IDs, or unique name tokens.
#     matches = [
#         item for item in recipients
#         if (
#             search_value == item.get("name", "").casefold()
#             or search_value == item.get("recipient_id", "").casefold()
#             or search_value in item.get("name", "").casefold().split()
#         )
#     ]

#     # Never select a recipient if multiple contacts match.
#     recipient = matches[0] if len(matches) == 1 else None

#     if recipient is None:
#         return {
#             "found": False,
#             "recipient": None,
#             "transaction_count": 0,
#             "typical_amount": None,
#             "last_paid": None,
#             "history_available": False,
#         }

#     recipient_id = recipient["recipient_id"]

#     successful_transactions = [
#         transaction
#         for transaction in transactions
#         if transaction.get("recipient_id") == recipient_id
#         and transaction.get("status") == "SUCCESS"
#         and isinstance(transaction.get("amount"), (int, float))
#         and transaction["amount"] > 0
#     ]

#     amounts = [
#         float(transaction["amount"])
#         for transaction in successful_transactions
#     ]

#     typical_amount = median(amounts) if amounts else None

#     timestamps = [
#         transaction["timestamp"]
#         for transaction in successful_transactions
#         if transaction.get("timestamp")
#     ]

#     last_paid = max(timestamps) if timestamps else None

#     return {
#         "found": True,
#         "recipient": {
#             "recipient_id": recipient["recipient_id"],
#             "name": recipient["name"],
#             "upi_id": recipient["upi_id"],
#             "verified_by_user": recipient["verified_by_user"],
#             "is_active": recipient["is_active"],
#         },
#         "transaction_count": len(successful_transactions),
#         "typical_amount": typical_amount,
#         "last_paid": last_paid,
#         "history_available": len(amounts) >= 3,
#     }



import json
from pathlib import Path
from statistics import median


BACKEND_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BACKEND_DIR / "data"

CONTACTS_PATH = DATA_DIR / "contacts_mock.json"
HISTORY_PATH = DATA_DIR / "transaction_history_mock.json"


def load_json_file(path: Path) -> dict:
    """Load a JSON data file safely."""

    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {path}")

    try:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path.name}") from exc


def get_user_records(user_id: str = "demo_user_001") -> tuple:
    """Retrieve recipient and transaction records for a user."""

    contacts_data = load_json_file(CONTACTS_PATH)
    history_data = load_json_file(HISTORY_PATH)

    if contacts_data.get("dataset_type") != "SYNTHETIC_DEMO_DATA":
        raise ValueError("Unexpected contacts dataset type.")

    if history_data.get("dataset_type") != "SYNTHETIC_DEMO_DATA":
        raise ValueError("Unexpected transaction dataset type.")

    contacts_user = next(
        (
            user for user in contacts_data.get("users", [])
            if user.get("user_id") == user_id
        ),
        None,
    )

    history_user = next(
        (
            user for user in history_data.get("users", [])
            if user.get("user_id") == user_id
        ),
        None,
    )

    if contacts_user is None or history_user is None:
        raise ValueError("User profile or transaction history not found.")

    return (
        contacts_user.get("recipients", []),
        history_user.get("transactions", []),
    )


def get_recipient_profile(
    recipient_name: str,
    user_id: str = "demo_user_001",
) -> dict:
    """Find a recipient using their name or recipient ID."""

    recipients, transactions = get_user_records(user_id)

    search_value = recipient_name.strip().casefold()

    if not search_value:
        raise ValueError("Recipient name cannot be empty.")

    # Match exact names, recipient IDs, or unique name tokens.
    matches = [
        item for item in recipients
        if (
            search_value == item.get("name", "").casefold()
            or search_value == item.get("recipient_id", "").casefold()
            or search_value in item.get("name", "").casefold().split()
        )
    ]

    match_count = len(matches)

    # Never select a recipient if multiple contacts match.
    recipient = matches[0] if match_count == 1 else None

    if recipient is None:
        return {
            "found": False,
            "match_count": match_count,
            "recipient": None,
            "transaction_count": 0,
            "typical_amount": None,
            "last_paid": None,
            "history_available": False,
        }

    recipient_id = recipient["recipient_id"]

    successful_transactions = [
        transaction
        for transaction in transactions
        if transaction.get("recipient_id") == recipient_id
        and transaction.get("status") == "SUCCESS"
        and isinstance(transaction.get("amount"), (int, float))
        and transaction["amount"] > 0
    ]

    amounts = [
        float(transaction["amount"])
        for transaction in successful_transactions
    ]

    typical_amount = median(amounts) if amounts else None

    timestamps = [
        transaction["timestamp"]
        for transaction in successful_transactions
        if transaction.get("timestamp")
    ]

    last_paid = max(timestamps) if timestamps else None

    return {
        "found": True,
        "match_count": match_count,
        "recipient": {
            "recipient_id": recipient["recipient_id"],
            "name": recipient["name"],
            "upi_id": recipient["upi_id"],
            "verified_by_user": recipient["verified_by_user"],
            "is_active": recipient["is_active"],
        },
        "transaction_count": len(successful_transactions),
        "typical_amount": typical_amount,
        "last_paid": last_paid,
        "history_available": len(amounts) >= 3,
    }
