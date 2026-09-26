from typing import cast

from rest_framework import generics, permissions

from apps.accounts.models import User
from apps.accounts.serializers import UserSerializer


class MeView(generics.RetrieveUpdateAPIView):
    """Read or update the authenticated user's own profile.

    The object comes from the session, never from a client-supplied id.
    """

    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self) -> User:
        return cast(User, self.request.user)
