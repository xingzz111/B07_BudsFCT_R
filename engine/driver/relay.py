
class Relay(object):

    rpc_public_api = ["test123", "test222"]
    def __init__(self, i2c_base, i2c_sib, i2c_wib):
        self.i2c_base = i2c_base
        self.i2c_sib = i2c_sib
        self.i2c_wib = i2c_wib

    def test123(self, *args, **kwargs):
        print("i2c_base: {}".format(self.i2c_base))
        print("i2c_sib: {}".format(self.i2c_sib))
        print("i2c_wib: {}".format(self.i2c_wib))
        return "done"
    
    def test222(self, *args, **kwargs):
        print("test222: --> value: {}".format(args[0]))
        return True
