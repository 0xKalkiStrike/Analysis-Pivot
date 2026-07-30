"""Global constants."""
from __future__ import annotations

SUPPORTED_EXCEL = {".xlsx", ".xls", ".xlsm", ".xlsb"}
SUPPORTED_CSV = {".csv", ".tsv", ".txt"}
SUPPORTED_ALL = SUPPORTED_EXCEL | SUPPORTED_CSV

# Column semantics for smart detection
COLUMN_HINTS: dict[str, tuple[str, ...]] = {
    "email": ("email", "e-mail", "mail", "email_address", "emailid"),
    "phone": ("phone", "mobile", "contact", "tel", "telephone", "phone_no", "mobile_no"),
    "id": ("id", "customer_id", "cust_id", "user_id", "record_id"),
    "invoice": ("invoice", "invoice_no", "invoice_id", "bill_no", "bill_id"),
    "gst": ("gst", "gstin", "tax_id", "vat", "gst_no"),
    "product": ("product", "product_code", "sku", "item_code", "product_id"),
    "name": ("name", "full_name", "customer_name", "company", "company_name"),
    "address": ("address", "addr", "street", "location"),
    "city": ("city", "town"),
    "state": ("state", "province", "region"),
    "country": ("country", "nation"),
    "zip": ("zip", "postcode", "postal_code", "pincode", "pin"),
    "date": ("date", "created", "updated", "timestamp", "dob", "birthday"),
    "amount": ("amount", "price", "cost", "total", "value", "salary"),
}

DUP_STRATEGIES = (
    "exact",
    "case_insensitive",
    "whitespace_normalized",
    "unicode_normalized",
    "hash",
    "fuzzy",
    "token",
    "phonetic",
)

DEFAULT_FUZZY_THRESHOLD = 88.0
