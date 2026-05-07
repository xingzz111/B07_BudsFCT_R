#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
======================
@author:Zcnwei
@time:2024/3/25 22:32
=====================
"""

import json
import re
from rtrpcLib.common import Report


patt_skip = re.compile('(\w*)\-(\w*)\-(\w*)\s*\-\-\>\s*SKIP')
start_dict = {u"group": "", u"to_pdca": False, u"subsubtestname": "", u"description": "",
              u"dimension": "", u"tid": ""}
finish_dict = {u"group": "", u"to_pdca": False, u"subsubtestname": "",
               u"value": u"SKIP", u"result": 2, u"tid": ""}


class SequencerProtocol(object):
    @staticmethod
    def parse_report(msg):
        if 'data' in msg and 'event' in msg:
            report_dict = json.loads(msg)
            report = Report()
            report.event = report_dict['event']
            report.data = report_dict['data']
            return report
        else:
            # print('illegal report: {}'.format(msg))
            return None

    @staticmethod
    def create_skip_start_report(msg):
        items = patt_skip.findall(msg)
        if items and len(items[0]) == 3:
            group, tid, subsub = items[0]
            start_dict[u'group'] = group
            start_dict[u'tid'] = tid
            start_dict[u'subsubtestname'] = subsub
            start_report = Report()
            start_report.event = 2
            start_report.data = start_dict
            return start_report
        return None

    @staticmethod
    def create_skip_finish_report(msg):
        items = patt_skip.findall(msg)
        if items and len(items[0]) == 3:
            group, tid, subsub = items[0]
            finish_dict[u'group'] = group
            finish_dict[u'tid'] = tid
            finish_dict[u'subsubtestname'] = subsub
            finish_report = Report()
            finish_report.event = 3
            finish_report.data = finish_dict
            return finish_report
        return None


if __name__ == "__main__":
    msg = '{"data": {"tid": "HW_VER_PARSE", "to_pdca": false, "result": 2, "value": "SKIP"}, "event": 3}'
    print(json.loads(msg))
    print(SequencerProtocol.parse_report(msg))
    msg = u'WAKE_UP-Transition-00_Delay_500MS --> SKIP'
    print(SequencerProtocol.create_skip_finish_report(msg))
