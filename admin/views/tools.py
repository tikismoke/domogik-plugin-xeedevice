# -*- coding: utf-8 -*-
from domogik.admin.application import app
from domogik.common.utils import get_sanitized_hostname

from domogikmq.reqrep.client import MQSyncReq
from domogikmq.message import MQMessage


def get_xeecar_info(abort=False):
    data = {u'status': u'dead', u'PYOZWLibVers': u'unknown', u'ConfigPath': u'undefined', 'uUserPath': u'not init',
            u'Options': {},
            u'error': u''}
    if not abort:
        print "########NO ABORT#########"
        cli = MQSyncReq(app.zmq_context)
        msg = MQMessage()
        msg.set_action('xeedevice.car.get')
        res = cli.request('plugin-xeedevice.{0}'.format(get_sanitized_hostname()), msg.get(), timeout=10)
        if res is not None:
            data = res.get_data()
        else:
            data['error'] = u'Plugin timeout response.'
        return data
    else:
        print "########ABORT#########"
