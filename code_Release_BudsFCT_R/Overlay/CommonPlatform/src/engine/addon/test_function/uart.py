

from rtlib.utility import Unit
from rtlib.utility import ReturnDef
from rtlib.utility import handle_response


class uart(object):

    rpc_public_api = [
       'switch_mode','open_uart', 'close_uart', 'send', 'send_read', 'send_read_key_words', 'read_until', 'read_string', 'send_read_save_buff',
        'send_recv', 'sendrecv_by_byte' ,'write_sn','read_sn', 'send_read_with_dummy'
    ]

    def __init__(self, xobjects):
        self.xobjects = xobjects
        self.mixrpc = xobjects["mix_dev_rpc"]
        self.site = xobjects.get('site')
        self.publisher = xobjects.get('cb_pub')
        self.serial = xobjects.get('uart0', None)
        

    def log(self, message):
        if self.publisher:
            print(message)
            msg = '[{}] '.format(message)
            self.publisher.publish(msg)


    def switch_mode(self, *args, **kwargs):
        '''
            for coreboard single/double uart switch
        '''
        if len(args) != 1:
            return ReturnDef.MISS_PARAMETER
        oneline = True if args[0] == "TRUE" else False
        bRet = self.mixrpc.rpc_call("mixdevice.switch_mode", oneline)
        return bRet

    
    def send_recv(self, *args, **kwargs):
        '''
            core uart send read
        '''
        print("*"*100)
        print(len(args))

        cmd = str(args[0])
        for i in range(3):
            self.mixrpc.rpc_call("com.write", cmd)
            time.sleep(1)
            bRet = self.mixrpc.rpc_call("com.read_by_byte")
            read_str = ''.join(chr(x) for x in bRet if x < 128)
            if read_str:
                read_str = read_str.replace("\n","").replace("\r","").strip()
                response = re.findall(r'[\w\d\.=,!\- ]+', read_str)
                print(response)
        return ReturnDef.PASS_STRING


    def sendrecv_by_byte(self, *args, **kwargs):
        '''
            core uart send read by byte
        '''
        if len(args)!=2:
            return ReturnDef.MISS_PARAMETER
        cmd_list = str(args[0])
        args1 = args[1].split(":")
        delay_ms = int(args1[0])
        need_response = True if args1[1] == "True" else False
        bRet = self.mixrpc.rpc_call("mixdevice.sendrecv_by_byte", cmd_list, delay_ms, need_response)
        return bRet


    def open_uart(self, *args, **kwargs):
        try:
            self.serial.connect()
            return ReturnDef.PASS_STRING
        except:
            return ReturnDef.FAIL_STRING
        return ReturnDef.FAIL_STRING


    def close_uart(self, *args, **kwargs):
        try:
            self.serial.close()
            return ReturnDef.PASS_STRING
        except:
            return ReturnDef.FAIL_STRING
        return ReturnDef.FAIL_STRING

    def read_string(self, *args, **kwargs):
        self.serial.read_string()
        return True

    def send_read(self, *args, **kwargs):
        cmd  = str(args[0])
        expect_keyword = str(args[1])
        self.serial.read_string()
        for i in range(3):
            self.serial.send(cmd)
            time.sleep(0.5)
            bRet = self.serial.read_until(expect_keyword, 2000)
            if bRet:
                if cmd == "[get_charging_status,]":
                    chg_satus = re.findall(r"ChgStatus:(\w+)",bRet)
                    if chg_satus:
                        return chg_satus[0].strip()
                elif cmd == "get_batt_curr,]":
                    bat_curr = re.findall(r"Cur:(\w+)",bRet)
                    if bat_curr:
                        return bat_curr[0].strip()
                elif cmd == "[get_adc0,]":
                    adc0 = re.findall(r"Adc0:(\w+)", bRet)
                    if adc0:
                        return adc0[0].strip()
                elif cmd == "[get_8300_version,]":
                    fw1 = re.findall(r"Fw1Version:([\d.]+)",bRet)
                    if fw1:
                        return fw1[0].strip()
                else:
                    return bRet.replace("\n","").replace("\r","")
            continue
        return ReturnDef.FAIL_STRING

    def send_read_with_dummy(self, *args, **kwargs):
        cmd = str(args[0])
        expect_keyword = str(args[1])
        self.send("dummy")
        # self.serial.read_string()
        bRet = self.send_read(cmd, expect_keyword)
        if bRet and bRet != ReturnDef.FAIL_STRING:
            return bRet
        else:
            if cmd == "[get_charging_status,]":
                for i in range(3):
                    self.send(cmd)
                    time.sleep(2)
                    bRet = self.serial.read_string()
                    if bRet and re.findall(r"ChgStatus:(\w+)",bRet):
                        return re.findall(r"ChgStatus:(\w+)",bRet)[0]
            return ReturnDef.FAIL_STRING

    def check_8300_fw(self, *args, **kwargs):
        # if fw == expect fw : skip restore 8300 and cal
        # if fw == "00.00.00.00" normal to do restore 8300 and cal
        # if fe != "00.00.00.00" and fw(old fw) to do restore erase 8300 and cal
        expect_fw = str(args[0])
        self.skip_8300_restore_and_cal = False
        cmd = "[get_8300_version,]"
        expect_keyword = "Fw1Version"
        bRet = self.send_read_with_dummy(cmd, expect_keyword)
        if bRet:
            if re.findall(expect_fw, bRet):
                self.skip_8300_restore_and_cal = True
                self.erase_8300_on = False
                return expect_fw
            elif re.findall(r"00.00.00", bRet):
                self.skip_8300_restore_and_cal = False
                self.erase_8300_on = False
                return "No 8300 FW"
            else:
                self.skip_8300_restore_and_cal = False
                self.erase_8300_on = True
                return "Old 8300 FW"
        return ReturnDef.FAIL_STRING


    def send_read_key_words(self, *args, **kwargs):
        # cmd = str(args[0])
        # expect_keyword = str(args[1])
        # terminator = str(args[2])
        # time_out = int(args[3])
        cmd, expect_keyword , terminator= str(args[0]).split("@")
        timeout1, timeout2 = str(args[1]).split("@")
        timeout1 = int(timeout1)
        timeout2 = int(timeout2)
        for i in range(3):
            self.serial.send(cmd)
            if self.serial.read_until(expect_keyword, timeout1):
                if self.serial.read_until(terminator, timeout2):
                    return terminator
                else:
                    return ReturnDef.FAIL_STRING
            else:
                continue
        return ReturnDef.FAIL_STRING

    def read_until(self, *args, **kwargs):
        terminator = str(args[0])
        timeout = int(args[1])
        if self.serial.read_until(terminator, timeout):
            return "--PASS--"
        return "--FAIL--"


    def send(self, *args, **kwargs):
        cmd = args[0]
        bRet = self.serial.send(cmd)
        if bRet:
            return ReturnDef.PASS_STRING
        else:
            return ReturnDef.FAIL_STRING



    def write_sn(self, *args, **kwargs):
        self.read_string()
        scan_sn = str(args[0])
        cmd = "[set_pcba_sn,{}]".format(scan_sn)
        expect_keyword = str(args[0])
        return self.send_read(cmd, expect_keyword)

    def read_sn(self, *args, **kwargs):
        print("====",len(args))
        self.read_string()
        scan_sn = str(args[0])
        cmd = "[get_pcba_sn,]"
        expect_keyword = scan_sn
        bRet = self.send_read(cmd, "PCBA SN")
        if bRet:
            bRet =bRet.replace("\n","").replace("\r","")
            print("sn------",bRet)
            read_sn = re.findall(r"PCBA SN:(\w{14})",bRet)
            if read_sn:
                return  read_sn[0]
            return bRet
        return ReturnDef.FAIL_STRING

   

    def covert_str(self,data):
        data = data.replace(" ","")
        return "".join([data[i:i+2] for i in range(0, len(data), 2)])



    def send_read_save_buff(self, *args, **kwargs):
        cmd = str(args[0])
        expect_keyword = str(args[1])
        # self.serial.read_string()
        for i in range(3):
            self.buff_dict = {}
            self.serial.send(cmd)
            time.sleep(0.5)
            bRet = self.serial.read_until(expect_keyword, 2000)
            if bRet:
                if cmd == "[2700_status,]":
                    mode = re.findall(r"Mode0:(\w+)", bRet)
                    if mode and mode[0]:
                        mode = mode[0].strip()
                        self.buff_dict["Mode0"] = mode
                    bt = re.findall(r"BT:(\w+)", bRet)
                    if bt and bt[0]:
                        bt = bt[0].strip()
                        bt = self.covert_str(bt)
                        self.buff_dict["BT"] = bt
                    ble = re.findall(r"BLE:(\w+)", bRet)
                    if ble and ble[0]:
                        ble = ble[0].strip()
                        ble = self.covert_str(ble)
                        self.buff_dict["BLE"] = ble
                elif cmd == "[init_status,]":
                    aw = re.findall(r"Aw:(\w+)", bRet)
                    if aw and aw[0]:
                        aw = aw[0].strip()
                        self.buff_dict["Aw"] = aw
                    cw = re.findall(r"Cw:(\w+)", bRet)
                    if cw and cw[0]:
                        cw = cw[0].strip()
                        self.buff_dict["Cw"] = cw

                    fw0 = re.findall(r"Fw0Version:([\w.]+)", bRet)
                    if fw0 and fw0[0]:
                        fw0 = fw0[0].strip()
                        self.buff_dict["Fw0Version"] = fw0

                    fw2 = re.findall(r"Fw2Version:([\w.]+)", bRet)
                    if fw2 and fw2[0]:
                        fw2 = fw2[0].strip()
                        self.buff_dict["Fw2Version"] = fw2
                return ReturnDef.PASS_STRING
            continue
        return ReturnDef.FAIL_STRING
