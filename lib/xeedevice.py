""" This file is part of B{Domogik} project (U{http://www.domogik.org}).

License
=======

B{Domogik} is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

B{Domogik} is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Domogik. If not, see U{http://www.gnu.org/licenses}.

Plugin purpose
==============

Plugin for NEST protect and thermostat

Implements
==========

class XEE, xeeException

@author: tikismoke
@copyright: (C) 2007-2016 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import traceback
import subprocess
try:
    from xee import Xee
    import xee.entities as xee_entities
except RuntimeError:
    self._log.debug(u"Error importing xee!")
import sys
import os
import pickle
import locale
import time

class xeeException(Exception):
    """
    XEE exception
    """
    def __init__(self, value):
        Exception.__init__(self)
        self.value = value

    def __str__(self):
        return repr(self.value)

class XEEclass:
    """
    Get informations about xee
    """
    # -------------------------------------------------------------------------------------------------
    def __init__(self, log, client_id, client_secret, redirect_url, period):
        try:
            """
            Create a xee instance, allowing to use XEE api
            """
            self._log = log
            self.client_id = client_id
            self.client_secret = client_secret
            self.redirect_url = redirect_url
            self.period = period
            self.xee = Xee(client_id = self.client_id,
			client_secret = self.client_secret,
		        redirect_uri = self.redirect_url)
            login_url = self.xee.get_authentication_url() + "&redirect_uri=" + self.redirect_url
            xee_config_file = os.path.join(os.path.dirname(__file__), '../data/xee_token.sav')
#	    self.open_token()
            try:
    	        with open(xee_config_file, 'r') as xee_token_file:
                    self._log.debug(u"Opening File")
                    self.token = pickle.load(xee_token_file)
                    self._log.debug(u"Getting user")
                    user ,error = self.xee.get_user(self.token.access_token)
                    if error != None :
                        self._log.warning(u"Error getting user, try refreshing with token_refresh from file")
                        self._log.warning(error)
                        self.token,error = self.xee.get_token_from_refresh_token(self.token.refresh_token)
                        if error != None :
                            self._log.error(u"Error getting user, from refresh token")
                            self._log.error(error)
                            sys.exit("refreshing token failed from refresh_token")
                            #TODO stop plugin
                        else :
                            self._log.warning(u"Token succesfully refresh with token_refresh from file")
                with open(xee_config_file, 'w') as xee_token_file:
                    pickle.dump(self.token, xee_token_file)

            except:
                self._log.error(u"Error with file saved or no file saved")
                self._log.error(u"Go to Advanced page to generate a new token file")
                #TODO stop plugin

        except ValueError:
            self._log.error(u"error reading Xee.")
            return

    def boolify(self, s):
        return (str)(s).lower() in['true' '1' 't' 'y' 'yes' 'on' 'enable'
                                   'enabled']
    
    def epoch2date(self, epoch):
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(epoch))

    def CtoF(self, t):
        return (t*9)/5+32


    # -------------------------------------------------------------------------------------------------
    def readXeeApiCar(self, carid):
        """
        read the xee api for car information
        """
        try:
            car ,error = self.xee.get_car(int(carid),self.token.access_token)
            if error == None :
                self._log.debug(car)
                return car
            else:
                self._log.debug(error)
                return "failed"
        except AttributeError:
            self._log.error(u"### Sensor '%s', ERROR while reading value." % sensor)
            return "failed"

    # -------------------------------------------------------------------------------------------------
    def readXeeApiStatus(self, carid):
        """
        read the xee api status information
        """
        try:
            carstatus ,error = self.xee.get_status(int(carid),self.token.access_token)
            if error == None :
                self._log.debug(carstatus)
                return carstatus
            else:
                self._log.debug(error)
                return "failed"
        except AttributeError:
            self._log.error(u"### Sensor '%s', ERROR while reading value." % sensor)
            return "failed"


    # -------------------------------------------------------------------------------------------------
    def loop_read_sensor(self, deviceid, devicename, device_type, carid, send, stop):
        """
        """
        while not stop.isSet():
            if device_type == "xee.car":
                val = self.readXeeApiCar(carid)
                if val != "failed":
                    send(deviceid, {'name': val.name, 'make': val.make, 'carid': val.id})
            elif device_type == "xee.car.status":
                val = self.readXeeApiStatus(carid)
                if val != "failed":
                    self._log.debug(val.signals)
                    speed = u''
                    odometer = u''
                    fuel_level = u''
                    battery_voltage = u''
                    position = u''
                    lock_status = u''
                    ignition_status = u''
                    for t in val.signals:
                        if t.name == "VehiculeSpeed":
                            speed = t.value
                        elif t.name == "Odometer":
                            odometer = t.value
                        elif t.name == "FuelLevel":
                            fuel_level = t.value
                        elif t.name == "BatteryVoltage":
                            battery_voltage = t.value
                        elif t.name == "LockSts":
                            lock_status = t.value
                        elif t.name == "IgnitionSts":
                            ignition_status = t.value
                    position = str(val.location.latitude) + "," + str(val.location.longitude)
                    send(deviceid, {'position' : position , 'fuel_level' : fuel_level, 'battery_voltage' : battery_voltage,
                                    'odometer' : odometer, 'speed' : speed, 'lock_status' : lock_status,
                                    'ignition_status' : ignition_status })
            
	    self._log.debug(u"=> '{0}' : wait for {1} seconds".format(devicename, self.period))
    	    stop.wait(self.period)
