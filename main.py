from flask import Flask
from flask_restful import Api

from routes import route
from mail_helper import init_mail


application = Flask(__name__)
api = Api(application)
route(api)
init_mail(application)

@application.after_request
def apply_origin(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

if '__main__' == __name__:
    application.run(host='0.0.0.0', port=80)
