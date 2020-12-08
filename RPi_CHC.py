#!/usr/bin/env python3
import os, sys
import math
import shutil, subprocess
import argparse
from glob import glob
import collections
import RPi.GPIO
import smbus
import time


class rpi_chc:
    """Raspberry CHeeseCake interface for I2C"""

    def __init__(self):
        self.GPIO = RPi.GPIO
        self.bus = smbus

        # Setting the pin numbering scheme
        self.GPIO.setmode(self.GPIO.BCM)
        self.GPIO.setwarnings(False)

        # Set up the I2C bus
        device_bus = 1  # for SDA1 and SCL1
        self.bus(device_bus)

    def close(self):
        """Setting GPIO17 to Low to deselect both channels for I2C switch, and cleans up rpi"""
        # Set GPIO 17 to High
        self.GPIO.output(17, 0)
        print("GPIO17 set to low, deselect both channels in I2C Switch")

        # Cleanup
        self.bus.close()
        self.GPIO.cleanup()

    def en_i2c_switch(self):
        """Setting GPIO17 to High to disable Reset for I2C switch"""
        reset_channel = 17
        self.GPIO.setup(reset_channel, self.GPIO.OUT)
        self.GPIO.output(reset_channel, 1)
        print("GPIO17 set to high, can now select channels in I2C Switch")

    def config_select(self, boss_addr=True):
        """Setting GPIO 13 high, connected to config_select enabling I2C"""
        config_channel = []
        if boss_addr:
            config_channel.append(13)
        elif not boss_addr:
            config_channel.append(26)
        self.GPIO.setup(config_channel, self.GPIO.OUT)
        self.GPIO.output(config_channel, 1)
        print("Config Select set to I2C for Pin : " + str(config_channel) + "\n")

    def i2c_cha_sel(self, i2c_cha):
        """ Select the boss (i2c_cha==1) or sub (i2c_cha==0) address for I2C Switch"""
        i2c_switch_addr = 0x73  # 01110011

        # Control Register for channel selection in I2C Switch
        ctrl_reg = {"Boss": 0x01, "Sub": 0x02}

        # Select the slave address for DPS422
        if i2c_cha == 1:  # boss
            self.bus.write_byte(i2c_switch_addr, ctrl_reg["Boss"])
            print("Boss selected")
        elif i2c_cha == 0:  # sub
            self.bus.write_byte(i2c_switch_addr, ctrl_reg["Sub"])
            print("Sub selected")

    def get_i2c_address(self, address):
        """Given an address, returns address suitable for i2c between RPi and LpGBT"""
        reg_addr = int(address, 16)
        reg_addr_low = reg_addr & 0x00ff
        reg_addr_high = (reg_addr >> 8) & 0x00ff  # NOTE Is this correct?
        return reg_addr, reg_addr_low, reg_addr_high

    def i2c_write(self, address, value):
        """Write to the LpGBT register given an address and value using I2C"""
        device_addr, reg_addr_low, reg_addr_high = self.get_i2c_address(address)

        data_write = int(value, 16)
        return self.bus.write_i2c_block_data(device_addr, reg_addr_low, [reg_addr_high, data_write])

    def i2c_read(self, address):
        """Read the LpGBT register given address"""
        device_addr, reg_addr_low, reg_addr_high = self.get_i2c_address(address)
        self.bus.write_i2c_block_data(device_addr, reg_addr_low, [reg_addr_high])

        data_final = self.bus.read_byte(device_addr)
        data_final_hex = hex(data_final)
        print("Final data value for register " + device_addr + " : " + str(data_final_hex))



