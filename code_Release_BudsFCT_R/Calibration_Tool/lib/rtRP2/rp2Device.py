from . import com
import time
import ast
import re

class Rp2Device(object):

    def __init__(self, port, baudrate, publisher=None, isprint=True):
        self._port = port
        self._baudrate = baudrate
        self._pyb = None
        self._publisher = publisher
        self.isprint = True

    def init(self):
        if not self._pyb:
            self._pyb = com.Pyboard(self._port, self._baudrate)
            self._pyb.enter_raw_repl()
        return True

    def deinit(self):
        if self._pyb:
            self._pyb.exit_raw_repl()
            self._pyb = None

    def rpc_call(self, *args, **kwargs):
        # start_time = time.time()
        # 检查是否提供了函数名
        if len(args) < 1:
            raise RuntimeError("Missing function name")
        # 提取函数名
        function = str(args[0])
        # 提取位置参数
        function_args = args[1:]  # args[1:] 是函数的参数部分
        # 将位置参数转为字符串表示
        arg_strings = [repr(arg) for arg in function_args]  # 使用 repr 确保参数格式正确
        kwargs_strings = [f"{key}={repr(value)}" for key, value in kwargs.items()]

        # 拼接所有参数
        all_args = ", ".join(arg_strings + kwargs_strings)
        # 构造要执行的 Python 代码
        python_code = f"{function}({all_args})"
        # 打印调试信息
        if self._publisher:
            self._publisher.publish(f"{python_code}")
        if self.isprint:
            print(f"{python_code}")
        # 执行代码（假设 pyb 是某种执行器对象）
        if hasattr(self, "_pyb") and self._pyb:
            res = self._pyb.exec_(python_code)
            if self.isprint:
                print(res)
            res = self.parse_result(res)
            if self._publisher:
                self._publisher.publish(res)
            # print("durating: {}".format(time.time() - start_time))
            return res
        else:
            raise RuntimeError("No execution engine (_pyb) found!")

    def parse_result(self, response: bytes):

        """
        通用解析方法：解析返回值并转换为对应的Python类型。
        
        Args:
            response (bytes): 返回的字节数据，例如 b'xxx\r\nxxxx\r\nxxxx\r\n'
        
        Returns:
            Any: 转换后的Python对象（float, int, str, list, dict, array.array等）
        """
        try:
            # 解码为字符串
            decoded = response.decode('utf-8').strip()
            last_line = decoded.split('\r\n')[-1].strip()
            match = re.search(r"array\('[a-zA-Z]', \[(.*)\]\)", last_line)
            if match:
                numbers_str = match.group(1)
                last_line = f"[{numbers_str}]"
            return ast.literal_eval(last_line)
        except (ValueError, SyntaxError):
            # 如果无法解析为Python原生类型，返回字符串本身
            return last_line