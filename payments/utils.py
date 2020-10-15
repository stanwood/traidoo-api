from decimal import Decimal

NATURAL_USER_TYPES = frozenset({"einzelunternehmer", "einzelunternehmen"})
COMPANY_TYPE_MAPPING = {
    "gbr": "SOLETRADER",
    "gewerbliche gbr": "SOLETRADER",
    "landwirtschaftliche gbr": "SOLETRADER",
    "e.v.": "ORGANIZATION",
    "eg": "ORGANIZATION",
    "genossenschaft": "ORGANIZATION",
    "verein": "ORGANIZATION",
}


def euro_to_cents(value) -> int:
    return int(Decimal(str(value)) * 100)


def lookup_user_type(company_type: str = None) -> str:
    if company_type and company_type.lower() in NATURAL_USER_TYPES:
        return "natural"
    else:
        return "legal"


def lookup_legal_person_type(company_type_name: str) -> str:
    try:
        return COMPANY_TYPE_MAPPING[company_type_name.lower()]
    except KeyError:
        return "BUSINESS"
