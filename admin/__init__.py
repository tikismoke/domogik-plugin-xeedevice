# -*- coding: utf-8 -*-

### common imports
from flask import Blueprint, abort
from domogik.common.utils import get_packages_directory
from domogik.admin.application import render_template
from domogik.admin.views.clients import get_client_detail
from jinja2 import TemplateNotFound
import traceback
import sys

### package specific imports
import subprocess
import os
import pickle
import datetime
import time
#from domogik.common.utils import get_data_files_directory_for_plugin
from flask_wtf import Form
from wtforms import StringField

from flask import request, flash

try:
    from flask.ext.babel import gettext, ngettext
except ImportError:
    from flask_babel import gettext, ngettext
    pass

### plugin specific imports
from xee import Xee
import xee.entities as xee_entities

#TODO
#from domogik_packages.plugin_xeedevice.bin.xeedevice import TOKEN_SAV
#import domogik_packages.plugin_xeedevice.bin.xeedevice as xeedevice
#from domogik.common.plugin import Plugin
#from domogikmq.message import MQMessage
#import zmq

from domogikmq.reqrep.client import MQSyncReq
from domogikmq.message import MQMessage
from domogik.admin.application import app
from domogik.common.utils import get_sanitized_hostname

### package specific functions

def get_token_link(xee_client_id,xee_client_secret,xee_redirect_url):
    xee = Xee(client_id = xee_client_id,
              client_secret = xee_client_secret,
              redirect_uri = xee_redirect_url)
    login_url = xee.get_authentication_url() + "&redirect_uri=" + xee_redirect_url
    login_url = unicode(login_url, 'utf-8')
    return login_url

def generate_token_file(authorization_code,xee_client_id,xee_client_secret,xee_redirect_url):
    xee = Xee(client_id = xee_client_id,
              client_secret = xee_client_secret,
              redirect_uri = xee_redirect_url)
    token , error = xee.get_token_from_code(authorization_code)
    if error != None :
        flash(gettext(u"Error while getting token from Xee code check you client id/secret redirect url or code"),"error")
    else:
        with open(xee_config_file, 'w') as xee_token_file:
            pickle.dump(token, xee_token_file)
            flash(gettext(u"Successfully generate token. Please restart the plugin."), "success")


def get_car_list(client_id,client_secret,redirect_url):
    try:
        xee = Xee(client_id = client_id,
                        client_secret = client_secret,
                        redirect_uri = redirect_url)
        with open(xee_config_file, 'r') as xee_token_file:
            token = pickle.load(xee_token_file)
            cars ,error = xee.get_cars(token.access_token)
            if error != None:
                error_string = str(error)
                return error
            else :
                return cars
#                return_car =""
#                for car in cars:
#                    car_id = str(car.id)
#                    car_name = car.name
#                    return_car += "CarId: " + car_id + " for car Name: " + car_name +"\n"
#                    cars_string = str(return_car)
#                return cars_string
    except:
        return "Error"

def show_current_token():
    try:
        with open(xee_config_file, 'r') as xee_token_file:
            token = pickle.load(xee_token_file)
            this_token = token.access_token
            this_refresh_token = token.refresh_token
            this_token_expires = str(datetime.datetime.fromtimestamp(token.expires_at))
            this_token = str("Token = " + this_token + "\n" )
            this_refresh_token = str("Refresh token = " + this_refresh_token + "\n" )
            this_token_expires = str("Expires on = " + this_token_expires + "\n")
            result = this_token + this_refresh_token + this_token_expires
        return result
    except:
        return "Error"

def get_info_from_log(cmd):
    print("Command = %s" % cmd)
    error_log_process = subprocess.Popen([cmd], stdout=subprocess.PIPE)
    output = error_log_process.communicate()[0]
    if isinstance(output, str):
        output = unicode(output, 'utf-8')
    return output

def get_position(client_id,client_secret,redirect_url):
    try:
        xee = Xee(client_id = client_id,
                        client_secret = client_secret,
                        redirect_uri = redirect_url)
        with open(xee_config_file, 'r') as xee_token_file:
            token = pickle.load(xee_token_file)
            locations ,error = xee.get_locations("14113",token.access_token,limit=10)
            if error != None:
                error_string = str(error)
                return error
            else :
                return_location =""
                data = {}
                cli = MQSyncReq(app.zmq_context)
                msg = MQMessage()
                for location in locations:
                    lat = str(location.latitude)
                    lon = str(location.longitude)
                    date = str(location.date)
                    date = date[:19]
                    timestamp = time.mktime(datetime.datetime.strptime(date, "%Y-%m-%d %H:%M:%S" ).timetuple())
                    position = str( lat + ":" + lon)
                    return_location += str ("Lat: " + lat + " Lon: " + lon + " date: " + date + " timestamp: " + str(timestamp) + "\n")
                    msg.set_action('client.sensor')
                    msg.add_data('sensor_id', 1841)
                    msg.add_data('value', position)
                    msg.add_data('atTimestamp', timestamp)
                    print (msg.get())
                    print (cli.request('xplgw', msg.get(), timeout=10))
#			data['1830'] = position
#			data['atTimestamp'] = timestamp
#			Plugin._pub.send_event('client.sensor', data)
                locations_string = str(return_location)
                return locations_string
    except:
        return "Error"    

class CodeForm(Form):
    code = StringField("code")

### common tasks
package = "plugin_xeedevice"
template_dir = "{0}/{1}/admin/templates".format(get_packages_directory(), package)
static_dir = "{0}/{1}/admin/static".format(get_packages_directory(), package)
geterrorlogcmd = "{0}/{1}/admin/geterrorlog.sh".format(get_packages_directory(), package)

#TODO
#xee_config_file = os.path.join(get_data_files_directory_for_plugin("xeedevice"), TOKEN_SAV)
xee_config_file = os.path.join(os.path.dirname(__file__), '../data/xee_token.sav')


plugin_xeedevice_adm = Blueprint(package, __name__,
                        template_folder = template_dir,
                        static_folder = static_dir)


@plugin_xeedevice_adm.route('/<client_id>', methods = ['GET', 'POST'])
def index(client_id):
    detail = get_client_detail(client_id)
    form = CodeForm()
    xee_client_id = str(detail['data']['configuration'][1]['value'])
    xee_client_secret = str(detail['data']['configuration'][2]['value'])
    xee_redirect_url = str(detail['data']['configuration'][3]['value'])
    information = ''

    if request.method == "POST":
        generate_token_file(form.code.data,xee_client_id,xee_client_secret,xee_redirect_url)
	information = get_position(xee_client_id,xee_client_secret,xee_redirect_url)
    try:
        return render_template('plugin_xeedevice.html',
            clientid = client_id,
            client_detail = detail,
            mactive = "clients",
            active = 'advanced',
            get_token_url = get_token_link(xee_client_id,xee_client_secret,xee_redirect_url),
            form = form,
            car_id = get_car_list(xee_client_id,xee_client_secret,xee_redirect_url),
            current_token = show_current_token(),
            errorlog = get_info_from_log(geterrorlogcmd),
	    information = information)

    except TemplateNotFound:
        abort(404)

@plugin_xeedevice_adm.route('/<client_id>/import', methods = ['GET', 'POST'])
def mass_import(client_id):
    detail = get_client_detail(client_id)
    form = CodeForm()
    xee_client_id = str(detail['data']['configuration'][1]['value'])
    xee_client_secret = str(detail['data']['configuration'][2]['value'])
    xee_redirect_url = str(detail['data']['configuration'][3]['value'])
    mass_import_position = ''

    if request.method == "POST":
	mass_import_position = get_position(xee_client_id,xee_client_secret,xee_redirect_url)

    try:
        return render_template('import.html',
            clientid = client_id,
            client_detail = detail,
            mactive = "clients",
            active = 'advanced',
            mass_import_position = mass_import_position,
            form = form)

    except TemplateNotFound:
        abort(404)

