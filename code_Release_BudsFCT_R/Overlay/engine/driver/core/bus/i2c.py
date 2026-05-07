
class I2C(object):
    rpc_public_api = ["test123"]
    def __init__(self, dev_name):
        self.dev_name = dev_name

    def test123(self):
        print("dev_name: {}".format(self.dev_name))
