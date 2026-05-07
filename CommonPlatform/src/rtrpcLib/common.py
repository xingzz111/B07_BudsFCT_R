#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import os
import json
import inspect
import hashlib
import zipfile
import subprocess
from datetime import datetime
from threading import Timer
from rtrpcLib import levels, events
from rtrpcLib.events import getEvents


class Report:
    __slots__ = ("event", "data")

    def __init__(self):
        event = None
        data = None

    def _to_dict(self):
        jdata = dict(event=self.event, data=self.data)
        return jdata

    def serialize(self):
        return json.dumps(self._to_dict())

    def __repr__(self):
        resStr = 'event=' + getEvents(self.event) + '; data=' + str(self.data)
        return resStr


class TesterReporter(object):
    def __init__(self, publisher):
        self.publisher = publisher

    def create_report(self, event_type, data, **kwargs):
        report = Report()
        report.event = event_type
        report.data = data
        self.publisher.publish(report.serialize(), level=levels.REPORTER)

    @staticmethod
    def parse_report(msg):
        if 'data' in msg and 'event' in msg:
            report_dict = json.loads(msg)
            report = Report()
            report.event = report_dict['event']
            report.data = report_dict['data']
            return report
        else:
            report = Report()
            report.event = events.ILLEGAL_EVENT
            report.data = msg
            return report


def print_with_stack(info):
    stack = inspect.stack()[1][0]
    module, line = re.findall("([a-zA-Z0-9]+\.py).*(line\s* \d+)", str(stack))[0]
    print(f"{datetime.now()} <{module}><{line}>   {info}")


def print_with_time(info):
    print(str(datetime.now()) + ' ' * 3 + info)


class Utility:
    @staticmethod
    def run_shell_with_timeout(cmd, timeout=3):
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        timer = Timer(timeout, lambda process: process.kill(), [p])
        try:
            timer.start()
            stdout, stderr = p.communicate()
            return_code = p.returncode
            return return_code, stdout, stderr
        finally:
            timer.cancel()

    @staticmethod
    def get_first_file(file_path, file_type='.csv', count=1):
        files = [f for f in os.listdir(str(file_path)) if f.endswith(file_type)]
        if count == -1:
            return files
        if len(files) >= count:
            files.sort()
            return files[:count]
        return None

    @staticmethod
    def get_first_absPathFile(file_path, file_type='.csv'):
        files = [os.path.join(file_path, f) for f in os.listdir(str(file_path)) if f.endswith(file_type)]
        if len(files) >= 1:
            files.sort()
            return files[0]
        return None

    @staticmethod
    def get_all_absPathFile(file_path, file_type='.csv'):
        files = [os.path.join(file_path, f) for f in os.listdir(str(file_path)) if f.endswith(file_type)]
        if len(files) >= 1:
            return files
        return None

    @staticmethod
    def get_first_path(file_path="/"):
        paths = [p for p in os.listdir(str(file_path)) if os.path.isdir(os.path.join(file_path, p))]
        if paths:
            return paths[0]
        return None

    @staticmethod
    def get_file_md5(check_file):
        try:
            with open(check_file, 'rb') as f:
                md5 = hashlib.md5(f.read()).hexdigest()
            return md5
        except:
            return None

    @staticmethod
    def files_to_zip(file_path, zip_path, save_name='PRM_Backup_Log.zip'):
        files = [os.path.join(file_path, f) for f in os.listdir(str(file_path))]
        zip_new = os.path.join(zip_path, save_name)
        if not zip_new.endswith('.zip'):
            zip_new += '.zip'
        zf = zipfile.ZipFile(zip_new, 'w')
        for f in files:
            f_path, f_name = os.path.split(f)
            zf.write(f, arcname=f_name, compress_type=zipfile.ZIP_DEFLATED)
        zf.close()
        return True

    @staticmethod
    def upload_insight_format(file_path):
        files = [os.path.join(file_path, f) for f in os.listdir(str(file_path))]
        ret = json.dumps({'logs': ','.join(files)})
        return ret if ret else ''

    @staticmethod
    def parseTestPlan(tpPath):
        tpFile = os.path.split(tpPath)[-1]
        tpName = os.path.splitext(tpFile)[0]
        return tpName.split("__")


if __name__ == "__main__":
    print_with_stack('hi')
