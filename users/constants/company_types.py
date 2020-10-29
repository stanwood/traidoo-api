COMPANY_TYPES = {  # TODO: it would be better to store integers in DB
    "Natural": (("Einzelunternehmer", "Einzelunternehmer"),),
    "Agrarian Sole Trader": (("Landwirtschaftliche GbR", "Landwirtschaftliche GbR"),),
    "Soletrader": (("Gewerbliche GbR", "Gewerbliche GbR"),),
    "Companies": (
        ("eG", "eG"),
        ("KG", "KG"),
        ("AG", "AG"),
        ("GmbH", "GmbH"),
        ("GmbH & Co. KG", "GmbH & Co. KG"),
        ("UG (haftungsbeschränkt)", "UG (haftungsbeschränkt)"),
        ("OHG", "OHG"),
        ("Kollektivgesellschaft", "Kollektivgesellschaft"),
        ("Kommanditgesellschaft", "Kommanditgesellschaft"),

    ),
    "Organisations": (
        ("e.V.", "e.V."),
        ("Genossenschaft", "Genossenschaft"),
        ("Verein", "Verein")
    ),
}
