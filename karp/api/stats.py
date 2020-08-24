from flask import Blueprint, jsonify  # pyre-ignore

from karp.application import context
import karp.auth.auth as auth

stats_api = Blueprint("stats_api", __name__)


@stats_api.route("/<resource_id>/stats/<field>", methods=["GET"])
@auth.auth.authorization("READ")
def get_field_values(resource_id: str, field: str):
    return jsonify(context.search_index.statistics(resource_id, field))
