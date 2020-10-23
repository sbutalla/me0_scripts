import sys
from time import sleep,time
import cProfile

import platform
hostname = platform.uname()[1]
if ("eagle" in hostname):
    from rw_reg_lgpbt_ctp7 import *
else:
    from rw_reg_dongle import *

readback = 0
master = 0
minimal = 0
spicy = 0
reset_before_config=0

FUSE_TIMEOUT_MS = 1000
TOTAL_EFUSE_ON_TIME_MS = 0

def main(do_readback=0):

    gbt.gbtx_disable_efusepower()

    readback = do_readback

    global master

    print "Parsing xml file..."
    parseXML()
    print "Parsing complete..."

    ########################################################
    # readback rom register to make sure communication is OK
    ########################################################
    check_rom_readback()
    ########################################################

    if len(sys.argv) < 2:
        print "Please select master or slave"
        return
    elif (sys.argv[1]=="master"):
        print "Configuring LPGBT as master"
        master=1
        minimal=0
    elif (sys.argv[1]=="master_minimal"):
        print "Configuring minimally LPGBT as master"
        master=1
        minimal=1
    elif (sys.argv[1]=="slave"):
        print "Configuring LPGBT as slave"
        master=0
    elif (sys.argv[1]=="slave_minimal"):
        print "Configuring minimally LPGBT as slave"
        master=0
        minimal=1
    elif (sys.argv[1]=="fuseid"):
        fuse_chip_id()
        sys.exit()
    elif len(sys.argv)==3 and (sys.argv[1]=="fuse_from_file"):
        fuse_from_file (sys.argv[2])
        sys.exit()
    elif len(sys.argv)==3 and (sys.argv[1]=="config_from_file"):
        config_from_file (sys.argv[2])
        sys.exit()
    elif (sys.argv[1]=="fuse_minimal_config"):
        fuse_minimal_config()
        sys.exit()
    else:
        print "instructions to come..."
        sys.exit()

    mpoke (0x007,(0xFEEDBEEF >> 0)  & 0xff) #[0x007] USERID3 BITS [ 7: 0]
    mpoke (0x006,(0xFEEDBEEF >> 8)  & 0xff) #[0x006] USERID2 BITS [15: 8]
    mpoke (0x005,(0xFEEDBEEF >> 16) & 0xff) #[0x005] USERID1 BITS [23:16]
    mpoke (0x004,(0xFEEDBEEF >> 24) & 0xff) #[0x004] USERID0 BITS [31:24]

    # optionally reset LPGBT
    if (reset_before_config):
        reset_lpgbt()

    configure_lpgbt(readback, minimal)

    if (len(sys.argv)==3):
        if (sys.argv[2]=="spicy"):
            invert_the_extra_spicy(1)
        if (sys.argv[2]=="classic"):
            invert_the_extra_spicy(0)

def configure_lpgbt(readback, minimal=False):
    configure_base()

    if not minimal:
        # eportrx dll configuration
        configure_eport_dlls()

        # eportrx channel configuration
        configure_eprx()

    # configure downlink
    if (master):
        configure_downlink()

    if not minimal:
        # configure eport tx
        if (master):
            configure_eptx()

        # configure phase shifter on master lpgbt
        if (master):
            configure_phase_shifter()

        # configure ec channels
        configure_ec_channel()

    # invert relevant hsio and eptx
    invert_hsio()

    if not minimal:
        invert_eptx()
        #invert_eprx()

        # configure reset + led outputs
        configure_gpio()

    mpoke (0x0ed, 0x03)
    mpoke (0x0ee, 0x30)

    #set_uplink_group_data_source("normal", pattern=0x55555555)

    print ("Configuration finished... asserting config done")

    set_config_done()

    if (master):
        write_config_file("config_master.txt")
    else:
        write_config_file("config_slave.txt")

def config_from_file (filename):
   f = open (filename, "r")
   config = f.read()
   config = config.split('\n')
   data = 0x0

   for reg_addr in range(0,len(config)-1):
      value = int(config[reg_addr],16)
      print("wr(0x%04X,0x%02X)" % (reg_addr,value))
      mpoke (reg_addr,value)

def fuse_from_file (filename):
   f = open (filename, "r")
   config = f.read()
   config = config.split('\n')
   data = 0x0

   write_fuse_magic(1)

   print "Fusing from file \"%s\"" % filename
   en="No"
   while (en!="yes"):
        en = raw_input ("please type \"yes\" to continue: ")

   for reg_addr in range(0,len(config)-1):

      #maximum fusible register
      #DONT FUSE 0xEF HERE.. put it in a separate function for safety w/ updateEnable
      if (reg_addr >= 0xef):
         return

      if (reg_addr%4==0):
         data=0

      value = int(config[reg_addr],16)
      data  |= value << (8*reg_addr%4)

      if (reg_addr%4==3) and data != 0:
         write_blow_and_check_fuse (reg_addr & 0xfffc, data, True)

   write_fuse_magic(0)

def set_uplink_group_data_source(type, pattern=0x55555555):

    setting = 0
    if (type=="normal"):
        setting = 0
    elif(type=="prbs7"):
        setting = 1
    elif(type=="cntup"):
        setting = 2
    elif(type=="cntdown"):
        setting = 3
    elif(type=="pattern"):
        setting = 4
    elif(type=="invpattern"):
        setting = 5
    elif(type=="loopback"):
        setting = 6
    else:
        print "Setting invalid in set_uplink_group_data_source"
        print sys.exit()

    writeReg(getNode("LPGBT.RW.TESTING.ULG0DATASOURCE"), setting, readback) #
    writeReg(getNode("LPGBT.RW.TESTING.ULG1DATASOURCE"), setting, readback) #
    writeReg(getNode("LPGBT.RW.TESTING.ULG2DATASOURCE"), setting, readback) #
    writeReg(getNode("LPGBT.RW.TESTING.ULG3DATASOURCE"), setting, readback) #
    writeReg(getNode("LPGBT.RW.TESTING.ULG4DATASOURCE"), setting, readback) #
    writeReg(getNode("LPGBT.RW.TESTING.ULG5DATASOURCE"), setting, readback) #
    writeReg(getNode("LPGBT.RW.TESTING.ULG6DATASOURCE"), setting, readback) #

    if (setting==4 or setting==5):
        writeReg(getNode("LPGBT.RW.TESTING.DPDATAPATTERN0"), 0xff & (pattern>>0), readback) #
        writeReg(getNode("LPGBT.RW.TESTING.DPDATAPATTERN1"), 0xff & (pattern>>8), readback) #
        writeReg(getNode("LPGBT.RW.TESTING.DPDATAPATTERN2"), 0xff & (pattern>>16), readback) #
        writeReg(getNode("LPGBT.RW.TESTING.DPDATAPATTERN3"), 0xff & (pattern>>24), readback) #

def invert_the_extra_spicy(spicy=0):

    if (spicy==0):
        print ("Inverting clk/tx/rx for the classic slot...");
    else:
        print ("Inverting clk/tx/rx for the extra spicy slot...");

    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX_CHN_CONTROL.EPRX0INVERT"),  spicy, readback)
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX_CHN_CONTROL.EPRX1INVERT"),  spicy, readback)
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX_CHN_CONTROL.EPRX2INVERT"),  spicy, readback)
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX_CHN_CONTROL.EPRX3INVERT"),  spicy, readback)
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX_CHN_CONTROL.EPRX4INVERT"),  spicy, readback)
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX_CHN_CONTROL.EPRX5INVERT"),  spicy, readback)
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX_CHN_CONTROL.EPRX6INVERT"),  spicy, readback)
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX_CHN_CONTROL.EPRX7INVERT"),  spicy, readback)
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX_CHN_CONTROL.EPRX8INVERT"),  spicy, readback)
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX_CHN_CONTROL.EPRX9INVERT"),  spicy, readback)
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX_CHN_CONTROL.EPRX10INVERT"), spicy, readback)
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX_CHN_CONTROL.EPRX11INVERT"), spicy, readback)
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX_CHN_CONTROL.EPRX12INVERT"), spicy, readback)
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX_CHN_CONTROL.EPRX13INVERT"), spicy, readback)
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX_CHN_CONTROL.EPRX14INVERT"), spicy, readback)
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX_CHN_CONTROL.EPRX15INVERT"), spicy, readback)
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX_CHN_CONTROL.EPRX16INVERT"), spicy, readback)
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX_CHN_CONTROL.EPRX17INVERT"), spicy, readback)
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX_CHN_CONTROL.EPRX18INVERT"), spicy, readback)
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX_CHN_CONTROL.EPRX19INVERT"), spicy, readback)
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX_CHN_CONTROL.EPRX20INVERT"), spicy, readback)
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX_CHN_CONTROL.EPRX21INVERT"), spicy, readback)
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX_CHN_CONTROL.EPRX22INVERT"), spicy, readback)
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX_CHN_CONTROL.EPRX23INVERT"), spicy, readback)
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX_CHN_CONTROL.EPRX24INVERT"), spicy, readback)
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX_CHN_CONTROL.EPRX25INVERT"), spicy, readback)
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX_CHN_CONTROL.EPRX26INVERT"), spicy, readback)
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX_CHN_CONTROL.EPRX27INVERT"), spicy, readback)

    if (master):
        writeReg(getNode("LPGBT.RWF.EPORTTX.EPTX10INVERT"), 1^spicy, readback) #master 4
        writeReg(getNode("LPGBT.RWF.EPORTTX.EPTX23INVERT"), 1^spicy, readback) #master 11

        writeReg(getNode("LPGBT.RWF.EPORTTX.EPTX12INVERT"), spicy, readback) #master 6
        writeReg(getNode("LPGBT.RWF.EPORTTX.EPTX20INVERT"), spicy, readback) #master 8
        writeReg(getNode("LPGBT.RWF.EPORTTX.EPTX00INVERT"), spicy, readback) #master 0
        writeReg(getNode("LPGBT.RWF.EPORTTX.EPTX02INVERT"), spicy, readback) #master 2

    if (master):
        writeReg(getNode("LPGBT.RWF.EPORTCLK.EPCLK3INVERT"),  spicy, readback)
        writeReg(getNode("LPGBT.RWF.EPORTCLK.EPCLK5INVERT"),  spicy, readback)
        writeReg(getNode("LPGBT.RWF.EPORTCLK.EPCLK6INVERT"),  spicy, readback)
        writeReg(getNode("LPGBT.RWF.EPORTCLK.EPCLK7INVERT"),  spicy, readback)
        writeReg(getNode("LPGBT.RWF.EPORTCLK.EPCLK15INVERT"), spicy, readback)
        writeReg(getNode("LPGBT.RWF.EPORTCLK.EPCLK16INVERT"), spicy, readback)

def configure_eptx():
    #[0x0a7] EPTXDataRate
    writeReg(getNode("LPGBT.RWF.EPORTTX.EPTX0DATARATE"), 0x3, readback)
    writeReg(getNode("LPGBT.RWF.EPORTTX.EPTX1DATARATE"), 0x3, readback)
    writeReg(getNode("LPGBT.RWF.EPORTTX.EPTX2DATARATE"), 0x3, readback)
    writeReg(getNode("LPGBT.RWF.EPORTTX.EPTX3DATARATE"), 0x3, readback)

    #EPTXxxEnable
    writeReg(getNode("LPGBT.RWF.EPORTTX.EPTX12ENABLE"), 0x1, readback) #master 6
    writeReg(getNode("LPGBT.RWF.EPORTTX.EPTX10ENABLE"), 0x1, readback) #master 4
    writeReg(getNode("LPGBT.RWF.EPORTTX.EPTX20ENABLE"), 0x1, readback) #master 8
    writeReg(getNode("LPGBT.RWF.EPORTTX.EPTX00ENABLE"), 0x1, readback) #master 0
    writeReg(getNode("LPGBT.RWF.EPORTTX.EPTX23ENABLE"), 0x1, readback) #master 11
    writeReg(getNode("LPGBT.RWF.EPORTTX.EPTX02ENABLE"), 0x1, readback) #master 2

    #EPTXxxDriveStrength
    writeReg(getNode("LPGBT.RWF.EPORTTX.EPTX_CHN_CONTROL.EPTX6DRIVESTRENGTH"), 0x3, readback) #master 6
    writeReg(getNode("LPGBT.RWF.EPORTTX.EPTX_CHN_CONTROL.EPTX4DRIVESTRENGTH"), 0x3, readback) #master 4
    writeReg(getNode("LPGBT.RWF.EPORTTX.EPTX_CHN_CONTROL.EPTX8DRIVESTRENGTH"), 0x3, readback) #master 8
    writeReg(getNode("LPGBT.RWF.EPORTTX.EPTX_CHN_CONTROL.EPTX0DRIVESTRENGTH"), 0x3, readback) #master 0
    writeReg(getNode("LPGBT.RWF.EPORTTX.EPTX_CHN_CONTROL.EPTX11DRIVESTRENGTH"), 0x3, readback) #master 11
    writeReg(getNode("LPGBT.RWF.EPORTTX.EPTX_CHN_CONTROL.EPTX2DRIVESTRENGTH"), 0x3, readback) #master 2

    # enable mirror feature
    writeReg(getNode("LPGBT.RWF.EPORTTX.EPTX0MIRRORENABLE"), 0x1, readback)
    writeReg(getNode("LPGBT.RWF.EPORTTX.EPTX1MIRRORENABLE"), 0x1, readback)
    writeReg(getNode("LPGBT.RWF.EPORTTX.EPTX2MIRRORENABLE"), 0x1, readback)
    writeReg(getNode("LPGBT.RWF.EPORTTX.EPTX3MIRRORENABLE"), 0x1, readback)

    #turn on 320 MHz clocks

    writeReg(getNode("LPGBT.RWF.EPORTCLK.EPCLK3FREQ"),  0x4, readback)
    writeReg(getNode("LPGBT.RWF.EPORTCLK.EPCLK5FREQ"),  0x4, readback)
    writeReg(getNode("LPGBT.RWF.EPORTCLK.EPCLK6FREQ"),  0x4, readback)
    writeReg(getNode("LPGBT.RWF.EPORTCLK.EPCLK7FREQ"),  0x4, readback)
    writeReg(getNode("LPGBT.RWF.EPORTCLK.EPCLK15FREQ"), 0x4, readback)
    writeReg(getNode("LPGBT.RWF.EPORTCLK.EPCLK16FREQ"), 0x4, readback)

    writeReg(getNode("LPGBT.RWF.EPORTCLK.EPCLK3DRIVESTRENGTH"), 0x3, readback)
    writeReg(getNode("LPGBT.RWF.EPORTCLK.EPCLK5DRIVESTRENGTH"), 0x3, readback)
    writeReg(getNode("LPGBT.RWF.EPORTCLK.EPCLK6DRIVESTRENGTH"), 0x3, readback)
    writeReg(getNode("LPGBT.RWF.EPORTCLK.EPCLK7DRIVESTRENGTH"), 0x3, readback)
    writeReg(getNode("LPGBT.RWF.EPORTCLK.EPCLK15DRIVESTRENGTH"), 0x3, readback)
    writeReg(getNode("LPGBT.RWF.EPORTCLK.EPCLK16DRIVESTRENGTH"), 0x3, readback)


def invert_hsio():
    print ("Configuring pin inversion...")
    if (master):
        writeReg(getNode("LPGBT.RWF.CHIPCONFIG.HIGHSPEEDDATAININVERT"), 0x1, readback)
    else:
        writeReg(getNode("LPGBT.RWF.CHIPCONFIG.HIGHSPEEDDATAOUTINVERT"), 0x1, readback)

def invert_eptx():

    if (master):
        writeReg(getNode("LPGBT.RWF.EPORTTX.EPTX10INVERT"), 0x0, readback) #master 4
        writeReg(getNode("LPGBT.RWF.EPORTTX.EPTX23INVERT"), 0x0, readback) #master 11

#def invert_eprx(master, spicy):
#
#    inverted_sbits_master = [9, 4, 2, 0, 19, 17, 18, 20, 22, 24, 26]
#    inverted_sbits_slave  = [21, 23, 27, 25, 9, 10, 3, 5, 1, 12]
#
#    non_inverted_sbits_master = [6, 7, 5, 1, 3, 15, 14, 12, 10, 11, 13, 27, 16, 21, 23]
#    non_inverted_sbits_slave  = [18, 20, 22, 26, 17, 19, 14, 7, 15, 8, 11, 13, 0, 2, 4, 6]
#
#    inverted_vfatrx_master = [25]
#    inverted_vfatrx_slave  = [24]
#
#    non_inverted_vfatrx_master = [3, 27]
#    non_inverted_vfatrx_slave  = [11, 6]
#
#    # just do some sanity checks to make sure things are correct
#
#    for pair in inverted_sbits_master:
#        if (pair in non_inverted_sbits_master):
#            print "Duplicated pair listed in both inverted/non-inverted master sbits"
#
#    for pair in inverted_sbits_slave:
#        if (pair in non_inverted_sbits_slave):
#            print "Duplicated pair listed in both inverted/non-inverted slave sbits"
#
#    for pair in inverted_vfatrx_master:
#        if (pair in non_inverted_vfatrx_master):
#            print "Duplicated pair listed in both inverted/non-inverted master vfatrx"
#
#    for pair in inverted_vfatrx_slave:
#        if (pair in non_inverted_vfatrx_slave):
#            print "Duplicated pair listed in both inverted/non-inverted slave vfatrx"
#
#    if (len(inverted_sbits_master) + len(non_inverted_sbits_master) != 24):
#        print "Missing master s-bits"
#
#    if (len(inverted_sbits_slave) + len(non_inverted_sbits_slave) != 24):
#        print "Missing slave s-bits"
#
#    list = []
#
#    if (invert_sbits):
#
#        if (spicy):
#            if master:
#                list += non_inverted_sbits_master
#            else:
#                list += non_inverted_sbits_slave
#        else:
#            if master:
#                list += inverted_sbits_master
#            else:
#                list += inverted_sbits_slave
#
#    if (invert_vfatrx):
#
#        if (spicy):
#            if master:
#                list += non_inverted_vfatrx_master
#            else:
#                list += non_inverted_vfatrx_slave
#        else:
#            if master:
#                list += inverted_vfatrx_master
#            else:
#                list += inverted_vfatrx_slave
#
#    for pair in list:
#        writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX_CHN_CONTROL.EPRX%dINVERT"), 0x0, readback)


def configure_ec_channel():
    print ("Configuring external control channels...")

    # enable EC output
    writeReg(getNode("LPGBT.RWF.EPORTTX.EPTXECENABLE"), 0x1, readback)

    # enable EC input
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRXECENABLE"), 0x1, readback)
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRXECTERM"),   0x1, readback)

    if (master):
        # turn on 80 Mbps EC clock
        writeReg(getNode("LPGBT.RWF.EPORTCLK.EPCLK28FREQ"), 0x2, readback)
        writeReg(getNode("LPGBT.RWF.EPORTCLK.EPCLK28DRIVESTRENGTH"), 0x3, readback)
        writeReg(getNode("LPGBT.RWF.EPORTCLK.EPCLK28INVERT"), 0x1, readback)

        # enable EC output
        writeReg(getNode("LPGBT.RWF.EPORTTX.EPTXECDRIVESTRENGTH"), 0x3, readback)
        writeReg(getNode("LPGBT.RWF.EPORTRX.EPRXECPHASESELECT"), 0x0, readback)
    else:
        writeReg(getNode("LPGBT.RWF.EPORTRX.EPRXECPHASESELECT"), 0x0, readback)

def configure_gpio():
    print ("Configuring gpio...")
    if (master):
        writeReg(getNode("LPGBT.RWF.PIO.PIODIRH"), 0x80 | 0x01, readback) # set as outputs
        writeReg(getNode("LPGBT.RWF.PIO.PIODIRL"), 0x01 | 0x02, readback) # set as outputs
        writeReg(getNode("LPGBT.RWF.PIO.PIOOUTH"), 0x80, readback) # enable LED
        writeReg(getNode("LPGBT.RWF.PIO.PIOOUTL"), 0x00, readback) #
    else:
        writeReg(getNode("LPGBT.RWF.PIO.PIODIRH"), 0x02 | 0x04 | 0x08, readback) # set as outputs
        writeReg(getNode("LPGBT.RWF.PIO.PIODIRL"), 0x00 | 0x00, readback) # set as outputs
        writeReg(getNode("LPGBT.RWF.PIO.PIOOUTH"), 0x00, readback) #
        writeReg(getNode("LPGBT.RWF.PIO.PIOOUTL"), 0x00, readback) #

def configure_downlink():

    print "Configuring downlink..."

    #2.2.6. Downlink: Frame aligner settings (if high speed receiver is used)

    # downlink

    #[0x02f] FAMaxHeaderFoundCount
    writeReg(getNode("LPGBT.RWF.CALIBRATION.FAMAXHEADERFOUNDCOUNT"), 0xA, readback)
    #[0x030] FAMaxHeaderFoundCountAfterNF
    writeReg(getNode("LPGBT.RWF.CALIBRATION.FAMAXHEADERFOUNDCOUNTAFTERNF"), 0xA, readback)
    ##[0x031] FAMaxHeaderNotFoundCount
    writeReg(getNode("LPGBT.RWF.CALIBRATION.FAMAXHEADERNOTFOUNDCOUNT"), 0xA, readback)
    ##[0x032] FAFAMaxSkipCycleCountAfterNF
    writeReg(getNode("LPGBT.RWF.CALIBRATION.FAMAXSKIPCYCLECOUNTAFTERNF"), 0xA, readback)
    writeReg(getNode("LPGBT.RWF.CALIBRATION.EPRXUNLOCKTHRESHOLD"), 0x5, readback)

    writeReg(getNode("LPGBT.RWF.EQUALIZER.EQATTENUATION"), 0x3)


def configure_eprx():

    print "Configuring elink inputs..."
    # Enable Elink-inputs

    #set banks to 320 Mbps
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX0DATARATE"), 1, readback) # 1=320mbps in 10gbps mode
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX1DATARATE"), 1, readback) # 1=320mbps in 10gbps mode
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX2DATARATE"), 1, readback) # 1=320mbps in 10gbps mode
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX3DATARATE"), 1, readback) # 1=320mbps in 10gbps mode
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX4DATARATE"), 1, readback) # 1=320mbps in 10gbps mode
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX5DATARATE"), 1, readback) # 1=320mbps in 10gbps mode
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX6DATARATE"), 1, readback) # 1=320mbps in 10gbps mode

    #set banks to fixed phase
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX0TRACKMODE"), 0, readback) # 0 = fixed phase
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX1TRACKMODE"), 0, readback) # 0 = fixed phase
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX2TRACKMODE"), 0, readback) # 0 = fixed phase
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX3TRACKMODE"), 0, readback) # 0 = fixed phase
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX4TRACKMODE"), 0, readback) # 0 = fixed phase
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX5TRACKMODE"), 0, readback) # 0 = fixed phase
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX6TRACKMODE"), 0, readback) # 0 = fixed phase

    #enable inputs
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX00ENABLE"), 1, readback)
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX01ENABLE"), 1, readback)
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX02ENABLE"), 1, readback)
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX03ENABLE"), 1, readback)

    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX10ENABLE"), 1, readback)
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX11ENABLE"), 1, readback)
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX12ENABLE"), 1, readback)
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX13ENABLE"), 1, readback)

    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX20ENABLE"), 1, readback)
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX21ENABLE"), 1, readback)
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX22ENABLE"), 1, readback)
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX23ENABLE"), 1, readback)

    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX30ENABLE"), 1, readback)
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX31ENABLE"), 1, readback)
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX32ENABLE"), 1, readback)
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX33ENABLE"), 1, readback)

    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX40ENABLE"), 1, readback)
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX41ENABLE"), 1, readback)
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX42ENABLE"), 1, readback)
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX43ENABLE"), 1, readback)

    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX50ENABLE"), 1, readback)
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX51ENABLE"), 1, readback)
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX52ENABLE"), 1, readback)
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX53ENABLE"), 1, readback)

    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX60ENABLE"), 1, readback)
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX61ENABLE"), 1, readback)
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX62ENABLE"), 1, readback)
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX63ENABLE"), 1, readback)

    writeReg(getNode("LPGBT.RWF.CALIBRATION.PSDLLCONFIRMCOUNT"), 0x1, readback) # 4 40mhz clock cycles to confirm lock
    writeReg(getNode("LPGBT.RWF.CALIBRATION.PSDLLCURRENTSEL"), 0x1, readback)

    #enable 100 ohm termination
    for i in range (28):
        writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX_CHN_CONTROL.EPRX%dTERM" % i), 1, readback)

def reset_lpgbt():
    writeReg(getNode("LPGBT.RW.RESET.RSTPLLDIGITAL"), 1, readback)
    writeReg(getNode("LPGBT.RW.RESET.RSTFUSES"),      1, readback)
    writeReg(getNode("LPGBT.RW.RESET.RSTCONFIG"),     1, readback)
    writeReg(getNode("LPGBT.RW.RESET.RSTRXLOGIC"),    1, readback)
    writeReg(getNode("LPGBT.RW.RESET.RSTTXLOGIC"),    1, readback)

    writeReg(getNode("LPGBT.RW.RESET.RSTPLLDIGITAL"), 0, readback)
    writeReg(getNode("LPGBT.RW.RESET.RSTFUSES"),      0, readback)
    writeReg(getNode("LPGBT.RW.RESET.RSTCONFIG"),     0, readback)
    writeReg(getNode("LPGBT.RW.RESET.RSTRXLOGIC"),    0, readback)
    writeReg(getNode("LPGBT.RW.RESET.RSTTXLOGIC"),    0, readback)

def check_rom_readback():
    romreg=readReg(getNode("LPGBT.RO.ROMREG"))
    if (romreg != 0xa5):
        print "Error: no communication with LPGBT. ROMREG=0x%x, EXPECT=0x%x" % (romreg, 0xa5)
        sys.exit()
    else:
        print "Successfully read from ROM. I2C communication OK"

def configure_eport_dlls():
    print "Configuring eport dlls..."
    #2.2.2. Uplink: ePort Inputs DLL's
    #[0x034] EPRXDllConfig
    writeReg(getNode("LPGBT.RWF.CALIBRATION.EPRXDLLCURRENT"), 0x1, readback)
    writeReg(getNode("LPGBT.RWF.CALIBRATION.EPRXDLLCONFIRMCOUNT"), 0x1, readback)
    writeReg(getNode("LPGBT.RWF.CALIBRATION.EPRXDLLFSMCLKALWAYSON"), 0x0, readback)
    writeReg(getNode("LPGBT.RWF.CALIBRATION.EPRXDLLCOARSELOCKDETECTION"), 0x0, readback)
    writeReg(getNode("LPGBT.RWF.CALIBRATION.EPRXENABLEREINIT"), 0x0, readback)
    writeReg(getNode("LPGBT.RWF.CALIBRATION.EPRXDATAGATINGENABLE"), 0x1, readback)

def configure_base():

    #   Enable PowerGood @ 1.0 V, Delay 100 ms:
    mpoke(0x03e,0xdc)

    #Configure ClockGen Block:
    mpoke(0x01f,0x55)
    mpoke(0x020,0xc8)
    mpoke(0x021,0x24) #was 0x24
    mpoke(0x022,0x44)
    mpoke(0x023,0x55)
    mpoke(0x024,0x55)
    mpoke(0x025,0x55)
    mpoke(0x026,0x55)
    mpoke(0x027,0x55)
    mpoke(0x028,0x0f)
    mpoke(0x029,0x00) # was 0x00
    mpoke(0x02a,0x00) # was 0x00
    mpoke(0x02b,0x00)
    mpoke(0x02c,0x88)
    mpoke(0x02d,0x89)
    mpoke(0x02e,0x99)

    # enabled fec counter for the downlink
    mpoke(0x132,0x10)

    # Set H.S. Uplink Driver current:
    mpoke(0x039,0x20)

    # Select TO0 internal signal:
    #mpoke(0x133,2) #40 mhz clock

def set_config_done():
    # Finally, Set pll&dllConfigDone to run chip:
    mpoke(0x0ef,0x06)

def configure_phase_shifter():
    # turn on phase shifter clock
    writeReg(getNode("LPGBT.RWF.PHASE_SHIFTER.PS1DELAY_8"), 0x0, readback)
    writeReg(getNode("LPGBT.RWF.PHASE_SHIFTER.PS1DELAY_7TO0"), 0x0, readback)
    writeReg(getNode("LPGBT.RWF.PHASE_SHIFTER.PS1ENABLEFINETUNE"), 0x0, readback)
    writeReg(getNode("LPGBT.RWF.PHASE_SHIFTER.PS1DRIVESTRENGTH"), 0x3, readback)
    writeReg(getNode("LPGBT.RWF.PHASE_SHIFTER.PS1FREQ"), 0x1, readback)
    writeReg(getNode("LPGBT.RWF.PHASE_SHIFTER.PS1PREEMPHASISMODE"), 0x0, readback)

#return 1 if check is ok
def check_fuse_block_data(adr, data, fullblock=False):

    fuse_block_adr    = adr & 0xfffc
    fuse_block_subadr = adr % 4

    mpoke(0x10e, 0xff&(fuse_block_adr>>8)) # adr high bits 15:8 [0x10e] FUSEBlowAddH
    mpoke(0x10f, 0xff&(fuse_block_adr>>0)) # adr low bits 7:0 [0x10f] FUSEBlowAddL

    # write fuseread on
    # [0x109] FUSEControl
    # Bit 7:4 - FuseBlowPulseLength[3:0] - Duration of fuse blowing pulse (default:12).
    # Bit 1 - FuseRead - Execute fuse readout sequence.
    # Bit 0 - FuseBlow - Execute fuse blowing sequence.
    mpoke(0x109, 0xC2)


    valid = False
    while (not valid):
        valid = (0x1 & ((mpeek(0x1a1)) >> 2))

    read=4*[0]

    read[0] = mpeek(0x1a2) # [0x1a2] FUSEValuesA
    read[1] = mpeek(0x1a3) # [0x1a3] FUSEValuesB
    read[2] = mpeek(0x1a4) # [0x1a4] FUSEValuesC
    read[3] = mpeek(0x1a5) # [0x1a5] FUSEValuesD

    # write fuseread off
    # [0x109] FUSEControl
    # Bit 7:4 - FuseBlowPulseLength[3:0] - Duration of fuse blowing pulse (default:12).
    # Bit 1 - FuseRead - Execute fuse readout sequence.
    # Bit 0 - FuseBlow - Execute fuse blowing sequence.
    mpoke(0x109, 0xC0)

    read_dword = 0

    if (fullblock):
        read_dword = (read[0]) | (read[1]<<8) | (read[2] << 16) | (read[3] << 24);
    else:
        read_dword = read[fuse_block_subadr]

    print "\tCHECKING FUSE ADR=%X, BLOCK=%X sub%X, VALID=%d, DATA_EXPECT=%X, DATA_READ=%X" % (adr, fuse_block_adr, fuse_block_subadr, valid, data, read_dword)
    return data==read_dword

def write_fuse_block_data(adr, data, fullblock=False):

    fuse_block_adr    = adr & 0xfffc
    fuse_block_subadr = adr % 4

    ok = 1

    # write address
    ok &= writeAndCheckAddr(0x10e, 0xff&(fuse_block_adr>>8)) # [0x10e] FUSEBlowAddH
    ok &= writeAndCheckAddr(0x10f, 0xff&(fuse_block_adr>>0)) # [0x10f] FUSEBlowAddL

    # zero out the rest of the address block to prevent accidental fusing
    if (not fullblock):
       ok &= writeAndCheckAddr(0x10A, 0)
       ok &= writeAndCheckAddr(0x10B, 0)
       ok &= writeAndCheckAddr(0x10C, 0)
       ok &= writeAndCheckAddr(0x10D, 0)

    if (fullblock):
        ok &= writeAndCheckAddr(0x10A, 0xff & (data >> 0))
        ok &= writeAndCheckAddr(0x10B, 0xff & (data >> 8))
        ok &= writeAndCheckAddr(0x10C, 0xff & (data >> 16))
        ok &= writeAndCheckAddr(0x10D, 0xff & (data >> 24))

    else:
        if (fuse_block_subadr==0):
            ok &= writeAndCheckAddr(0x10A, data)
        elif (fuse_block_subadr==1):
            ok &= writeAndCheckAddr(0x10B, data)
        elif (fuse_block_subadr==2):
            ok &= writeAndCheckAddr(0x10C, data)
        elif (fuse_block_subadr==3):
            ok &= writeAndCheckAddr(0x10D, data)

    if (not ok):
        print "Failed to read back fuse wdata block"
        sys.exit()

    return ok


def blow_fuse():
    global TOTAL_EFUSE_ON_TIME_MS

    adr = 0;

    adr |= mpeek (0x10e) << 8
    adr |= mpeek (0x10f) << 0

    rd = 0;
    rd |= mpeek(0x10A) << 0
    rd |= mpeek(0x10B) << 8
    rd |= mpeek(0x10C) << 16
    rd |= mpeek(0x10D) << 24
    print ("Blowing Fuse with ADR=%04X, DATA=%08X" % (adr, rd))

    mpoke(0x109, 0xC0)
    #gbt.gbtx_enable_efusepower()
    t0_efusepower = time()

    # https://pdf1.alldatasheet.com/datasheet-pdf/view/931712/TI1/LP2985A.html
    #sleep (0.01) # datasheet says the startup time is around 10ms with 150mA load (we have almost no load when using PIZZA)

    # write fuseblow on
    # [0x109] FUSEControl
    # Bit 7:4 - FuseBlowPulseLength[3:0] - Duration of fuse blowing pulse (default:12).
    # Bit 1 - FuseRead - Execute fuse readout sequence.
    # Bit 0 - FuseBlow - Execute fuse blowing sequence.
    mpoke(0x109, 0xC1) # wr

    #wait for fuseblowdone
    done = 0;
    t0 = time()
    while (done==0):
        done = (0x1 & ((mpeek(0x1a1)) >> 1))
        if int(round((time() - t0) * 1000)) > FUSE_TIMEOUT_MS:
            gbt.gbtx_disable_efusepower()
            mpoke(0x109, 0xC0) # wr
            TOTAL_EFUSE_ON_TIME_MS += int(round((time() - t0_efusepower) * 1000))
            print "ERROR: Fusing operation took longer than %dms and was terminated due to a timeout" % FUSE_TIMEOUT_MS
            print "Total efuse power on time: %dms" % TOTAL_EFUSE_ON_TIME_MS
            sys.exit()


    gbt.gbtx_disable_efusepower()
    TOTAL_EFUSE_ON_TIME_MS += int(round((time() - t0_efusepower) * 1000))
    print "Total efuse power on time: %dms" % TOTAL_EFUSE_ON_TIME_MS

    err = (0x1 & ((mpeek(0x1a1)) >> 3))
    print "\tFuse blown, err=%d" % err

    # write fuseblow on
    # [0x109] FUSEControl
    # Bit 7:4 - FuseBlowPulseLength[3:0] - Duration of fuse blowing pulse (default:12).
    # Bit 1 - FuseRead - Execute fuse readout sequence.
    # Bit 0 - FuseBlow - Execute fuse blowing sequence.
    mpoke(0x109, 0xC0) # wr

# sets fuse value, blows the fuse, and checks the result
# it can operate on a sub-address (one byte out of 4 in the fuse block)
# whenever fullblock is set to false
def write_blow_and_check_fuse  (adr,data,fullblock=False):
   if write_fuse_block_data(adr, data, fullblock):
      blow_fuse()
      check_fuse_block_data(adr,data,fullblock)

def write_fuse_magic(fuse_enable):
    value = 0
    if (fuse_enable):
        value = 0xA3
    #Load a magic number 0xA3 to the REG_FUSEMAGIC register to unlock fuse blowing.
    # [0x110] FuseMagic [7:0]
    mpoke(0x110, value) # wr

def fuse_chip_id():

   print ("Fusing chip ID and user ID...")

   #ans = raw_input("enter chip ID to fuse: ")
   #chip_id = int(ans, 0)
   #print ("fusing with chip id 0x%08X: " % chip_id)

   ans = raw_input("enter user ID to fuse: ")
   user_id = int(ans, 0)
   print ("fusing with user id 0x%08X: " % user_id)

   print ("INITIATING FUSING PROCEDURE OF CHIPID + USERID REGISTER")

   en="No"
   while (en!="yes"):
        en = raw_input ("please type \"yes\" to continue: ")

   write_fuse_magic(True)

   #Load fuse address into the REG_FUSEBLOWADDL and REG_FUSEBlowAddH registers.

   write_blow_and_check_fuse (0x003,(0 >> 0)  & 0xff) #[0x003] CHIPID3 BITS [ 7: 0]
   write_blow_and_check_fuse (0x002,(0 >> 8)  & 0xff) #[0x002] CHIPID2 BITS [15: 8]
   write_blow_and_check_fuse (0x001,(0 >> 16) & 0xff) #[0x001] CHIPID1 BITS [23:16]
   write_blow_and_check_fuse (0x000,(0 >> 24) & 0xff) #[0x000] CHIPID0 BITS [31:24]

   write_blow_and_check_fuse (0x007,(user_id >> 0)  & 0xff) #[0x007] USERID3 BITS [ 7: 0]
   write_blow_and_check_fuse (0x006,(user_id >> 8)  & 0xff) #[0x006] USERID2 BITS [15: 8]
   write_blow_and_check_fuse (0x005,(user_id >> 16) & 0xff) #[0x005] USERID1 BITS [23:16]
   write_blow_and_check_fuse (0x004,(user_id >> 24) & 0xff) #[0x004] USERID0 BITS [31:24]

   write_fuse_magic(False)

def fuse_minimal_config():

   # [0x020] CLKGConfig0
   # Bit 7:4 - CLKGCalibrationEndOfCount[3:0] - Selects the VCO calibration race goal in number of clock cycles between refClk (refClkCounter) and vco_40MHz (vcoClkCounter) (2^(CLKGCalibrationEndOfCount[3:0]+1)); default: 12
   # Bit 3:0 - CLKGBiasGenConfig[3:0] - Bias DAC for the charge pumps [0 : 8 : 120] uA; default: 8
   write_blow_and_check_fuse(0x020, 0xC8)

   # [0x025] CLKGCDRPropCur
   # Bit 7:4 - CLKGCDRPropCurWhenLocked[3:0] - CDR's Alexander phase detector proportional current path when in locked state [0 : 5.46 : 82] uA; default: 5
   # Bit 3:0 - CLKGCDRPropCur[3:0] - CDR's Alexander phase detector proportional current path when in locking state [0 : 5.46 : 82] uA; default: 5
   write_blow_and_check_fuse(0x025, 0x55)

   # [0x026] CLKGCDRIntCur
   # Bit 7:4 - CLKGCDRIntCurWhenLocked[3:0] - CDR's Alexander phase detector integral current path when in locked state [0 : 5.46 : 82] uA; default: 5
   # Bit 3:0 - CLKGCDRIntCur[3:0] - CDR's Alexander phase detector integral integral current path when in locking state [0 : 5.46 : 82] uA; default: 5
   write_blow_and_check_fuse(0x026, 0x55)

   # [0x039] LDConfigH
   # Line driver configuration register
   # Bit 7 - LDEmphasisEnable - Enable pre-emphasis in the line driver. The amplitude of the pre-emphasis is controlled by LDEmphasisAmp[6:0] and the duration by LDEmphasisShort.
   # Bit 6:0 - LDModulationCurrent[6:0] - Sets high-speed line driver modulation current: Im = 137 uA * LDModulationCurrent[6:0]
   write_blow_and_check_fuse(0x039, 0x20)

def fuse_powerup_register():

   fuse_enable=False

   print ("INITIATING FUSING PROCEDURE OF POWERUP REGISTER")
   print ("ONCE THIS REGISTER IS FUSED YOU CANNOT FUSE ANY MORE REGISTERS")
   print ("please type \"yes\" to continue: ")
   if (input=="yes"):
      fuse_enable=True
   else:
      fuse_enable=False

   if not fuse_enable:
      sys.exit()

   print ("Are you SURE??? type \"yes\" to continue: ")
   if (input=="yes"):
      fuse_enable=True
   else:
      fuse_enable=False

   if not fuse_enable:
      sys.exit()

   # [0x0ef] POWERUP2
   # Controls behavior of the power up state machine (for more details refer to Power-up state machine)
   # Bit 2 - dllConfigDone - When asserted, the power up state machine is allowed to proceed to PLL initialization. Please refer Configuration for more details.
   # Bit 1 - pllConfigDone - When asserted, the power up state machine is allowed to proceed to initialization of components containing DLLs (ePortRx, phase-shifter). Please refer Configuration for more details.
   # Bit 0 - updateEnable - When asserted, the power up state machine copies the values from fuses to configuration registers during power. Please refer Configuration for more details.

   #do NOT enable this until we are sure!!!
   #write_blow_and_check_fuse(0x0EF, 0x07)

if __name__ == '__main__':

   print "=================================="
   print "Writing register configuration..."
   print "=================================="

   #cProfile.run('main(0)')
   main(0)

   print "=================================="
   print "Checking register configuration..."
   print "=================================="

   main(1)

   pusmstate = readReg(getNode("LPGBT.RO.PUSM.PUSMSTATE"))
   if (pusmstate==18):
       print "LPGBT status is READY"
