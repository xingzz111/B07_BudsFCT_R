import re
import time
from rtlib.utility import retry_with_delay
class DUTCommand(object):
    rpc_public_api = ['open_uart', 'close_uart', 'send', 'read_string', 'read_until', 'send_read', 'send_read_key_words', 'parse_response',
                      'send_read_key_words_doe'
                    ]

    def __init__(self, uart, publisher=None):
        self.uart = uart
        self.publisher = publisher
        self.response = None

    def log(self, message):
        if self.publisher:
            print(message)
            msg = '[{}] '.format(message)
            self.publisher.publish(msg)

    def open_uart(self):
        try:
            result = self.uart.connect()
            return result
        except:
            return False

    def close_uart(self):
        try:
            result = self.uart.close()
            return result
        except:
            return False
   
    def send(self, cmd):
        try:
            result = self.uart.send(cmd)
            return result
        except:
            return False

    def read_string(self):
        try:
            result = self.uart.read_string()
            if result:
                return self.clean_string(result)
            return False
        except:
            return False

    def read_until(self, terminator, timeout):
        result = self.uart.read_until(terminator, timeout)
        if result:
            return self.clean_string(result)
        else:
            return False

    @retry_with_delay(max_retries=3, delay_seconds=0.1)
    def send_read(self, cmd, expect_keyword, pattern=None):
        self.uart.read_string()
        self.response = None
        self.uart.send(cmd)
        time.sleep(0.5)
        result = self.uart.read_until(expect_keyword, 2000)
        if result:
            self.response = result
            if pattern:
                return self.parse_response(pattern)
            return self.clean_string(result)
        else:
            time.sleep(0.2)
        return False

    def parse_response(self, pattern):
        if self.response:
            mactch_data = re.findall(pattern, self.response)
            if mactch_data and mactch_data[0]:
                result = mactch_data[0].strip()
                return result
        return False

    def send_read_key_words(self, cmd, expect_keyword, terminator, timeout1, timeout2):
        # self.read_string()
        for i in range(3):
            self.uart.send(cmd)
            if self.uart.read_until(expect_keyword, timeout1):
                if self.uart.read_until(terminator, timeout2):
                    return terminator
                else:
                    return False
            else:
                continue
        return False

    def send_read_key_words_doe(self, cmd, expect_keyword, terminator, timeout1, timeout2):
        # self.read_string()
        for i in range(3):
            self.uart.send(cmd)
            if self.uart.read_until(expect_keyword, timeout1):
                if self.uart.read_until(terminator, timeout2):
                    return terminator
                else:
                    self.read_string()
                    continue
            else:
                continue
        return False

    def write_sn(self, sn):
        self.read_string()
        cmd = "[set_pcba_sn,{}]".format(sn)
        return self.send_read(cmd, sn)

    def read_sn(self):
        cmd = "[get_pcba_sn,]"
        self.read_string()
        result = self.send_read(cmd, "PCBA SN")
        if result:
            read_sn = re.findall(r"PCBA SN:(\w{14})",result)
            if read_sn:
                return  read_sn[0]
            return result
        return False
    
    def clean_string(self, result):
        result = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]","",result)
        result = result.replace("\n", " ")
        return result