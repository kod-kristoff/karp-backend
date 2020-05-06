from flask import Blueprint, jsonify  # pyre-ignore

# from karp import search
# import karp.domain.services.auth.auth as auth
from karp.application import ctx

stats_api = Blueprint("stats_api", __name__)


@stats_api.route("/<resource_id>/stats/<field>", methods=["GET"])
@ctx.auth_service.authorization("READ")
def get_field_values(resource_id, field):
    return jsonify(ctx.search_service.statistics(resource_id, field))
