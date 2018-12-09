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

import subprocess
import traceback

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
import pytz


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
    def __init__(self, log, client_id, client_secret, redirect_url, period, speed_period, dataPath):
        try:
            """
            Create a xee instance, allowing to use XEE api
            """
            self._log = log
            self.client_id = client_id
            self.client_secret = client_secret
            self.redirect_url = redirect_url
            self.period = period
	    self.saved_period = period
	    self.speed_period = speed_period
            self._sensors = []
            self._dataPath = dataPath
            self.xee = Xee(client_id=self.client_id,
                           client_secret=self.client_secret,
                           redirect_uri=self.redirect_url)
            if not os.path.exists(self._dataPath):
                self._log.info(u"Directory data not exist, trying create : %s", self._dataPath)
                try:
                    os.mkdir(self._dataPath)
                    self._log.info(u"Xee data directory created : %s" % self._dataPath)
                except Exception as e:
                    self._log.error(e.message)
                    raise xeeException("Xee data directory not exist : %s" % self._dataPath)
            if not os.access(self._dataPath, os.W_OK):
                self._log.error("User %s haven't write access on data directory : %s" % (user, self._dataPath))
                raise xeeException("User %s haven't write access on data directory : %s" % (user, self._dataPath))

            self.xee_config_file = os.path.join(os.path.dirname(__file__), '../data/xee_token.sav')
            self.open_token(self.xee)

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
                if error is not None:
                    self._log.warning(u"Error getting user, try refreshing with token_refresh from file")
                    self._log.warning(error)
                    self.token, error = self.xee.get_token_from_refresh_token(self.token.refresh_token)
                    if error is not None:
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
            if error is not None:
                self._log.debug(error)
                self.open_token(self.xee)
                return "failed"
            else:
                #                self._log.debug(car)
                return car
        except AttributeError:
            self._log.error(u"### Car Id '%s', ERROR while reading car." % carid)
        except:
            self._log.error(u"Xee Exception : {0}".format(traceback.format_exc()))
            #        finally :
            self.open_token(self.xee)
            #            return "failed"

    # -------------------------------------------------------------------------------------------------
    def readXeeApiSignals(self, carid, begindate):
        """
        read the xee api status information
        """
        try:
#            carsignals, error = self.xee.get_signals(int(carid), self.token.access_token, begin=begindate)
            carsignals, error = self.xee.get_status(int(carid), self.token.access_token)
            if error is not None:
                self.open_token(self.xee)
                self._log.debug(error)
                return "failed"
            else:
                #                self._log.debug(carsignals)
                return carsignals
        except AttributeError:
            self._log.error(u"### Car Id '%s', ERROR while reading car status." % carid)
        except:
            self._log.error(u"Xee Exception : {0}".format(traceback.format_exc()))
            #	finally :
            self.open_token(self.xee)
            #            return "failed"

    # -------------------------------------------------------------------------------------------------
    def readXeeApiPosition(self, carid, begindate):
        """
        read the xee api status information
        """
        try:
            position, error = self.xee.get_locations(int(carid), self.token.access_token, begin=begindate)
            if error is not None:
                self.open_token(self.xee)
                self._log.debug(error)
                return "failed"
            else:
                #                self._log.debug(position)
                return position
        except AttributeError:
            self._log.error(u"### Car Id '%s', ERROR while reading car status." % carid)
        except:
            self._log.error(u"Xee Exception : {0}".format(traceback.format_exc()))
            #	finally :
            self.open_token(self.xee)
            #            return "failed"

    # -------------------------------------------------------------------------------------------------
    def loop_read_sensor(self, send_sensor, stop):
        """
        """
        while not stop.isSet():
            try:  # catch error if self._sensors modify during iteration
                for sensor in self._sensors:
                    if sensor['device_type'] == "xee.information":
                        val = self.readXeeApiCar(sensor['sensor_carid'])
                        if val is not None:
                            send_sensor(sensor['device_id'], 'name', val.name, None)
                            send_sensor(sensor['device_id'], 'make', val.make, None)
                            send_sensor(sensor['device_id'], 'carid', val.id, None)
                    elif sensor['device_type'] == "xee.location":
                        now = datetime.datetime.now(pytz.utc)
                        today = datetime.datetime(now.year, now.month, now.day, now.hour, now.minute, now.second,
                                                  tzinfo=pytz.utc)
                        begin = today - datetime.timedelta(seconds=self.period)
                        val = self.readXeeApiPosition(sensor['sensor_carid'], begin)
                        if val is not None:
                            for locations in val:
			        location = u''
	                        location = str(locations.latitude) + "," + str(locations.longitude)
                                if location != u'':
                                    timestamp = calendar.timegm(locations.date.timetuple())
                                    send_sensor(sensor['device_id'], 'location', location, timestamp)
                    else:
                        now = datetime.datetime.now(pytz.utc)
                        today = datetime.datetime(now.year, now.month, now.day, now.hour, now.minute, now.second,
                                                  tzinfo=pytz.utc)
                        begin = today - datetime.timedelta(seconds=self.period)
                        val = self.readXeeApiSignals(sensor['sensor_carid'], begin)
                        if val is not None:
#                            self._log.debug(val)
                            position = u''
                            for sensors in val.signals:
                                sensor_name = u''
                                if sensor['device_type'] == "xee.status":
				    # XeeCONNECT
                                    if sensors.name == "BatteryVoltage":
                                        sensor_name = "battery_voltage"
				if sensor['device_type'] == "xee.lights":
                                    # Lights
                                    if sensors.name == "FrontFogLightSts":
                                        sensor_name = "front_fog_light_status"
                                    elif sensors.name == "RearFogLightSts":
                                        sensor_name = "rear_fog_light_status"
                                    elif sensors.name == "HazardSts":
                                        sensor_name = "hazard_status"
                                    elif sensors.name == "HeadLightSts":
                                        sensor_name = "head_light_status"
                                    elif sensors.name == "HighBeamSts":
                                        sensor_name = "high_beam_status"
                                    elif sensors.name == "LowBeamSts":
                                        sensor_name = "low_beam_status"
                                    elif sensors.name == "LeftIndicatorSts":
                                        sensor_name = "left_indicator_status"
                                    elif sensors.name == "RightIndicatorSts":
                                        sensor_name = "right_indicator_status"
                                if sensor['device_type'] == "xee.status":
                                    # Misc
                                    if sensors.name == "FuelLevel":
                                        sensor_name = "fuel_level"
                                    elif sensors.name == "IgnitionSts":
                                        sensor_name = "ignition_status"
                                	if sensors.value == 1:
	                            	    self.period = self.speed_period
                                    	    self._log.debug(u"moteur on")
                                        else :
                                	    self.period = self.saved_period
                            		    self._log.debug(u"moteur off")
                                    elif sensors.name == "Odometer":
                                        sensor_name = "odometer"
                                    elif sensors.name == "LockSts":
                                        sensor_name = "lock_status"
                                if sensor['device_type'] == "xee.status.full":
				    # XeeCONNECT
                                    if sensors.name == "BatteryVoltage":
                                        sensor_name = "battery_voltage"
                                    # Misc
                                    elif sensors.name == "FuelLevel":
                                        sensor_name = "fuel_level"
                                    elif sensors.name == "IgnitionSts":
                                        sensor_name = "ignition_status"
                                	if sensors.value == 1:
	                            	    self.period = self.speed_period
                                    	    self._log.debug(u"moteur on")
                                        else :
                                	    self.period = self.saved_period
                            		    self._log.debug(u"moteur off")
                                    elif sensors.name == "Odometer":
                                        sensor_name = "odometer"
                                    elif sensors.name == "LockSts":
                                        sensor_name = "lock_status"
                                    # Speed
                                    elif sensors.name == "EngineSpeed":
                                        sensor_name = "engine_speed"
                                    elif sensors.name == "VehiculeSpeed":
                                        sensor_name = "vehicle_speed"
                                    # Computed
                                    elif sensors.name == "ComputedFuelLevel":
                                        sensor_name = "computed_fuel_level"
                                if sensor['device_type'] == "xee.status.simple":
				    # XeeCONNECT
                                    if sensors.name == "BatteryVoltage":
                                        sensor_name = "battery_voltage"
                                    # Misc
                                    elif sensors.name == "FuelLevel":
                                        sensor_name = "fuel_level"
                                    elif sensors.name == "IgnitionSts":
                                        sensor_name = "ignition_status"
                                	if sensors.value == 1:
	                            	    self.period = self.speed_period
                                    	    self._log.debug(u"moteur on")
                                        else :
                                	    self.period = self.saved_period
                            		    self._log.debug(u"moteur off")
                                    elif sensors.name == "Odometer":
                                        sensor_name = "odometer"
                                    elif sensors.name == "LockSts":
                                        sensor_name = "lock_status"
                                if sensor['device_type'] == "xee.wippers":
                                    # Wipers
                                    if sensors.name == "IntermittentWiperSts":
                                        sensor_name = "intermittent_wiper_status"
                                    elif sensors.name == "ManualWiperSts":
                                        sensor_name = "manual_wiper_status"
                                    elif sensors.name == "LowSpeedWiperSts":
                                        sensor_name = "low_speed_wiper_status"
                                    elif sensors.name == "HighSpeedWiperSts":
                                        sensor_name = "high_speed_wiper_status"
                                    elif sensors.name == "AutoRearWiperSts":
                                        sensor_name = "auto_rear_wiper_status"
                                    elif sensors.name == "ManualRearWiperSts":
                                        sensor_name = "manual_rear_wiper_status"
                                if sensor['device_type'] == "xee.status":
                                    # Speed
                                    if sensors.name == "EngineSpeed":
                                        sensor_name = "engine_speed"
                                    elif sensors.name == "VehiculeSpeed":
                                        sensor_name = "vehicle_speed"
                                    # Computed
                                    elif sensors.name == "ComputedFuelLevel":
                                        sensor_name = "computed_fuel_level"
                                if sensor_name != u'':
                                    timestamp = calendar.timegm(sensors.date.timetuple())
                                    send_sensor(sensor['device_id'], sensor_name, sensors.value, timestamp)
                    self._log.debug(u"=> '{0}' : wait for {1} seconds".format(sensor['device_name'], self.period))
            except Exception, e:
                self._log.error(u"# Loop_read_sensors EXCEPTION: {0}".format(traceback.format_exc()))
                pass
            stop.wait(self.period)
