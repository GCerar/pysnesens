from fcntl import ioctl
import time
import codecs


def concat_hex(*args):
    reducer = lambda x, y: y + chr(x)
    return reduce(reducer, args, '')


class LPS331AP:
    """Measures pressure."""

    # SDO connected to ground -> address: 0b011100
    _I2C_ADDRESS = 0x5C


    # Usable registers
    _CTRL_REG1 = 0x20
    _CTRL_REG2 = 0x21
    _STATUS_REG = 0x27

    _WHO_AM_I = 0x0F

    _PRESS_OUT_XL = 0x28
    _PRESS_OUT_L = 0x29
    _PRESS_OUT_H = 0x2A

    _TEMP_OUT_L = 0x2B
    _TEMP_OUT_H = 0x2C

    # Usable on _CTRL_REG1
    _PD_MODE_DISABLE = 0x80
    _PD_MODE_ENABLE = 0x00

    # Usable on _CTRL_REG2
    _BOOT_MASK = 0x80
    _SWRESET_MASK = 0x04
    _TRIGGER_ONESHOT = 0x01

    # Usable on _STATUS_REG
    _PRESS_DA = 0x02  # Pressure data available
    _PRESS_OR = 0x20  # Pressure data overrun

    _TEMP_DA = 0x01
    _TEMP_OR = 0x10

    # From Linux kernel configuration
    _I2C_SLAVE = 0x0703

    _TIMEOUT = 0.050


    def __init__(self, bus=1):
        self.i2c = open('/dev/i2c-%s' % bus, mode='r+', buffering=0)
        ioctl(self.i2c, self._I2C_SLAVE, self._I2C_ADDRESS)

        #self._power_up()
        #self._swreset()

        # Sensor starts in power-down mode.
        self._power_up()

        self.i2c.write(chr(self._WHO_AM_I))
        if ord(self.i2c.read(1)) != 0xBB:
            raise Exception('0xF0 (HWO_AM_I) register returns incorrect value.')

    def _power_up(self):
        """Set power-down bit to 1, which disables powerdown mode."""
        self.i2c.write(bytearray([self._CTRL_REG1, self._PD_MODE_DISABLE]))


    def _swreset(self):
        """Set BOOT and SWRESET bit to 1 for full reset."""
        self.i2c.write(
            bytearray([self._CTRL_REG2, self._BOOT_MASK | self._SWRESET_MASK])
        )
        while self._wait_status_bits():
            time.sleep(self._TIMEOUT)


    def _wait_status_bits(self):
        """Stop waiting when BOOT bit is 0."""
        self.i2c.write(chr(self._CTRL_REG2))
        ctrl_reg2 = ord(self.i2c.read(1))
        return bool(ctrl_reg2 & self._BOOT_MASK)


    def _wait_pressure(self):
        """Returns False when P_DA bit is set to 1, otherwise True."""
        self.i2c.write(chr(self._STATUS_REG))
        status_reg = ord(self.i2c.read(1))
        return not bool(status_reg & (self._PRESS_DA | self._PRESS_OR))


    def _wait_temperature(self):
        """Returns False when T_DA bit is set to 1, otherwise True."""
        self.i2c.write(chr(self._STATUS_REG))
        status_reg = ord(self.i2c.read(1))
        return not bool(status_reg & (self._TEMP_DA | self._TEMP_OR))


    def _trigger_oneshot(self):
        """Set ONESHOT bit to 1."""
        self.i2c.write(
            bytearray([self._CTRL_REG2, self._TRIGGER_ONESHOT])
        )


    def _get_pressure_from_bytarray(self, data):
        """Pout = SP / 4096;"""
	
        #unadjusted = (data[0] << 8) + data[1]
        unadjusted = int(codecs.encode(data, 'hex'), 16)
	#unadjusted = int.from_bytes(data, byteorder='little', signed=False)
        unadjusted /= 4096
        return unadjusted


    def _get_temperature_from_bytearray(self, data):
        """T[C] = 42.5 + ST/480"""
        #unadjusted = (data[0] << 16) + (data[1] << 8) + data[1]
        unadjusted = int(codecs.encode(data, 'hex'), 16)
        unadjusted -= 1 << 16  # temperature can be negative
        #unadjusted = int.from_bytes(data, byteorder='little', signed=False)
        unadjusted /= 480.0
        unadjusted += 42.5
        return unadjusted


    def read_pressure(self):
        """Read 3 bytes of pressure data."""
        self._trigger_oneshot()

        while self._wait_pressure():
            time.sleep(self._TIMEOUT)

        data = bytearray([])
        for address in [self._PRESS_OUT_H, self._PRESS_OUT_L, self._PRESS_OUT_XL]:
            self.i2c.write(chr(address))
            data.append(ord(self.i2c.read(1)))

        return self._get_pressure_from_bytarray(data)


    def read_temperature(self):
        """Read 2 bytes of temperature data."""
        self._trigger_oneshot()

        while self._wait_temperature():
            time.sleep(self._TIMEOUT)

        data = bytearray([])
        for address in [self._TEMP_OUT_H, self._TEMP_OUT_L]:
            self.i2c.write(chr(address))
            data.append(ord(self.i2c.read(1)))

        return self._get_temperature_from_bytearray(data)



if __name__ == '__main__':
    sensor = LPS331AP()
    print(sensor.read_pressure())
    print(sensor.read_temperature())
