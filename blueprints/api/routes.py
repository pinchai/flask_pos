import os
from flask import request
from flask_restx import Resource
from . import api

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@api.route("/users/<int:user_id>/<string:name>")
class UserList(Resource):
    def get(self, user_id=None, name=None):
        return [{"id": user_id, "name": name}]


@api.route("/students")
class StudentList(Resource):

    @api.doc(params={
        "page": {
            "description": "Page number",
            "type": "integer",
            "location": "args",
            "default": 1
        },
        "per_page": {
            "description": "Items per page",
            "type": "integer",
            "location": "args",
            "default": 20
        },
        "keyword": {
            "description": "Search keyword",
            "type": "string",
            "location": "args"
        }
    })
    def get(self):
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)
        keyword = request.args.get("keyword", "", type=str)

        return {
            "page": page,
            "per_page": per_page,
            "keyword": keyword
        }

    @api.doc(
        consumes=["multipart/form-data"],
        params={
            "name": {
                "in": "formData",
                "type": "string",
                "required": True,
                "description": "Student name"
            },
            "email": {
                "in": "formData",
                "type": "string",
                "required": True,
                "description": "Student email"
            },
            "photo": {
                "in": "formData",
                "type": "file",
                "required": True,
                "description": "Student photo"
            }
        }
    )
    def post(self):
        name = request.form.get("name")
        email = request.form.get("email")
        photo = request.files.get("photo")

        filename = None

        if photo:
            filename = photo.filename
            photo.save(os.path.join(UPLOAD_FOLDER, filename))

        return {
            "message": "Student created",
            "name": name,
            "email": email,
            "photo": filename
        }, 201
