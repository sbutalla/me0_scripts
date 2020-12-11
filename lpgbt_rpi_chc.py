#!/usr/bin/env python3
import os, sys
import math
import shutil, subprocess

import RPi.GPIO as GPIO
import smbus
import time


class lpgbt_rpi_chc:
    """Raspberry CHeeseCake interface for I2C"""

    def __init__(self):

        # Setting the pin numbering scheme
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        # Set up the I2C bus
        device_bus = 1  # for SDA1 and SCL1
        self.bus = smbus.SMBus(device_bus)
        self.gbtx_address = 0x70

    def terminate(self):
        """Setting GPIO17 to Low to deselect both channels for I2C switch, and cleans up rpi"""
        # Set GPIO 17 to High
        reset_channel = 17
        GPIO.output(reset_channel, 0)
        print("GPIO17 set to low, deselect both channels in I2C Switch")

        # Cleanup
        self.bus.close()
        GPIO.cleanup()

    def initialize(self, boss):
        """Takes all steps to initialize I2C with either boss or sub LpGBT"""
        lpgbt_rpi_chc.config_select(boss)
        lpgbt_rpi_chc.en_i2c_switch()
        lpgbt_rpi_chc.i2c_cha_sel(boss)

    def en_i2c_switch(self):
        """Setting GPIO17 to High to disable Reset for I2C switch"""
        reset_channel = 17
        GPIO.setup(reset_channel, GPIO.OUT)
        GPIO.output(reset_channel, 1)
        print("GPIO17 set to high, can now select channels in I2C Switch")

    def config_select(self, boss):
        """Setting GPIO 13 high, connected to config_select enabling I2C"""
        config_channel = 0
        if boss:
            config_channel = 13
        elif not boss:
            config_channel = 26
        if config_channel == 0:
            print("Config Select channel missing")
            i2c_selected = 0
        else:
            GPIO.setup(config_channel, GPIO.OUT)
            GPIO.output(config_channel, 1)
            i2c_selected = 1
        print("Config Select set to I2C for Pin : " + str(config_channel) + "\n")
        return i2c_selected

    def i2c_cha_sel(self, boss):
        """ Select the boss (i2c_cha==1) or sub (i2c_cha==0) address for I2C Switch"""
        i2c_switch_addr = 0x73  # 01110011

        # Control Register for channel selection in I2C Switch
        if boss:  # boss
            self.bus.write_byte(i2c_switch_addr, 0x01)
            print("Boss selected")
        else:  # sub
            self.bus.write_byte(i2c_switch_addr, 0x02)
            print("Sub selected")

    def i2c_device_scan(self):
        """Scans all possible I2C addresses for connected devices"""
        for device in range(128):

            try:
                self.bus.read_byte(device)
                print(hex(device))
            except:  # exception if read_byte fails
                pass

    #    def get_i2c_address(self, address):
    #       """Given an address, returns address suitable for i2c between RPi and LpGBT"""
    #         reg_addr = int(address, 16)
    #         reg_addr_low = reg_addr & 0x00ff
    #         reg_addr_high = (reg_addr >> 8) & 0x00ff
    #        return reg_addr, reg_addr_low, reg_addr_high

    def lpgbt_write_register(self, device_add, register, value):
        """Write to the LpGBT register given an address and value using I2C"""
        reg_add_l = register & 0xFF
        reg_add_h = (register >> 8) & 0xFF
        self.bus.write_i2c_block_data(device_add, reg_add_l, [reg_add_h, value])

    def lpgbt_read_register(self, device_add, register):
        """Read the LpGBT register given address"""
        reg_add_l = register & 0xFF
        reg_add_h = (register >> 8) & 0xFF
        self.bus.write_i2c_block_data(device_add, reg_add_l, [reg_add_h])

        data = self.bus.read_byte(device_add)
        return data
