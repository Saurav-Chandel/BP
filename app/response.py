from rest_framework.response import Response


class ResponseOk(Response):

    status_code = 200

    def __init__(self, data=None):
        if data is None:
            data = {"success": 1, "message": "OK", "status": 200}
        if isinstance(data, str):
            data = {"success": 1, "message": data, "status": 200}
        elif isinstance(data, dict):
            if "success" not in data.keys():
                data["success"] = 1
            if "status" not in data.keys():
                data["status"] = 200
            if "message" not in data.keys():
                data["message"] = "OK"
        super(ResponseOk, self).__init__(data, status=200)


class ResponseNotFound(Response):

    status_code = 404

    def __init__(self, data=None):
        if data is None:
            data = {"success": 0, "error": "Not found", "status": 404}
        if isinstance(data, str):
            data = {"success": 0, "error": data, "status": 404}
        elif isinstance(data, dict):
            if "success" not in data.keys():
                data["success"] = 0
            if "status" not in data.keys():
                data["status"] = 404
            if "error" not in data.keys():
                data["error"] = "Not found"
        super(ResponseNotFound, self).__init__(data, status=404)



class ResponseBadRequest(Response):

    status_code = 400

    def __init__(self, data=None):
        if data is None:
            data = {"success": 0, "error": "Bad Request", "status": 400}
        if isinstance(data, str):
            data = {"success": 0, "error": data, "status": 400}
        elif isinstance(data, dict):
            if "success" not in data.keys():
                data["success"] = 0
            if "status" not in data.keys():
                data["status"] = 400
            if "error" not in data.keys():
                data["error"] = "Bad Request"
        super(ResponseBadRequest, self).__init__(data, status=400)


