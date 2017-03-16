from periphery import I2C



class LPS331AP:

    _I2C_ADDRESS = 0x5C

    _CTRL_REG2 = 0x21
    _STATUS_REG = 0x27



    _BOOT_MASK = 0x80
    _SWRESET_MASK = 0x04
    _TRIGGER_ONESHOT = 0x01

    _PRESS_STATUS_MASK = 0x02
    _TEMP_STATUS_MASK = 0x01



    def __init__(self, bus=1):
        self.i2c = I2C('/dev/i2c-%s' % bus)

        # SWRESET
        swreset = [
            I2C.Message([self._CTRL_REG2]),
            I2C.Message([self._BOOT_MASK | self._SWRESET_MASK]),
        ]
        self.i2c.transfer(self._I2C_ADDRESS, swreset)
        while self._wait_swreset():
            time.sleep(0.05)



    def _wait_swreset():
        get_status_bits = [
            I2C.Message(self._STATUS_REG),
            I2C.Message([0x00], read=True)
        ]

        self.i2c.transfer(self._I2C_ADDRESS, get_status_bits)
        status_reg = get_status_bits[1].data[0]
        print(status_reg)


    def close():
        self.i2c.close()



if __name__ == '__main__':
    chip = LPS331AP()






# from fcntl import ioctl
# import time


# def concat_hex(*args):
#     reducer = lambda x, y: y + chr(x)
#     return reduce(reducer, args, '')


# class LPS331AP:
#     """Measures pressure."""

#     # SDO connected to ground -> address: 0b011100
#     _I2C_ADDRESS = 0x5C


#     # Usable registers
#     _CTRL_REG2 = 0x21
#     _STATUS_REG = 0x27

#     _PRESS_OUT_XL = 0x28
#     _PRESS_OUT_L = 0x29
#     _PRESS_OUT_H = 0x2A

#     _TEMP_OUT_L = 0x2B
#     _TEMP_OUT_H = 0x2C


#     # Usable on _CTRL_REG2
#     _BOOT_MASK = 0x80
#     _SWRESET_MASK = 0x04
#     _TRIGGER_ONESHOT = 0x01

#     # Usable on _STATUS_REG
#     _PRESS_STATUS_MASK = 0x02
#     _TEMP_STATUS_MASK = 0x01

#     # From Linux kernel configuration
#     _I2C_SLAVE = 0x0703

#     _TIMEOUT = 0.050


#     def __init__(self, bus=1):
#         self.i2c = open('/dev/i2c-%s' % bus, 'r+', 0)
#         ioctl(self.i2c, self._I2C_SLAVE, self._I2C_ADDRESS)
#         self.i2c.write(chr(self._CTRL_REG2) + chr(self._BOOT_MASK | self._SWRESET_MASK))

#         while self._wait_status_bits():
#             time.sleep(self._TIMEOUT)


#     def _wait_status_bits(self):
#         """Returns False when BOOT bit is 0, otherwise True."""
#         self.i2c.write(chr(self._CTRL_REG2))
#         ctrl_reg2 = self.i2c.read(1)
#         return bool(ord(ctrl_reg2) & self._BOOT_MASK)


#     def _wait_pressure(self):
#         """Returns False when P_DA bit is set to 1, otherwise True."""
#         self.i2c.write(chr(self._STATUS_REG))
#         status_reg = self.i2c.read(1)
#         return not bool(ord(status_reg) & self._PRESS_STATUS_MASK)


#     def _wait_temperature(self):
#         """Returns False when T_DA bit is set to 1, otherwise True."""
#         self.i2c.write(chr(self._STATUS_REG))
#         status_reg = self.i2c.read(1)
#         return not bool(ord(status_reg) & self._TEMP_STATUS_MASK)


#     #def wait_press_temp(self):
#     #    """True if P_DA and T_DA bits are not 1, otherwise False."""
#     #    self.i2c.write(chr(self._STATUS_REG))
#     #    status_reg = self.i2c.read(1)
#     #    p_da = status_reg & self._PRESS_STATUS_MASK
#     #    t_da = status_reg & self._TEMP_STATUS_MASK
#     #    return not(p_da and t_da)


#     def _trigger_oneshot(self):
#         self.i2c.write(chr(self._CTRL_REG2) + chr(self._TRIGGER_ONESHOT))


#     def _get_pressure_from_buffer(self, data):
#         """Pout = SP / 4096; XL, L, H register"""
#         unadjusted = ord(data[0]) | ord(data[1]) << 8 | ord(data[2]) << 16
#         unadjusted /= 4096
#         return unadjusted


#     def _get_temperature_from_buffer(self, data):
#         """T[C] = 42.5 + ST/480"""
#         unadjusted = ord(data[0]) | ord(data[1]) << 8
#         unadjusted /= 480
#         return unadjusted


#     def read_pressure(self):
#         self._trigger_oneshot()

#         while self._wait_pressure():
#             time.sleep(self._TIMEOUT)

#         self.i2c.write(chr(self._PRESS_OUT_XL))
#         data = self.i2c.read(3)  # 3 bytes of data for pressure
#         return self._get_pressure_from_buffer(data)


#     def read_temperature(self):
#         self._trigger_oneshot()

#         while self._wait_temperature():
#             time.sleep(self._TIMEOUT)

#         self.i2c.write(chr(self._TEMP_OUT_L))
#         data = self.i2c.read(2)  # 2 bytes of temperature data
#         return self._get_temperature_from_buffer(data)
