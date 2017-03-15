import fcntl
import time


class SHT21:
    """SHT21 provides way to measure temperature and humidity."""

    _SOFT_RESET = 0xFE
    _I2C_ADDRESS = 0x40

    _TRIGGER_TEMPERATURE_NO_HOLD = 0xF3
    _TRIGGER_HUMIDITY_NO_HOLD = 0xF5
    _STATUS_BITS_MASK = 0xFFFC

    I2C_SLAVE = 0x0703
    I2C_SLAVE_FORCE = 0x0706


    _TEMPERATURE_WAIT_TIME = 0.086  # (datasheet: typ=66, max=85)
    _HUMIDITY_WAIT_TIME = 0.030  # (datasheet: typ=22, max=29)


    def __init__(self, i2c_number=1):
        """i2c_number=0 for old PRi, 1 for new RPi."""
        self.i2c = open('/dev/i2c-%s' % i2c_number, 'r+', 0)
        fcntl.ioctl(self.i2c, self.I2C_SLAVE, self._I2C_ADDRESS)
        self.i2c.write(chr(self._SOFTRESET))
        time.sleep(0.050)


    @staticmethod
    def _calculate_checksum(data, number_of_bytes):
        """5.7 CRC Checksum using the polynomial given in the datasheet"""
        # CRC
        POLYNOMIAL = 0x131  # //P(x)=x^8+x^5+x^4+1 = 100110001
        crc = 0
        # calculates 8-Bit checksum with given polynomial
        for byteCtr in range(number_of_bytes):
            crc ^= (ord(data[byteCtr]))
            for bit in range(8, 0, -1):
                if crc & 0x80:
                    crc = (crc << 1) ^ POLYNOMIAL
                else:
                    crc = (crc << 1)
        return crc


    @classmethod
    def _get_temperature_from_buffer(cls, data):
        """This function reads the first two bytes of data and
        returns the temperature in C by using the following function:
        T = 46.82 + (172.72 * (ST/2^16))
        where ST is the value from the sensor
        """
        unadjusted = (ord(data[0]) << 8) + ord(data[1])
        unadjusted &= cls._STATUS_BITS_MASK  # zero the status bits
        unadjusted *= 175.72
        unadjusted /= 1 << 16  # divide by 2^16
        unadjusted -= 46.85
        return unadjusted


    @classmethod
    def _get_humidity_from_buffer(cls, data):
        """This function reads the first two bytes of data and returns
        the relative humidity in percent by using the following function:
        RH = -6 + (125 * (SRH / 2 ^16))
        where SRH is the value read from the sensor
        """
        unadjusted = (ord(data[0]) << 8) + ord(data[1])
        unadjusted &= cls._STATUS_BITS_MASK  # zero the status bits
        unadjusted *= 125.0
        unadjusted /= 1 << 16  # divide by 2^16
        unadjusted -= 6
        return unadjusted


    def read_temperature(self):
        self.i2c.write(chr(self._TRIGGER_TEMPERATURE_NO_HOLD))
        time.sleep(self._TEMPERATURE_WAIT_TIME)
        data = self.i2c.read(3)  # 2 bytes of data + 1 byte CRC
        if self._calculate_checksum(data, 2) == ord(data[2]):
            return self._get_temperature_from_buffer(data)


    def read_humidity(self):
        self.i2c.write(chr(self._TRIGGER_HUMIDITY_NO_HOLD))
        time.sleep(self._HUMIDITY_WAIT_TIME)
        data = self.i2c.read(3)  # 2 bytes of data + 1 byte CRC
        if self._calculate_checksum(data, 2) == ord(data[2]):
            return self._get_humidity_from_buffer(data)


    def close(self):
        self.i2c.close()


    def __enter__(self):
        return self


    def __exit__(self, type, value, traceback):
        self.close()
