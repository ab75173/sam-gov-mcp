"""Reference data for the SAM.gov Opportunities API v2.

These code tables come from the official GSA documentation:
https://open.gsa.gov/api/get-opportunities-public-api/
"""

# typeOfSetAside code -> human-readable description (FAR small-business programs).
SET_ASIDE_CODES: dict[str, str] = {
    "SBA": "Total Small Business Set-Aside (FAR 19.5)",
    "SBP": "Partial Small Business Set-Aside (FAR 19.5)",
    "8A": "8(a) Set-Aside (FAR 19.8)",
    "8AN": "8(a) Sole Source (FAR 19.8)",
    "HZC": "HUBZone Set-Aside (FAR 19.13)",
    "HZS": "HUBZone Sole Source (FAR 19.13)",
    "SDVOSBC": "Service-Disabled Veteran-Owned Small Business Set-Aside (FAR 19.14)",
    "SDVOSBS": "Service-Disabled Veteran-Owned Small Business Sole Source (FAR 19.14)",
    "WOSB": "Women-Owned Small Business Program Set-Aside (FAR 19.15)",
    "WOSBSS": "Women-Owned Small Business Program Sole Source (FAR 19.15)",
    "EDWOSB": "Economically Disadvantaged WOSB Program Set-Aside (FAR 19.15)",
    "EDWOSBSS": "Economically Disadvantaged WOSB Program Sole Source (FAR 19.15)",
    "LAS": "Local Area Set-Aside (FAR 26.2)",
    "IEE": "Indian Economic Enterprise Set-Aside",
    "ISBEE": "Indian Small Business Economic Enterprise Set-Aside",
    "BICiv": "Buy Indian Set-Aside",
    "VSA": "Veteran-Owned Small Business Set-Aside",
    "VSS": "Veteran-Owned Small Business Sole Source",
}

# ptype (procurement type) code -> meaning.
PROCUREMENT_TYPES: dict[str, str] = {
    "u": "Justification (J&A)",
    "p": "Pre-solicitation",
    "a": "Award Notice",
    "r": "Sources Sought",
    "s": "Special Notice",
    "o": "Solicitation",
    "g": "Sale of Surplus Property",
    "k": "Combined Synopsis/Solicitation",
    "i": "Intent to Bundle Requirements (DoD-Funded)",
}
