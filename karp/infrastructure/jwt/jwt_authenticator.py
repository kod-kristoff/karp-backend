from karp.infrastructure.unit_of_work import unit_of_work
import jwt
import time
import jwt.exceptions as jwte  # pyre-ignore

from .authenticator import Authenticator
from karp import get_resource_string
from karp.auth.user import User
import karp.resourcemgr as resourcemgr
from karp.errors import KarpError, ClientErrorCodes

from karp import schemas
from karp.application import ctx

jwt_key = get_resource_string("auth/pubkey.pem")


class JWTAuthenticator(Authenticator):
    def authenticate(self, _auth_scheme: str, auth_token: str):
        if auth_token:
            try:
                user_token = jwt.decode(auth_token, key=jwt_key, algorithms=["RS256"])
            except jwte.ExpiredSignatureError:
                raise KarpError(
                    "The given jwt have expired", ClientErrorCodes.EXPIRED_JWT
                )

            # TODO check code, but this should't be needed since it seems like the JWT-lib checks expiration
            if user_token["exp"] < time.time():
                raise KarpError(
                    "The given jwt have expired", ClientErrorCodes.EXPIRED_JWT
                )

            lexicon_permissions = {}
            if "scope" in user_token and "lexica" in user_token["scope"]:
                lexicon_permissions = user_token["scope"]["lexica"]
            return User(user_token["sub"], lexicon_permissions, user_token["levels"])

        return None

    def authorize(self, level: schemas.PermissionLevel, user, args):
        if "resource_id" in args:
            resource_ids = [args["resource_id"]]
        elif "resource_ids" in args:
            resource_ids = args["resource_ids"].split(",")
        elif "resources" in args:
            resource_ids = args["resources"].split(",")
        else:
            return True

        with unit_of_work(using=ctx.resource_repository) as uw:
            for resource_id in resource_ids:
                resource = uw.get_by_resource_id(resource_id)
                if resource.is_protected(level) and (
                    (
                        not user
                        or not user.permissions.get(resource_id)
                        or user.permissions[resource_id] < user.levels[level]
                    )
                ):
                    return False
        return True
