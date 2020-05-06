from karp.domain.model.user import User


class Authenticator:
    def authenticate(self, request):
        return User("dummy", {}, {})

    def authorize(self, level, user, args):
        return True
