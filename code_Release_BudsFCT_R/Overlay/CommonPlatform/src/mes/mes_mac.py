from prmcommon import constant
from mes.mes_client import MesClient


def get_mac_by_sn(sn, publisher=None):
    _params = dict({'TCMD': 'GET_BS_MACCODE', 'SN': sn, 'TYPE': '0', 'TSID': constant.TERMINAL_NAME,
                    'EMPNO': '12279395'})

    print('get_mac_by_sn-_params:{}'.format(_params))
    try:
        _result, _response, _error_msg, _total_time = MesClient(publisher, 'param').post('GetMACBySN', _params)
        print("get_sn_get_sn",_result, _response, _error_msg, _total_time)
        # OK 返回"{\"Result\": \"OK\",\"Info\":\"SN=GFH95250LH6EML;MACCODE=D812659917E9; LICENSE_KEY=[ 27 6C…]\"}";
        # NG 返回"{\"Result\": \"NG\",\"Info\":\"MAC CODE Type is Error\"}";
        if _result:
            _result = _response.get('Result', 'NG')
            _result = True if (_result == 'OK' or _result == 'PASS') else False
            _result_info = _response.get('Info', '')
            return _result, _result_info
        else:
            return _result, 'Network anomaly'
    except Exception as e:
        return False, 'Service not available'

