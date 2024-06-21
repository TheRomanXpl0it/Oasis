import werkzeug
from flask import jsonify, request
from functools import wraps


def need_args(*needed_args_list):
    def real_decorator(func):
        @wraps(func)
        def inner(*args, **kws):
            try:
                posted_json = request.get_json()
            except werkzeug.exceptions.BadRequest:
                return jsonify({"status": 400, "addition": {"error": "Args would be in json format"}})
            if posted_json is None:
                return jsonify({"status": 400, "addition": {"error": "Args would be in json format"}})
            kwargs = {}
            for key in needed_args_list:
                try:
                    if key == 'addition':
                        kwargs[key] = posted_json[key]
                    else:
                        kwargs[key] = posted_json["addition"][key]
                except KeyError:
                    return jsonify({"status": 400, "addition": {"error": "Wrong args"}})
            return func(**kwargs)
        return inner
    return real_decorator