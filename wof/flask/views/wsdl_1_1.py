from flask import (Flask, request, Markup, Response, render_template,
                   make_response, Module, current_app)

try:
    from flask import Blueprint
    wsdl = Blueprint(__name__, __name__)
except ImportError:
    wsdl = Module(__name__)


@wsdl.route('/soap/wateroneflow_1_1.wsdl')
def get_wsdl():
#TODO: The WSDL should be served separately from the Flask application.
# Come up with a better way to do this.
    network = current_app.wof_inst.network.lower()

    try:
       serv_loc = current_app.config['SOAP_SERVICE_URL']
    except KeyError:
        serv_loc = current_app.config.get(
            'SOAP_SERVICE_URL',
            '%s/wateroneflow/1_1/' % request.url.rsplit('/', 1)[0])

    response = make_response(render_template('wsdl_1_1_template.wsdl',
                                             serv_loc=serv_loc,
                                             network=network))

    response.headers['Content-Type'] = 'text/xml'

    return response
