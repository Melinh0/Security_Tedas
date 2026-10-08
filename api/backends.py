from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

from . import encryption

UserModel = get_user_model()


class EncryptedUsernameBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)
        if username is None or password is None:
            return None
        try:
            user = UserModel._default_manager.get(
                username_index=encryption.blind_index(username)
            )
        except UserModel.DoesNotExist:
            UserModel().set_password(password)
            return None
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
