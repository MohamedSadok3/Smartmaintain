from flask import jsonify, request


def get_json_body():
    return request.get_json(silent=True) or {}


def json_error(message, status=400):
    return jsonify({"error": message}), status


def json_response(data, status=200):
    return jsonify(data), status
