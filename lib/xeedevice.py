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

Plugin for Xee connect car device

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
import datetime
import calendar

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
            self._sensors = []
            self.xee = Xee(client_id=self.client_id,
                           client_secret=self.client_secret,
                           redirect_uri=self.redirect_url)
            login_url = self.xee.get_authentication_url() + "&redirect_uri=" + self.redirect_url
            self.xee_config_file = os.path.join(os.path.dirname(__file__), '../data/xee_token.sav')
            self.open_token(self.xee)

        except ValueError:
            self._log.error(u"error reading Xee.")
            try:
                with open(xee_config_file, 'r') as xee_token_file:
                    self._log.debug(u"Opening File")
                    self.token = pickle.load(xee_token_file)
                    self._log.debug(u"Getting user")
                    user, error = self.xee.get_user(self.token.access_token)
                    if error != None:
                        self._log.warning(u"Error getting user, try refreshing with token_refresh from file")
                        self._log.warning(error)
                        self.token, error = self.xee.get_token_from_refresh_token(self.token.refresh_token)
                        if error != None:
                            self._log.error(u"Error getting user, from refresh token")
                            self._log.error(error)
                            sys.exit("refreshing token failed from refresh_token")
                            # TODO stop plugin
                        else:
                            self._log.warning(u"Token succesfully refresh with token_refresh from file")
                with open(xee_config_file, 'w') as xee_token_file:
                    pickle.dump(self.token, xee_token_file)

            except ValueError:
                self._log.error(u"error reading Xee.")
                return

    def open_token(self, xee):
        try:
            with open(self.xee_config_file, 'r') as xee_token_file:
                self._log.debug(u"Opening File")
                self.token = pickle.load(xee_token_file)
                self._log.debug(u"Getting user")
                user, error = xee.get_user(self.token.access_token)
                if error != None:
                    self._log.warning(u"Error getting user, try refreshing with token_refresh from file")
                    self._log.warning(error)
                    self.token, error = xee.get_token_from_refresh_token(self.token.refresh_token)
                    if error != None:
                        self._log.error(u"Error getting user, from refresh token")
                        self._log.error(error)
                        sys.exit("refreshing token failed from refresh_token")
                        # TODO stop plugin
                    else:
                        self._log.warning(u"Token succesfully refresh with token_refresh from file")
            with open(self.xee_config_file, 'w') as xee_token_file:
                pickle.dump(self.token, xee_token_file)

        except:
            self._log.error(u"Error with file saved or no file saved")
            self._log.error(u"Go to Advanced page to generate a new token file")
            # TODO stop plugin

    # -------------------------------------------------------------------------------------------------
    def add_sensor(self, device_id, device_name, device_type, sensor_carid):
        """
        Add a sensor to sensors list.
        """
        self._sensors.append({'device_id': device_id, 'device_name': device_name, 'device_type': device_type,
                              'sensor_carid': sensor_carid})

    # -------------------------------------------------------------------------------------------------
    def readXeeApiCar(self, carid):
        """
        read the xee api for car information
        """
        try:
            car, error = self.xee.get_car(int(carid), self.token.access_token)
            if error == None:
                self._log.debug(car)
                return car
            else:
                self._log.debug(error)
                return "failed"
        except AttributeError:
            self.open_token()
            self._log.error(u"### Car Id '%s', ERROR while reading car." % carid)
            return "failed"

    # -------------------------------------------------------------------------------------------------
    def readXeeApiStatus(self, carid):
        """
        read the xee api status information
        """
        try:
            carstatus, error = self.xee.get_status(int(carid), self.token.access_token)
            if error == None:
                self._log.debug(carstatus)
                return carstatus
            else:
                self._log.debug(error)
                return "failed"
        except AttributeError:
            self.open_token()
            self._log.error(u"### Car Id '%s', ERROR while reading car status." % carid)
            return "failed"

    # -------------------------------------------------------------------------------------------------
    def loop_read_sensor(self, send, send_sensor, stop):
        """
        """
        while not stop.isSet():
            try:  # catch error if self._sensors modify during iteration
                for sensor in self._sensors:
                    if sensor['device_type'] == "xee.car":
                        val = self.readXeeApiCar(sensor['sensor_carid'])
                        if val != "failed":
# TODO to remove send
#                            name = u''
#                            make = u''
#                            carid = u''
#                            for sensor in val:
#				print sensor
#                                if sensor.name == "name":
#                                    name = sensor.value
##	                            send_sensor(sensor['device_id'],'name', name)
#                                elif sensor.name == "make":
#                                    make = sensor.value
#	                            send_sensor(sensor['device_id'],'make', make)
#                                elif sensor.name == "id":
#                                    carid = sensor.value
#	                            send_sensor(sensor['device_id'],'carid', carid)
                            send(sensor['device_id'], {'name': val.name, 'make': val.make, 'carid': val.id})
                    elif sensor['device_type'] == "xee.car.status":
                        val = self.readXeeApiStatus(sensor['sensor_carid'])
                        if val != "failed":
                            self._log.debug(val.signals)
                            position = u''
                            for sensors in val.signals:
                                sensor_name = u''
                                if sensors.name == "VehiculeSpeed":
                                    sensor_name = "speed"
                                elif sensors.name == "Odometer":
                                    sensor_name = "odometer"
                                elif sensors.name == "FuelLevel":
                                    sensor_name = "fuel_level"
                                elif sensors.name == "BatteryVoltage":
                                    sensor_name = "battery_voltage"
                                elif sensors.name == "LockSts":
                                    sensor_name = "lock_status"
                                elif sensors.name == "IgnitionSts":
                                    sensor_name = "ignition_status"
                                elif sensors.name == "HeadLightSts":
                                    sensor_name = "headlight_status"
                                elif sensors.name == "HighBeamSts":
                                    sensor_name = "highbeam_status"
                                elif sensors.name == "LowBeamSts":
                                    sensor_name = "lowbeam_status"
                                if sensor_name != u'':
                                    timestamp = calendar.timegm(sensors.date.timetuple())
                                    send_sensor(sensor['device_id'], sensor_name, sensors.value, timestamp)
                            position = str(val.location.latitude) + "," + str(val.location.longitude)
                            if position != u'':
                                timestamp = calendar.timegm(val.location.date.timetuple())
                                send_sensor(sensor['device_id'],'position', position, timestamp)
                        self._log.debug(u"=> '{0}' : wait for {1} seconds".format(sensor['device_name'], self.period))
            except:
                self._log.error(u"# Loop_read_sensors EXCEPTION")
                pass
            stop.wait(self.period)
