This folder (/mix/addon/config/) contains MIX Firmware profile.
Refer to Profile spec in <rdar://problem/56735804> for details.

Example hw profile that only start 1 DUT RPC server at port 7801:

```
{
    "NOTES":"This is an example profile that only start 1 DUT RPC server at port 7801.",
    "duts": {
        "dut0": {
            "site": 0
        }
    }
}
```