from rw_reg_dongle_chc import *
from time import sleep
import sys
import os
import argparse

vtrx_slave_addr = 0x50

# VTRX+ registers
TX_reg = {}
TX_reg["TX1"] = { "biascur_reg": 0x03, "modcur_reg":0x04, "empamp_reg":0x05}
TX_reg["TX2"] = { "biascur_reg": 0x06, "modcur_reg":0x07, "empamp_reg":0x08}
TX_reg["TX3"] = { "biascur_reg": 0x09, "modcur_reg":0x0A, "empamp_reg":0x0B}
TX_reg["TX4"] = { "biascur_reg": 0x0C, "modcur_reg":0x0D, "empamp_reg":0x0E}

enable_reg = 0x00
TX_enable_bit = {}
TX_enable_bit["TX1"] = 0
TX_enable_bit["TX2"] = 1
TX_enable_bit["TX3"] = 2
TX_enable_bit["TX4"] = 3


def i2cmaster_write(system, reg_addr, data):

    # Writing control register of I2CMaster 2
    nbytes = 2
    control_register_data = nbytes<<2 | 0 # using 100 kHz
    writeReg(getNode("LPGBT.RW.I2C.I2CM2DATA0"), control_register_data, 0)
    writeReg(getNode("LPGBT.RW.I2C.I2CM2CMD"), 0x0, 0) # I2C_WRITE_CR
    
    # Writing multi byte data to I2CMaster 2
    writeReg(getNode("LPGBT.RW.I2C.I2CM2DATA0"), reg_addr, 0)
    writeReg(getNode("LPGBT.RW.I2C.I2CM2DATA1"), data, 0)
    writeReg(getNode("LPGBT.RW.I2C.I2CM2CMD"), 0x8, 0) # I2C_W_MULTI_4BYTE0
    
    writeReg(getNode("LPGBT.RW.I2C.I2CM2ADDRESS"), vtrx_slave_addr, 0)
    writeReg(getNode("LPGBT.RW.I2C.I2CM2CMD"), 0xC, 0) # I2C_WRITE_MULTI
    
    success=0
    while(success==0):
        # Status register of I2CMaster 2
        if system!="dryrun":
            status = readReg(getNode("LPGBT.RO.I2CREAD.I2CM2STATUS"))
        else:
            status = 0x04
        if (status>>6) & 0x1:
            print ("ERROR: Last transaction was not acknowledged by the I2C slave")
            rw_terminate()
        elif (status>>3) & 0x1:
            print ("ERROR: I2C master port finds that the SDA line is pulled low 0 before initiating a transaction. Indicates a problem with the I2C bus.")
            rw_terminate()
        success = (status>>2) & 0x1
        
    reg_addr_string = "0x%02X" % (reg_addr)
    data_string = "0x%02X" % (data)
    print ("Successful I2C write to slave register: " + reg_addr_string + ", data: " + data_string + " (" + '{0:08b}'.format(data) + ")")



def i2cmaster_read(system, reg_addr):

    # Writing control register of I2CMaster 2
    nbytes = 1
    control_register_data = nbytes<<2 | 0 # using 100 kHz
    writeReg(getNode("LPGBT.RW.I2C.I2CM2DATA0"), control_register_data, 0)
    writeReg(getNode("LPGBT.RW.I2C.I2CM2CMD"), 0x0, 0) # I2C_WRITE_CR

    # Writing register address to I2CMaster 2
    writeReg(getNode("LPGBT.RW.I2C.I2CM2DATA0"), reg_addr, 0)
    writeReg(getNode("LPGBT.RW.I2C.I2CM2CMD"), 0x8, 0) # I2C_W_MULTI_4BYTE0

    writeReg(getNode("LPGBT.RW.I2C.I2CM2ADDRESS"), vtrx_slave_addr, 0)
    writeReg(getNode("LPGBT.RW.I2C.I2CM2CMD"), 0xC, 0) # I2C_WRITE_MULTI

    success=0
    while(success==0):
        # Status register of I2CMaster 2
        if system!="dryrun":
            status = readReg(getNode("LPGBT.RO.I2CREAD.I2CM2STATUS"))
        else:
            status = 0x04
        if (status>>6) & 0x1:
            print ("ERROR: Last transaction was not acknowledged by the I2C slave")
            rw_terminate()
        elif (status>>3) & 0x1:
            print ("ERROR: I2C master port finds that the SDA line is pulled low 0 before initiating a transaction. Indicates a problem with the I2C bus.")
            rw_terminate()
        success = (status>>2) & 0x1

    # Reading the register value to I2CMaster 2
    nbytes = 1
    control_register_data = nbytes<<2 | 0 # using 100 kHz
    writeReg(getNode("LPGBT.RW.I2C.I2CM2DATA0"), control_register_data, 0)
    writeReg(getNode("LPGBT.RW.I2C.I2CM2CMD"), 0x0, 0) # I2C_WRITE_CR

    writeReg(getNode("LPGBT.RW.I2C.I2CM2ADDRESS"), vtrx_slave_addr, 0)
    writeReg(getNode("LPGBT.RW.I2C.I2CM2CMD"), 0xD, 0) # I2C_READ_MULTI
    
    success=0
    while(success==0):
        # Status register of I2CMaster 2
        if system!="dryrun":
            status = readReg(getNode("LPGBT.RO.I2CREAD.I2CM2STATUS"))
        else:
            status = 0x04
        if (status>>6) & 0x1:
            print ("ERROR: Last transaction was not acknowledged by the I2C slave")
            rw_terminate()
        elif (status>>3) & 0x1:
            print ("ERROR: I2C master port finds that the SDA line is pulled low 0 before initiating a transaction. Indicates a problem with the I2C bus.")
            rw_terminate()
        success = (status>>2) & 0x1
    
    data = readReg(getNode("LPGBT.RO.I2CREAD.I2CM2READ15"))
    reg_addr_string = "0x%02X" % (reg_addr)
    data_string = "0x%02X" % (data)
    print ("Successful read from slave register: " + reg_addr_string + ", data: " + data_string + " (" + '{0:08b}'.format(data) + ")")
    return data



def main(system, boss, channel, enable, reg_list, data_list):

    # Readback rom register to make sure communication is OK
    if system!="dryrun":
        check_rom_readback()

    if not boss:
        print ("ERROR: VTRX+ control only for boss since I2C master of boss connected to VTRX+")
        return

    # Enabling TX Channel
    if channel is not None and enable is not None:
        en = 0
        if int(enable):
            print ("Enabling channel: "+channel)
            en = 1
        else:
            print ("Disabling channel: "+channel)
        enable_status = i2cmaster_read(system, enable_reg)
        enable_channel_bit = TX_enable_bit[channel]
        enable_mask = 1 << enable_channel_bit
        enable_data = (enable_status & (~enable_mask)) | (en << enable_channel_bit)     
        i2cmaster_write(system, enable_reg, enable_data)
        enable_status = i2cmaster_read(system, enable_reg)
        print ("")
 
    if len(reg_list) == 0:
        return

    # Reading registers
    print ("Initial Reading of VTRX+ registers: ")
    for reg in reg_list:
        data = i2cmaster_read(system, reg)
    print ("")
    
    if len(data_list) == 0:
        return
    
    # Writing registers
    print ("Writing to VTRX+ registers: ")
    for i, reg in enumerate(reg_list):
        i2cmaster_write(system, reg, data_list[i])
    print ("")  

    # Reading registers
    print ("Final Reading of VTRX+ registers: ")
    for reg in reg_list:
        data = i2cmaster_read(system, reg)
    print ("")
    


def check_rom_readback():
    romreg=readReg(getNode("LPGBT.RO.ROMREG"))
    if (romreg != 0xA5):
        print ("ERROR: no communication with LPGBT. ROMREG=0x%x, EXPECT=0x%x" % (romreg, 0xA5))
        rw_terminate()
    else:
        print ("Successfully read from ROM. I2C communication OK")



if __name__ == '__main__':
    # Parsing arguments
    parser = argparse.ArgumentParser(description='LPGBT VTRX+ CONTROL')
    parser.add_argument("-s", "--system", action="store", dest="system", help="system = chc or backend or dongle or dryrun")
    parser.add_argument("-l", "--lpgbt", action="store", dest="lpgbt", help="lpgbt = only boss allowed")
    parser.add_argument("-t", "--type", action="store", dest="type", help="type = reg or name")
    parser.add_argument("-r", "--reg", action="store", nargs='+', dest="reg", help="reg = list of registers to read/write; only use with type: reg")
    parser.add_argument("-c", "--channel", action="store", dest="channel", help="channel = TX1, TX2, TX3, TX4; only use with type: name")
    parser.add_argument("-e", "--enable", action="store", dest="enable", help="enable = 0 or 1; only use with type: name")
    parser.add_argument("-n", "--name", action="store", dest="name", nargs='+', help="name = biascur_reg, modcur_reg, empamp_reg; only use with type: name")
    parser.add_argument("-d", "--data", action="store", nargs='+', dest="data", help="data = list of data values to write")
    args = parser.parse_args()

    if args.system == "chc":
        print ("Using Rpi CHeeseCake for checking configuration")
    elif args.system == "backend":
        #print ("Using Backend for checking configuration")
        print ("Only chc (Rpi Cheesecake) or dryrun supported at the moment")
        sys.exit()
    elif args.system == "dongle":
        #print ("Using USB Dongle for checking configuration")
        print ("Only chc (Rpi Cheesecake) or dryrun supported at the moment")
        sys.exit()
    elif args.system == "dryrun":
        print ("Dry Run - not actually running on lpGBT")
    else:
        print ("Only valid options: chc, backend, dongle, dryrun")
        sys.exit()

    boss = None
    if args.lpgbt is None:
        print ("Please select boss")
        sys.exit()
    elif (args.lpgbt=="boss"):
        print ("VTRX+ control for boss")
        boss=1
    elif (args.lpgbt=="sub"):
        print ("VTRX+ control only for boss since I2C master of boss connected to VTRX+")
        boss=0
        sys.exit()
    else:
        print ("Please select boss")
        sys.exit()
    if boss is None:
        sys.exit()

    reg_list = []
    data_list = []
    if args.type == None:
        print ("Enter type")
        sys.exit()
    elif args.type == "reg":
        if args.channel is not None or args.name is not None:
            print ("For type reg only register values can be given")
            sys.exit()
        if args.enable is not None:
            print ("Enable option not available for type: reg")
            sys.exit()
        if args.reg == None:
            print ("Enter registers to read/write")
            sys.exit()
        for reg in args.reg:
            if int(reg,16) > 255:
                print ("Register address can only be 8 bit")
                sys.exit()
            reg_list.append(int(reg,16))
    elif args.type == "name":
        if args.reg is not None:
            print ("For type name only channel, enable or name can be given")
            sys.exit()
        if args.channel == None:
            print ("Enter channel")
            sys.exit()          
        if args.enable is not None:
            if args.enable not in ["0", "1"]:
                print ("Enter valid value for enable: 0 or 1")
                sys.exit()
        if args.enable is None and args.name == None:
            print ("Enter enable option or register name")
            sys.exit() 
        if args.channel not in ["TX1", "TX2", "TX3", "TX4"]:
            print ("Only allowed channels: TX1, TX2, TX3, TX4")
            sys.exit()
        if args.name is not None:
            for name in args.name:
                if name not in ["biascur_reg", "modcur_reg", "empamp_reg"]:
                    print ("Invalid register name")
                    sys.exit()
                reg_list.append(TX_reg[args.channel][name])
    else:
        print ("Only allowed type: reg, name")
        sys.exit()


    if args.data is not None:
        if len(reg_list) != len(args.data):
            print ("Number of registers and data values do not match")
            sys.exit()
        for data in args.data:
            if int(data,16) > 255:
                print ("Data value can only be 8 bit")
                sys.exit()
            data_list.append(int(data,16))
            
    # Parsing Registers XML File
    print("Parsing xml file...")
    parseXML()
    print("Parsing complete...")

    # Initialization (for CHeeseCake: reset and config_select)
    rw_initialize(args.system, boss)
    print("Initialization Done\n")

    try:
        main(args.system, boss, args.channel, args.enable, reg_list, data_list)
    except KeyboardInterrupt:
        print ("\nKeyboard Interrupt encountered")
        rw_terminate()
    except EOFError:
        print ("\nEOF Error")
        rw_terminate()

    # Termination
    rw_terminate()

