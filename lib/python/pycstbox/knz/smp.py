#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of CSTBox.
#
# CSTBox is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# CSTBox is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with CSTBox.  If not, see <http://www.gnu.org/licenses/>.

""" Kipp and Zonen pyranometer lew-level interface.

This modules defines a sub-class of minimalmodbus.Instrument which polls the
parameters of interest (namely irradiance and body température).

It also defines the input registers so that more specific needs can be
implemented by sub-classing and overiding, or direct Modbus register read.

Depends on Jonas Berg's minimalmodbus Python library :
    https://pypi.python.org/pypi/MinimalModbus/
    Version in date of writing: 0.4
"""

import struct
import math
from collections import namedtuple

from pycstbox.modbus import ModbusRegister, RTUModbusHWDevice
from pycstbox.log import Loggable

__author__ = 'Eric PASCUAL - CSTB (eric.pascual@cstb.fr)'
__copyright__ = 'Copyright (c) 2013 CSTB'


# Input registers

REG_DEVICE_TYPE = ModbusRegister(0x00)
REG_DATAMODEL_VERSION = ModbusRegister(0x01)
REG_OPERATIONAL_MODE = ModbusRegister(0x02)
REG_STATUS_FLAGS = ModbusRegister(0x03)
REG_SCALE_FACTOR = ModbusRegister(0x04)
REG_SENSOR_1_DATA = ModbusRegister(0x05)
REG_RAW_SENSOR1_DATA = ModbusRegister(0x06)
REG_STDEV_SENSOR1 = ModbusRegister(0x07)
REG_BODY_TEMPERATURE = ModbusRegister(0x08)
REG_EXT_POWER_SENSOR = ModbusRegister(0x09)
REG_DAC_OUTPUT_VOLTAGE = ModbusRegister(0x10)
REG_SELECTED_DAC_INPUT = ModbusRegister(0x11)
REG_ADC1_COUNTS = ModbusRegister(0x12, size=2)
REG_ADC2_COUNTS = ModbusRegister(0x14, size=2)
REG_ADC3_COUNTS = ModbusRegister(0x16, size=2)
REG_ADC4_COUNTS = ModbusRegister(0x18, size=2)

REG_ERROR_CODE = ModbusRegister(0x1A)

ALL_INPUTS_SIZE = reduce(lambda sztot, sz : sztot + sz,
                         [reg.size for reg in [  #pylint: disable=E1103
                            REG_DEVICE_TYPE,
                            REG_DATAMODEL_VERSION,
                            REG_OPERATIONAL_MODE,
                            REG_STATUS_FLAGS,
                            REG_SCALE_FACTOR,
                            REG_SENSOR_1_DATA,
                            REG_RAW_SENSOR1_DATA,
                            REG_STDEV_SENSOR1,
                            REG_BODY_TEMPERATURE,
                            REG_EXT_POWER_SENSOR,
                            REG_DAC_OUTPUT_VOLTAGE,
                            REG_SELECTED_DAC_INPUT,
                            REG_ADC1_COUNTS,
                            REG_ADC2_COUNTS,
                            REG_ADC3_COUNTS,
                            REG_ADC4_COUNTS,
                        ]])

# Operational modes
OPMODE_NORMAL = 1
OPMODE_SERVICE = 2
OPMODE_CALIBRATION = 3
OPMODE_FACTORY = 4
OPMODE_ERROR = 5

# Ouput registers (coils)

REG_CLEAR_ERROR = ModbusRegister(0x0A)


class StatusFlags(object):
    """ Device status flags. """

    names = [
        'signal', 'overflow', 'underflow', 'error', 'ADC', 'DAC',
        'calibration', 'update'
    ]
    SIGNAL_QUALITY, OVERFLOW, UNDERFLOW, ERROR, \
            ADC, DAC, CALIBRATION, UPDATE = xrange(len(names))

    def __init__(self, value):
        self.value = value

    def flags_set(self):
        return [
            name for bit, name in enumerate(self.names)
            if self.value & (1 << bit)
        ]

    def is_set(self, flag):
        return ((1 << flag) & self.value) != 0

    def __str__(self):
        return ','.join(self.flags_set)


class SMPInstrument(RTUModbusHWDevice):
    """ Kipp and Zonen SMP pyranometer modeling class.

    The supported model is the RTU RS485 one, the RS485 bus being connected
    via a USB.RS485 interface.
    """

    # Definition of the type of the poll() method result

    # VERY IMPORTANT :
    # The name of its items MUST match the name of the outputs described
    # in the metadata stored in devcfg.d directory, since the notification
    # events generation process is based on this.
    # (see pycstbox.hal.device.PolledDevice.poll() method for details)
    OutputValues = namedtuple('OutputValues', [
        'Irr',      # solar irradiance (W/m2)
        'temp',     # body temperature (degC)
    ])

    def __init__(self, port, unit_id):
        """
        :param str port: serial port on which the RS485 interface is connected
        :param int unit_id: the address of the device
        """
        super(SMPInstrument, self).__init__(port=port, unit_id=int(unit_id), logname='smp')

    def reset(self):
        """ Resets operational mode """
        self.write_bit(REG_CLEAR_ERROR.addr, 1)

    def poll(self):
        """ Reads the registers operational mode to sensor1 data and returns the
        values as a named tuple.

        In case of invalid current mode or error status, resets the device in
        operational mode and return None.
        """
        if self._first_poll:
            self._first_poll = False
            self.log_info('first poll -> reset device')
            self.reset()

        opmode, status_flags, scale_factor, sensor1_data, _, _, temp = struct.unpack(
            '>HHhhhhh',
            self.read_string(REG_OPERATIONAL_MODE.addr, 7)
        )

        if opmode != OPMODE_NORMAL:
            self.reset()
            self.log_warn('device was not in normal mode -> reset done')
            return None

        if status_flags:
            sf = StatusFlags(status_flags)
            self.log_error('some status flag(s) are set : %s', sf)
            if sf.is_set(StatusFlags.ERROR):
                errcode = self.read_register(REG_ERROR_CODE.addr)
                self.log_error(' - error code : %d', errcode)

            self.reset()
            self.log_warn('reset done')

        return self.OutputValues(
            Irr=sensor1_data / math.pow(10, scale_factor),
            temp=temp / 10.0
        )
