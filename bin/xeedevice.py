#!/usr/bin/python
# -*- coding: utf-8 -*-


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

Plugin for Xee connect car cloud api

Implements
==========


@author: tikismoke  (new dt domodroid at gmail dt com)
@copyright: (C) 2007-2016 Domogik project
@license: GPL(v3)
@organization: Domogik
"""
from domogik.common.plugin import Plugin
from domogikmq.message import MQMessage

from domogik_packages.plugin_xeedevice.lib.xeedevice import xeeException
from domogik_packages.plugin_xeedevice.lib.xeedevice import XEEclass

import threading
import time
import json


class xeeManager(Plugin):
    # -------------------------------------------------------------------------------------------------
    def __init__(self):
        """
            Init plugin
        """
        Plugin.__init__(self, name='xeedevice')

        # check if the plugin is configured. If not, this will stop the plugin and log an error
        if not self.check_configured():
            return

        # ### get all config keys
        client_id = str(self.get_config('client_id'))
        client_secret = str(self.get_config('client_secret'))
        redirect_url = str(self.get_config('redirect_url'))
        period = int(self.get_config('period'))

        # ### get the devices list
        # for this plugin, if no devices are created we won't be able to use devices.
        self.devices = self.get_device_list(quit_if_no_device=False)
        self.log.info(u"==> device:   %s" % format(self.devices))

        # get the sensors id per device :
        self.sensors = self.get_sensors(self.devices)
        self.log.info(u"==> sensors:   %s" % format(self.sensors))

        # ### Open the XEE lib
        try:
            self.XEEclass = XEEclass(self.log, client_id, client_secret, redirect_url, period)
        except xeeException as e:
            self.log.error(e.value)
            self.force_leave()
            return

        # ### For each device
        self.device_list = {}
        thread_sensors = None
        for a_device in self.devices:
            device_name = a_device["name"]
            device_id = a_device["id"]
            device_type = a_device["device_type_id"]
            sensor_carid = self.get_parameter(a_device, "carid")
            self.device_list.update({device_id: {'name': device_name, 'named': sensor_carid}})
            self.log.info(
                u"==> Device '{0}' (id:{1}/{2}), name = {3}".format(device_name, device_id, device_type, sensor_carid))
            self.log.debug(u"==> Sensor list of device '{0}': '{1}'".format(device_id, self.sensors[device_id]))
            self.XEEclass.add_sensor(device_id, device_name, device_type, sensor_carid)

        thread_sensors = threading.Thread(None,
                                          self.XEEclass.loop_read_sensor,
                                          'Main_reading_sensors',
                                          (self.send_pub_data, self.get_stop()),
                                          {})
        thread_sensors.start()
        self.register_thread(thread_sensors)
        self.ready()

    # -------------------------------------------------------------------------------------------------
    def send_pub_data(self, device_id, value):
        """ Send the sensors values over MQ
        """
        self.log.debug(u"send_pub_data : '%s' for device_id: '%s' " % (value, device_id))
        data = {}
        value_dumps = json.dumps(value)
        value_dict = json.loads(value_dumps)
        for sensor in self.sensors[device_id]:
            self.log.debug(u"value receive : '%s' for sensors: '%s' " % (value_dict[sensor], sensor))
            data[self.sensors[device_id][sensor]] = value_dict[sensor]
        self.log.debug(u"==> Update Sensor '%s' for device id %s (%s)" % (
            format(data), device_id, self.device_list[device_id]["name"]))  # {u'id': u'value'}

        try:
            self._pub.send_event('client.sensor', data)
        except:
            # We ignore the message if some values are not correct
            self.log.debug(u"Bad MQ message to send.MQ data is : {0}".format(data))
            pass


if __name__ == "__main__":
    xeeManager()
