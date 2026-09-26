# Re-export review creation from orders for clarity; primary API is create_review.
from apps.orders.services import create_review

__all__ = ["create_review"]
