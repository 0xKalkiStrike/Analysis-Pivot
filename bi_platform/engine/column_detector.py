"""Automatic Column Detection and Alias Mapping Engine.

Maps variations in column headers across different spreadsheets to standardized
canonical column names (e.g. 'Customer Name', 'Full Name' -> 'Name').
"""
from __future__ import annotations

import re
from typing import Iterable

# Default canonical field alias dictionary
DEFAULT_COLUMN_ALIASES: dict[str, list[str]] = {
    "Name": [
        "name", "customer name", "full name", "client name", "user name",
        "person name", "contact name", "first name", "last name", "owner name"
    ],
    "Address": [
        "address", "customer address", "home address", "office address",
        "street address", "addr", "street", "location", "billing address", "shipping address"
    ],
    "Phone Number": [
        "phone", "mobile", "contact number", "telephone", "phone number",
        "mobile no", "tel", "contact no", "cell", "phone_no", "mobile_number"
    ],
    "Email": [
        "email", "email address", "mail id", "mail", "e-mail", "email_id", "emailaddress"
    ],
    "Company": [
        "company", "company name", "organization", "org", "client company",
        "business name", "vendor", "supplier"
    ],
    "City": [
        "city", "town", "municipality", "location_city"
    ],
    "State": [
        "state", "province", "region", "territory"
    ],
    "Country": [
        "country", "nation"
    ],
    "ZIP Code": [
        "zip", "zip code", "postcode", "postal code", "pincode", "pin", "zipcode"
    ],
    "GST Number": [
        "gst", "gst number", "gstin", "tax id", "vat", "gst_no", "gstin_number"
    ],
    "PAN Number": [
        "pan", "pan number", "pan_no", "tax_number", "pan_card"
    ],
    "Customer ID": [
        "customer id", "cust id", "client id", "account id", "user id", "id", "customer_no"
    ],
    "Product Code": [
        "product code", "product id", "sku", "item code", "product", "part_number"
    ],
    "Invoice Number": [
        "invoice number", "invoice no", "invoice id", "bill number", "bill no", "inv_no"
    ],
    "Website": [
        "website", "web", "url", "site", "web_address", "domain"
    ],
    "Social Links": [
        "social links", "linkedin", "twitter", "facebook", "handle", "social_media"
    ],
    "Date of Birth": [
        "date of birth", "dob", "birthday", "birth date", "birth_date"
    ]
}


class ColumnDetector:
    """Detects semantic meaning of columns and maps alias variations to canonical names."""

    def __init__(self, custom_aliases: dict[str, list[str]] | None = None) -> None:
        self.aliases = dict(DEFAULT_COLUMN_ALIASES)
        if custom_aliases:
            for canonical, alias_list in custom_aliases.items():
                existing = self.aliases.setdefault(canonical, [])
                for a in alias_list:
                    if a not in existing:
                        existing.append(a)

    @staticmethod
    def _normalize_name(name: str) -> str:
        s = str(name).strip().lower()
        s = re.sub(r"[_\-\.]+", " ", s)
        s = re.sub(r"\s+", " ", s)
        return s

    def map_column(self, col_name: str) -> str:
        """Map a single column header to its canonical name or return the normalized original."""
        norm = self._normalize_name(col_name)

        # 1. Exact alias match
        for canonical, alias_list in self.aliases.items():
            norm_aliases = [self._normalize_name(a) for a in alias_list]
            if norm in norm_aliases:
                return canonical

        # 2. Substring/contains match (e.g. 'Customer_Full_Name')
        for canonical, alias_list in self.aliases.items():
            for a in alias_list:
                norm_a = self._normalize_name(a)
                if len(norm_a) >= 3 and (norm_a in norm or norm in norm_a):
                    return canonical

        # Default fallback
        return col_name.strip()

    def map_columns(self, columns: Iterable[str]) -> dict[str, str]:
        """Map a list of column headers to a dictionary of {original_column: canonical_name}."""
        mapping: dict[str, str] = {}
        seen_canonical: dict[str, int] = {}

        for col in columns:
            canonical = self.map_column(str(col))
            if canonical in seen_canonical:
                seen_canonical[canonical] += 1
                mapping[str(col)] = f"{canonical} ({seen_canonical[canonical]})"
            else:
                seen_canonical[canonical] = 1
                mapping[str(col)] = canonical

        return mapping

    def get_aliases_config(self) -> dict[str, list[str]]:
        return self.aliases

    def add_alias(self, canonical: str, alias: str) -> None:
        if canonical not in self.aliases:
            self.aliases[canonical] = []
        if alias not in self.aliases[canonical]:
            self.aliases[canonical].append(alias)
