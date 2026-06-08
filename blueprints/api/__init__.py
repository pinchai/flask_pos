from flask import Blueprint
from flask_restx import Api

api_bp = Blueprint('api', __name__)

authorizations = {
    'apikey': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'Authorization',
        'description': 'Type in the input box: Bearer &lt;JWT_TOKEN&gt;'
    }
}

api = Api(
    api_bp,
    title="Sample POS System REST API Docs",
    version="1.0",
    description="Interactive Swagger API Documentation for all modules (Users, Shops, Categories, Products, Payment Methods, and Sales)",
    doc="/docs",
    authorizations=authorizations,
    security='apikey'
)

from . import routes
