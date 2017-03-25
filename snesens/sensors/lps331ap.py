from fcntl import ioctl
import time





class LPS331AP:
    """Measure temperature, air pressure, indirectly altitude."""

    _I2C_ADDRESS = 0x5C


    _WHO_AM_I = 0x0F
    _RES_ADDR = 0x10
    _CTRL_REG1 = 0x20
    _CTRL_REG2 = 0x21

    _I2C_SLAVE = 0x0703

    _ONE_SHOT_CONVERSION_TIME = 0.042  # 41545 us

    __temperature = None
    __pressure = None
    __altitude = None


    def __init__(self, bus=1):
        # Works only on Py2.7; Python3.x doesn't support unbuffered R/W
        self.i2c = open('/dev/i2c-%s' % bus, mode='r+', buffering=0)
        ioctl(self.i2c, self._I2C_SLAVE, self._I2C_ADDRESS)

        self._check_who_am_i()
        self._configure()
        self.one_shot()


    def _check_who_am_i(self):
        self.i2c.write(bytearray([self._WHO_AM_I]))
        who_am_i = ord(self.i2c.read(1))
        if who_am_i != 0xBB:
            raise Exception('This is not LPS331AP!')


    def _configure(self):
        # Power down
        self.i2c.write(bytearray([self._CTRL_REG1, 0x00]))

        # Set highest precision
        self.i2c.write(bytearray([self._RES_ADDR, 0x7A]))

        # Power up + single shot mode
        self.i2c.write(bytearray([self._CTRL_REG1, 0x84]))


    def close(self):
        self.i2c.close()


    def one_shot(self):
        self.__altitude = None
        self.__pressure = None
        self.__temperature = None

        self.i2c.write(bytearray([self._CTRL_REG2, 0x01]))

        while self._wait_status_bit():
            time.sleep(self._ONE_SHOT_CONVERSION_TIME)


    def _wait_status_bit(self):
        self.i2c.write(bytearray([self._CTRL_REG2]))
        status = ord(self.i2c.read(1))
        return status != 0x00


    def _read_temperature(self):
        self.i2c.write(bytearray([0x2B]))
        lsb = ord(self.i2c.read(1))

        self.i2c.write(bytearray([0x2C]))
        msb = ord(self.i2c.read(1))

        temperature = (msb << 8) | lsb
        temperature -= 1 << 16  # Signed int16
        temperature = 42.5 + temperature / (120.0*4)
        return temperature


    def _read_pressure(self):
        self.i2c.write(bytearray([0x28]))
        xlsb = ord(self.i2c.read(1))

        self.i2c.write(bytearray([0x29]))
        lsb = ord(self.i2c.read(1))

        self.i2c.write(bytearray([0x2A]))
        msb = ord(self.i2c.read(1))

        pressure = (msb << 16) | (lsb << 8) | xlsb  # uint32
        pressure /= 4096  # scale
        return pressure


    def _read_altitude(self):
        """WARNING: This is only approximation!"""
        pressure_0 = 1013.25
        pressure = self.get_pressure()
        altitude_ft = (1 - (pressure/pressure_0)**0.190284)*145366.45
        altitude_m = altitude_ft / 3.280839895
        return altitude_m


    def get_pressure(self):
        if self.__pressure is None:
            self.__pressure = self._read_pressure()

        return self.__pressure


    def get_temperature(self):
        if self.__temperature is None:
            self.__temperature = self._read_temperature()

        return self.__temperature


    def get_altitude(self):
        if self.__altitude is None:
            self.__altitude = self._read_altitude()

        return self.__altitude



if __name__ == '__main__':
    sensor = LPS331AP()
    print("Temp (degC):", sensor.get_temperature())
    print("Pressure (mBar):", sensor.get_pressure())
    print("alt (m)", sensor.get_altitude())
