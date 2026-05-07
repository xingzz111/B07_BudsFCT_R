import time
import traceback
from mes.mes_client import MesClient


def check_sn(sn, publisher=None, **kwargs):

    _m_publish_exception = kwargs.get('m_publish_exception')

    _params = dict({'COMMAND': 'CheckData', 'SERIAL_NUMBER': sn})

    try:
        _result, _response, _error_msg, _total_time = MesClient(publisher).post('CheckData', _params)
        if _result:
            _result = _response.get('RESULT', 'FAIL')
            _result = True if (_result == 'OK' or _result == 'PASS') else False
            _result_info = _response.get('RESULT_INFO', '')
            return _result, _result_info
        else:
            _msg = 'Network anomaly'
            return _result, _msg

    except Exception as e:
        if _m_publish_exception:
            _m_publish_exception(str(e), format_exc=str(traceback.format_exc()), request_params=_params)
        return False, 'Service not available'
