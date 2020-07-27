from model_bakery.recipe import Recipe

from documents.models import Document

order_confirmation = Recipe(
    Document, document_type=Document.TYPES.get_value("order_confirmation_buyer")
)
