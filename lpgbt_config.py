from rw_reg_dongle_chc import mpeek,mpoke,writeReg,readReg,getNode,parseXML,chc_initialize,chc_terminate
from time import sleep
import sys
import argparse

def main(system, boss, cernconfig, configure_elinks, force_pusm_ready, reset_before_config, watchdog_disable, loopback, override_lockcontrol, override_cdr, readback=0):
    print ("Parsing xml file...")
    parseXML()
    print ("Parsing complete...")

    # Initiliazing Cheesecake (reset and config_select)
    if system == "chc":
        initialize_success = chc_initialize(boss)
        if not initialize_success:
            print ("Problem in setting config select")
            sys.exit()

    # readback rom register to make sure communication is OK
    check_rom_readback(system)

    # optionally reset LPGBT
    if (reset_before_config):
        reset_lpgbt(readback, system)

    if cernconfig:
        # cern configuration
        configLPGBT(readback, system)
    else:
        # basic configuration
        configure_base(boss, readback, override_lockcontrol, system)

    # eportrx dll configuration
    configure_eport_dlls(readback, system)

    # eportrx channel configuration
    if (configure_elinks):
        configure_eprx(readback, system)

    # configure downlink
    if (boss):
        configure_downlink(boss, readback, system)

    # configure eport tx
    if (boss and configure_elinks):
        configure_eptx(readback, system)

    # configure phase shifter on boss lpgbt
    configure_phase_shifter(boss, readback, system)

    # configure ec channels
    #configure_ec_channel(boss, readback, system)

    # invert hsio and eptx
    invert_hsio(boss, readback, system)
    #invert_eptx(boss, readback, system)

    # set line driver current
    writeReg(getNode("LPGBT.RWF.LINE_DRIVER.LDMODULATIONCURRENT"), 32, readback, system) #[0x039] LDConfigH

    # configure reset + led outputs
    configure_gpio(boss, readback, loopback, watchdog_disable, force_pusm_ready, override_cdr, system)

    set_uplink_group_data_source("normal", readback, system, pattern=0x55555555)

    print ("Configuration finished... asserting config done")
    # Finally, Set pll&dllConfigDone to run chip:
    writeReg(getNode("LPGBT.RWF.POWERUP.DLLCONFIGDONE"), 0x1, readback, system)
    writeReg(getNode("LPGBT.RWF.POWERUP.PLLCONFIGDONE"), 0x1, readback, system)

    # Terminating Cheesecake
    if system=="chc":
        chc_terminate()

def configLPGBT(readback, system):
    #parseXML()
    mpeek (0x1ca, system)

    #response1 = mpeek(0x141, system)
    #print ("Reading register 0x141 : 0x%.2x"%(response1))

    # Demonstrated control of RefClk termination:
    #mpoke(0x03b,0x01, system)

    #response2 = mpeek(0x03b, system)
    #print ("Reading register 0x03b : 0x%.2x"%(response2))

    # Configure ClockGen Block:
    mpoke(0x01f,0x55, system)
    mpoke(0x020,0xc8, system)
    mpoke(0x021,0x24, system) #was 0x24
    mpoke(0x022,0x44, system)
    mpoke(0x023,0x55, system)
    mpoke(0x024,0x55, system)
    mpoke(0x025,0x55, system)
    mpoke(0x026,0x55, system)
    mpoke(0x027,0x55, system)
    mpoke(0x028,0x0f, system)
    mpoke(0x029,0x00, system) # was 0x00
    mpoke(0x02a,0x00, system) # was 0x00
    mpoke(0x02b,0x00, system)
    mpoke(0x02c,0x88, system)
    mpoke(0x02d,0x89, system)
    mpoke(0x02e,0x99, system)

    # datapath configuration
    mpoke(0x132,0x10, system) # enabled fec counter for the downlink
    #mpoke(0x132,0x10 | 0x2, system) # enabled fec counter for the downlink

    #$# Uplink:  ePort Inputs DLL"s
    #$mpoke(0x034,0xa1, system)

    #$# Uplink: ePort Inputs Group 1 at 640 Mbps:
    #$mpoke(0x0c5,0x9a, system)
    #$mpoke(0x0d0,0x02, system)
    #$mpoke(0x0d2,0x02, system)

    # Set H.S. Uplink Driver current:
    mpoke(0x039,0x20, system)

    # Enable PowerGood @ 1.0 V, Delay 100 ms:
    mpoke(0x03e,0xdc, system)

    # Select TO0 internal signal:
    mpoke(0x133,2, system) #40 mhz clock

    # Setup & enable ch0 in eTx group 3:
    #mpoke(0x0a7,0x80, system)
    #mpoke(0x0b8,0x03, system)
    #mpoke(0x0aa,0x10, system)

    # Select test pattern for eTx group 3: (initial value from Ted : 0x40 (PRBS), 0xc0 = constant, 0x80 = binary)
    #mpoke(0x11d,0x40, system)

    writeReg(getNode("LPGBT.RWF.CHIPCONFIG.HIGHSPEEDDATAININVERT"), 0x1, readback, system)
    writeReg(getNode("LPGBT.RWF.CHIPCONFIG.HIGHSPEEDDATAOUTINVERT"), 0x0, readback, system)

    writeReg(getNode("LPGBT.RWF.CALIBRATION.FAMAXHEADERFOUNDCOUNT"), 0xA, readback, system)
    writeReg(getNode("LPGBT.RWF.CALIBRATION.FAMAXHEADERFOUNDCOUNTAFTERNF"), 0xA, readback, system)
    writeReg(getNode("LPGBT.RWF.CALIBRATION.FAMAXHEADERNOTFOUNDCOUNT"), 0xA, readback, system)
    writeReg(getNode("LPGBT.RWF.CALIBRATION.FAMAXSKIPCYCLECOUNTAFTERNF"), 0xA, readback, system)

    writeReg(getNode("LPGBT.RWF.CALIBRATION.EPRXUNLOCKTHRESHOLD"), 0x5, readback, system)

    writeReg(getNode("LPGBT.RWF.EQUALIZER.EQATTENUATION"), 0x3, readback, system)
    #writeReg(getNode("LPGBT.RW.BERT.SKIPDISABLE"),1, readback, system)
    #writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGDISABLEFRAMEALIGNERLOCKCONTROL"), 0x1, readback, system)
    #writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGLOCKFILTERENABLE"), 0x0, readback, system)
    #writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGWAITCDRTIME"), 0xa, readback, system)
    #writeReg(getNode("LPGBT.RW.RESET.RSTFRAMEALIGNER"), 1, readback, system)

    # Finally, Set pll&dllConfigDone to run chip:
    #mpoke(0x0ef,0x06, readback, system)


def set_uplink_group_data_source(type, readback, system, pattern=0x55555555):
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
        print ("Setting invalid in set_uplink_group_data_source")
        sys.exit()

    writeReg(getNode("LPGBT.RW.TESTING.ULG0DATASOURCE"), setting, readback, system) #
    writeReg(getNode("LPGBT.RW.TESTING.ULG1DATASOURCE"), setting, readback, system) #
    writeReg(getNode("LPGBT.RW.TESTING.ULG2DATASOURCE"), setting, readback, system) #
    writeReg(getNode("LPGBT.RW.TESTING.ULG3DATASOURCE"), setting, readback, system) #
    writeReg(getNode("LPGBT.RW.TESTING.ULG4DATASOURCE"), setting, readback, system) #
    writeReg(getNode("LPGBT.RW.TESTING.ULG5DATASOURCE"), setting, readback, system) #
    writeReg(getNode("LPGBT.RW.TESTING.ULG6DATASOURCE"), setting, readback, system) #

    if (setting==4 or setting==5):
        writeReg(getNode("LPGBT.RW.TESTING.DPDATAPATTERN0"), 0xff & (pattern>>0), readback, system) #
        writeReg(getNode("LPGBT.RW.TESTING.DPDATAPATTERN1"), 0xff & (pattern>>8), readback, system) #
        writeReg(getNode("LPGBT.RW.TESTING.DPDATAPATTERN2"), 0xff & (pattern>>16), readback, system) #
        writeReg(getNode("LPGBT.RW.TESTING.DPDATAPATTERN3"), 0xff & (pattern>>24), readback, system) #


def configure_eptx(readback):
    #[0x0a7] EPTXDataRate
    writeReg(getNode("LPGBT.RWF.EPORTTX.EPTX0DATARATE"), 0x3, readback, system)
    writeReg(getNode("LPGBT.RWF.EPORTTX.EPTX1DATARATE"), 0x3, readback, system)
    writeReg(getNode("LPGBT.RWF.EPORTTX.EPTX2DATARATE"), 0x3, readback, system)
    writeReg(getNode("LPGBT.RWF.EPORTTX.EPTX3DATARATE"), 0x3, readback, system)

    #EPTXxxEnable
    writeReg(getNode("LPGBT.RWF.EPORTTX.EPTX12ENABLE"), 0x1, readback, system) #boss 6
    writeReg(getNode("LPGBT.RWF.EPORTTX.EPTX10ENABLE"), 0x1, readback, system) #boss 4
    writeReg(getNode("LPGBT.RWF.EPORTTX.EPTX20ENABLE"), 0x1, readback, system) #boss 8
    writeReg(getNode("LPGBT.RWF.EPORTTX.EPTX00ENABLE"), 0x1, readback, system) #boss 0
    writeReg(getNode("LPGBT.RWF.EPORTTX.EPTX23ENABLE"), 0x1, readback, system) #boss 11
    writeReg(getNode("LPGBT.RWF.EPORTTX.EPTX02ENABLE"), 0x1, readback, system) #boss 2

    #EPTXxxDriveStrength
    writeReg(getNode("LPGBT.RWF.EPORTTX.EPTX_CHN_CONTROL.EPTX6DRIVESTRENGTH"), 0x3, readback, system) #boss 6
    writeReg(getNode("LPGBT.RWF.EPORTTX.EPTX_CHN_CONTROL.EPTX4DRIVESTRENGTH"), 0x3, readback, system) #boss 4
    writeReg(getNode("LPGBT.RWF.EPORTTX.EPTX_CHN_CONTROL.EPTX8DRIVESTRENGTH"), 0x3, readback, system) #boss 8
    writeReg(getNode("LPGBT.RWF.EPORTTX.EPTX_CHN_CONTROL.EPTX0DRIVESTRENGTH"), 0x3, readback, system) #boss 0
    writeReg(getNode("LPGBT.RWF.EPORTTX.EPTX_CHN_CONTROL.EPTX11DRIVESTRENGTH"), 0x3, readback, system) #boss 11
    writeReg(getNode("LPGBT.RWF.EPORTTX.EPTX_CHN_CONTROL.EPTX2DRIVESTRENGTH"), 0x3, readback, system) #boss 2

    # enable mirror feature
    writeReg(getNode("LPGBT.RWF.EPORTTX.EPTX0MIRRORENABLE"), 0x1, readback, system)
    writeReg(getNode("LPGBT.RWF.EPORTTX.EPTX1MIRRORENABLE"), 0x1, readback, system)
    writeReg(getNode("LPGBT.RWF.EPORTTX.EPTX2MIRRORENABLE"), 0x1, readback, system)
    writeReg(getNode("LPGBT.RWF.EPORTTX.EPTX3MIRRORENABLE"), 0x1, readback, system)

    #turn on 320 MHz clocks
    writeReg(getNode("LPGBT.RWF.EPORTCLK.EPCLK3FREQ"),  0x4, readback, system)
    writeReg(getNode("LPGBT.RWF.EPORTCLK.EPCLK5FREQ"),  0x4, readback, system)
    writeReg(getNode("LPGBT.RWF.EPORTCLK.EPCLK6FREQ"),  0x4, readback, system)
    writeReg(getNode("LPGBT.RWF.EPORTCLK.EPCLK7FREQ"),  0x4, readback, system)
    writeReg(getNode("LPGBT.RWF.EPORTCLK.EPCLK15FREQ"), 0x4, readback, system)
    writeReg(getNode("LPGBT.RWF.EPORTCLK.EPCLK16FREQ"), 0x4, readback, system)

    writeReg(getNode("LPGBT.RWF.EPORTCLK.EPCLK3DRIVESTRENGTH"), 0x3, readback, system)
    writeReg(getNode("LPGBT.RWF.EPORTCLK.EPCLK5DRIVESTRENGTH"), 0x3, readback, system)
    writeReg(getNode("LPGBT.RWF.EPORTCLK.EPCLK6DRIVESTRENGTH"), 0x3, readback, system)
    writeReg(getNode("LPGBT.RWF.EPORTCLK.EPCLK7DRIVESTRENGTH"), 0x3, readback, system)
    writeReg(getNode("LPGBT.RWF.EPORTCLK.EPCLK15DRIVESTRENGTH"), 0x3, readback, system)
    writeReg(getNode("LPGBT.RWF.EPORTCLK.EPCLK16DRIVESTRENGTH"), 0x3, readback, system)


def invert_hsio(boss, readback, system):
    print ("Configuring pin inversion...")
    if (boss):
        writeReg(getNode("LPGBT.RWF.CHIPCONFIG.HIGHSPEEDDATAININVERT"), 0x1, readback, system)
    else:
        writeReg(getNode("LPGBT.RWF.CHIPCONFIG.HIGHSPEEDDATAOUTINVERT"), 0x1, readback, system)


def invert_eptx(boss, readback, system):
    if (boss):
        writeReg(getNode("LPGBT.RWF.EPORTTX.EPTX10INVERT"), 0x1, readback, system) #boss 4
        writeReg(getNode("LPGBT.RWF.EPORTTX.EPTX23INVERT"), 0x1, readback, system) #boss 11


def configure_ec_channel(boss, readback, system):
    print ("Configuring external control channels...")

    # enable EC output
    writeReg(getNode("LPGBT.RWF.EPORTTX.EPTXECENABLE"), 0x1, readback, system)

    # enable EC input
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRXECENABLE"), 0x1, readback, system)
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRXECTERM"),   0x1, readback, system)

    if (boss):
        # turn on 80 Mbps EC clock
        writeReg(getNode("LPGBT.RWF.EPORTCLK.EPCLK28FREQ"), 0x2, readback, system)
        writeReg(getNode("LPGBT.RWF.EPORTCLK.EPCLK28DRIVESTRENGTH"), 0x3, readback, system)


def configure_gpio(boss, readback, loopback, watchdog_disable, force_pusm_ready, override_cdr, system):
    print ("Configuring gpio...")
    if (boss):
        writeReg(getNode("LPGBT.RWF.PIO.PIODIRH"), 0x80 | 0x01, readback, system) # set as outputs
        writeReg(getNode("LPGBT.RWF.PIO.PIODIRL"), 0x01 | 0x02, readback, system) # set as outputs
        writeReg(getNode("LPGBT.RWF.PIO.PIOOUTH"), 0x80, readback, system) # enable LED
        writeReg(getNode("LPGBT.RWF.PIO.PIOOUTL"), 0x00, readback, system) #
    else:
        writeReg(getNode("LPGBT.RWF.PIO.PIODIRH"), 0x02 | 0x04 | 0x08, readback, system) # set as outputs
        writeReg(getNode("LPGBT.RWF.PIO.PIODIRL"), 0x00 | 0x00, readback, system) # set as outputs
        writeReg(getNode("LPGBT.RWF.PIO.PIOOUTH"), 0x00, readback, system) #
        writeReg(getNode("LPGBT.RWF.PIO.PIOOUTL"), 0x00, readback, system) #

    #       if (loopback):
    #           writeReg(getNode("LPGBT.RW.TESTING.LDDATASOURCE"), 0x1, readback, system)
    #       else:
    #           writeReg(getNode("LPGBT.RW.TESTING.LDDATASOURCE"), 0x0, readback, system)

    #       if (watchdog_disable):
    #           writeReg(getNode("LPGBT.RWF.POWERUP.PUSMPLLWDOGDISABLE"),0x1, readback, system)
    #           writeReg(getNode("LPGBT.RWF.POWERUP.PUSMDLLWDOGDISABLE"),0x1, readback, system)
    #       else:
    #           writeReg(getNode("LPGBT.RWF.POWERUP.PUSMPLLWDOGDISABLE"),0x0, readback, system)
    #           writeReg(getNode("LPGBT.RWF.POWERUP.PUSMDLLWDOGDISABLE"),0x0, readback, system)

    #       print ("Finishing configuration...")
    #       #2.2.11. Finishing configuration
    #       #[0x0ef] POWERUP2

    #       #writeReg(getNode("LPGBT.RWF.POWERUP.PUSMPLLTIMEOUTCONFIG"), 15, readback, system)
    #       #writeReg(getNode("LPGBT.RWF.POWERUP.PUSMDLLTIMEOUTCONFIG"), 15, readback, system)


    #       sleep(1)

    #       if (force_pusm_ready):
    #           writeReg(getNode("LPGBT.RW.POWERUP.PUSMFORCESTATE"), 0x1, readback, system)
    #           writeReg(getNode("LPGBT.RW.POWERUP.PUSMFORCEMAGIC"), 0xA3, readback, system)
    #           writeReg(getNode("LPGBT.RW.POWERUP.PUSMSTATEFORCED"), 18, readback, system)
    #           writeReg(getNode("LPGBT.RWF.POWERUP.PUSMPLLWDOGDISABLE"),0x1, readback, system)
    #           writeReg(getNode("LPGBT.RWF.POWERUP.PUSMDLLWDOGDISABLE"),0x1, readback, system)
    #       else:
    #           writeReg(getNode("LPGBT.RW.POWERUP.PUSMFORCESTATE"), 0x0, readback, system)
    #           writeReg(getNode("LPGBT.RW.POWERUP.PUSMFORCEMAGIC"), 0x0, readback, system)
    #           writeReg(getNode("LPGBT.RWF.POWERUP.PUSMPLLWDOGDISABLE"),0x0, readback, system)
    #           writeReg(getNode("LPGBT.RWF.POWERUP.PUSMDLLWDOGDISABLE"),0x0, readback, system)


    #if (override_cdr):
    #    writeReg(getNode("LPGBT.RWF.CALIBRATION.CDRCONTROLOVERRIDEENABLE") ,1, readback, system)
    #    writeReg(getNode("LPGBT.RWF.CALIBRATION.CDRCOCONNECTCDR") ,1, readback, system)
    #    writeReg(getNode("LPGBT.RWF.CALIBRATION.CDRCOREFCLKSEL") ,0, readback, system) # 0 = data/4, 1=external
    #    writeReg(getNode("LPGBT.RWF.CALIBRATION.CDRCOENABLEPLL"), 1, readback, system) # enable the enablePLL switch. 0 = disable, 1 = enable
    #    writeReg(getNode("LPGBT.RWF.CALIBRATION.CDRCOENABLEFD"), 1, readback, system)
    #    writeReg(getNode("LPGBT.RWF.CALIBRATION.CDRCOENABLECDR"), 1, readback, system)
    #    writeReg(getNode("LPGBT.RWF.CALIBRATION.CDRCODISDATACOUNTERREF"), 1, readback, system)
    #    writeReg(getNode("LPGBT.RWF.CALIBRATION.CDRCODISDESVBIASGEN"), 1, readback, system)
    #    writeReg(getNode("LPGBT.RWF.CALIBRATION.CDRCOCONNECTPLL"), 1, readback, system)


def configure_downlink(readback, system):
    print ("Configuring downlink...")
    #2.2.6. Downlink: Frame aligner settings (if high speed receiver is used)
    # downlink

    #[0x02f] FAMaxHeaderFoundCount
    writeReg(getNode("LPGBT.RWF.CALIBRATION.FAMAXHEADERFOUNDCOUNT"), 0x0, readback, system)
    #[0x030] FAMaxHeaderFoundCountAfterNF
    writeReg(getNode("LPGBT.RWF.CALIBRATION.FAMAXHEADERFOUNDCOUNTAFTERNF"), 0xA, readback, system)
    ##[0x031] FAMaxHeaderNotFoundCount
    writeReg(getNode("LPGBT.RWF.CALIBRATION.FAMAXHEADERNOTFOUNDCOUNT"), 0xA, readback, system)
    ##[0x032] FAFAMaxSkipCycleCountAfterNF
    writeReg(getNode("LPGBT.RWF.CALIBRATION.FAMAXSKIPCYCLECOUNTAFTERNF"), 0xA, readback, system)
    writeReg(getNode("LPGBT.RWF.CALIBRATION.EPRXUNLOCKTHRESHOLD"), 0x5, readback, system)


def configure_eprx(readback, system):
    print ("Configuring elink inputs...")
    # Enable Elink-inputs

    #set banks to 320 Mbps
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX0DATARATE"), 1, readback, system) # 1=320mbps in 10gbps mode
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX1DATARATE"), 1, readback, system) # 1=320mbps in 10gbps mode
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX2DATARATE"), 1, readback, system) # 1=320mbps in 10gbps mode
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX3DATARATE"), 1, readback, system) # 1=320mbps in 10gbps mode
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX4DATARATE"), 1, readback, system) # 1=320mbps in 10gbps mode
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX5DATARATE"), 1, readback, system) # 1=320mbps in 10gbps mode
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX6DATARATE"), 1, readback, system) # 1=320mbps in 10gbps mode

    #set banks to fixed phase
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX0TRACKMODE"), 0, readback, system) # 0 = fixed phase
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX1TRACKMODE"), 0, readback, system) # 0 = fixed phase
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX2TRACKMODE"), 0, readback, system) # 0 = fixed phase
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX3TRACKMODE"), 0, readback, system) # 0 = fixed phase
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX4TRACKMODE"), 0, readback, system) # 0 = fixed phase
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX5TRACKMODE"), 0, readback, system) # 0 = fixed phase
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX6TRACKMODE"), 0, readback, system) # 0 = fixed phase

    #enable inputs
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX00ENABLE"), 1, readback, system)
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX01ENABLE"), 1, readback, system)
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX02ENABLE"), 1, readback, system)
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX03ENABLE"), 1, readback, system)

    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX10ENABLE"), 1, readback, system)
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX11ENABLE"), 1, readback, system)
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX12ENABLE"), 1, readback, system)
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX13ENABLE"), 1, readback, system)

    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX20ENABLE"), 1, readback, system)
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX21ENABLE"), 1, readback, system)
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX22ENABLE"), 1, readback, system)
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX23ENABLE"), 1, readback, system)

    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX30ENABLE"), 1, readback, system)
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX31ENABLE"), 1, readback, system)
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX32ENABLE"), 1, readback, system)
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX33ENABLE"), 1, readback, system)

    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX40ENABLE"), 1, readback, system)
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX41ENABLE"), 1, readback, system)
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX42ENABLE"), 1, readback, system)
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX43ENABLE"), 1, readback, system)

    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX50ENABLE"), 1, readback, system)
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX51ENABLE"), 1, readback, system)
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX52ENABLE"), 1, readback, system)
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX53ENABLE"), 1, readback, system)

    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX60ENABLE"), 1, readback, system)
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX61ENABLE"), 1, readback, system)
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX62ENABLE"), 1, readback, system)
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX63ENABLE"), 1, readback, system)

    writeReg(getNode("LPGBT.RWF.CALIBRATION.PSDLLCONFIRMCOUNT"), 0x1, readback, system) # 4 40mhz clock cycles to confirm lock
    writeReg(getNode("LPGBT.RWF.CALIBRATION.PSDLLCURRENTSEL"), 0x1, readback, system)

    #enable 100 ohm termination
    for i in range (28):
        writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX_CHN_CONTROL.EPRX%dTERM" % i), 1, readback, system)


def reset_lpgbt(readback, system):
    writeReg(getNode("LPGBT.RW.RESET.RSTPLLDIGITAL"), 1, readback, system)
    writeReg(getNode("LPGBT.RW.RESET.RSTFUSES"),      1, readback, system)
    writeReg(getNode("LPGBT.RW.RESET.RSTCONFIG"),     1, readback, system)
    writeReg(getNode("LPGBT.RW.RESET.RSTRXLOGIC"),    1, readback, system)
    writeReg(getNode("LPGBT.RW.RESET.RSTTXLOGIC"),    1, readback, system)

    writeReg(getNode("LPGBT.RW.RESET.RSTPLLDIGITAL"), 0, readback, system)
    writeReg(getNode("LPGBT.RW.RESET.RSTFUSES"),      0, readback, system)
    writeReg(getNode("LPGBT.RW.RESET.RSTCONFIG"),     0, readback, system)
    writeReg(getNode("LPGBT.RW.RESET.RSTRXLOGIC"),    0, readback, system)
    writeReg(getNode("LPGBT.RW.RESET.RSTTXLOGIC"),    0, readback, system)


def check_rom_readback(sysem):
    romreg=readReg(getNode("LPGBT.RO.ROMREG"), system)
    if (romreg != 0xa5):
        print ("Error: no communication with LPGBT. ROMREG=0x%x, EXPECT=0x%x" % (romreg, 0xa5))
        sys.exit()
    else:
        print ("Successfully read from ROM. I2C communication OK")


def configure_eport_dlls(readback, system):
    print ("Configuring eport dlls...")
    #2.2.2. Uplink: ePort Inputs DLL's

    #[0x034] EPRXDllConfig
    writeReg(getNode("LPGBT.RWF.CALIBRATION.EPRXDLLCURRENT"), 0x1, readback, system)
    writeReg(getNode("LPGBT.RWF.CALIBRATION.EPRXDLLCONFIRMCOUNT"), 0x1, readback, system)
    writeReg(getNode("LPGBT.RWF.CALIBRATION.EPRXDLLFSMCLKALWAYSON"), 0x0, readback, system)
    writeReg(getNode("LPGBT.RWF.CALIBRATION.EPRXDLLCOARSELOCKDETECTION"), 0x0, readback, system)
    writeReg(getNode("LPGBT.RWF.CALIBRATION.EPRXENABLEREINIT"), 0x0, readback, system)
    writeReg(getNode("LPGBT.RWF.CALIBRATION.EPRXDATAGATINGENABLE"), 0x1, readback, system)


def configure_base_cernscript(readback, system):
    # Enable PowerGood @ 1.0 V, Delay 100 ms:
    mpoke(0x03e,0xdc, system)

    #Configure ClockGen Block:
    mpoke(0x01f,0x55, system)
    mpoke(0x020,0xc8, system)
    mpoke(0x021,0x24, system) #was 0x24
    mpoke(0x022,0x44, system)
    mpoke(0x023,0x55, system)
    mpoke(0x024,0x55, system)
    mpoke(0x025,0x55, system)
    mpoke(0x026,0x55, system)
    mpoke(0x027,0x55, system)
    mpoke(0x028,0x0f, system)
    mpoke(0x029,0x00, system) # was 0x00
    mpoke(0x02a,0x00, system) # was 0x00
    mpoke(0x02b,0x00, system)
    mpoke(0x02c,0x88, system)
    mpoke(0x02d,0x89, system)
    mpoke(0x02e,0x99, system)

    # Set H.S. Uplink Driver current:
    mpoke(0x039,0x20, system)

    # Select TO0 internal signal:
    mpoke(0x133,2, system) #40 mhz clock
    mpoke(0x132,0x10, system) # enabled fec counter for the downlink

    # Finally, Set pll&dllConfigDone to run chip:
    #mpoke(0x0ef,0x06, system)


def configure_base(boss, readback, override_lockcontrol, system):
    # Enable PowerGood @ 1.0 V, Delay 100 ms:
    mpoke(0x03e,0xdc, system)

    # Select TO0 internal signal:
    mpoke(0x133,2, system) #40 mhz clock
    mpoke(0x132,0x10, system) # enabled fec counter for the downlink

    # [0x01f] EPRXLOCKFILTER
    writeReg(getNode("LPGBT.RWF.CALIBRATION.EPRXLOCKTHRESHOLD"), 5, readback, system)
    writeReg(getNode("LPGBT.RWF.CALIBRATION.EPRXRELOCKTHRESHOLD"), 5, readback, system)

    # [0x020] CLKGConfig0
    writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGCALIBRATIONENDOFCOUNT"), 12, readback, system)
    writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGBIASGENCONFIG"), 8, readback, system)

    #[0x021] CLKGConfig1
    writeReg(getNode("LPGBT.RWF.CALIBRATION.CDRCONTROLOVERRIDEENABLE") ,0, readback, system)

    #default: 1 when in RX/TRX mode, 0 when in TX mode
    if (boss):
        writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGCDRRES") ,1, readback, system)
    else:
        writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGCDRRES") ,0, readback, system)

    writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGVCODAC") ,8, readback, system)
    writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGVCORAILMODE") ,0, readback, system) #0 = voltage mode, 1 = current mode
    # quick start suggests voltage mode but manual suggests current mode as default

    # [0x022] CLKGPllRes
    #"default: 4; set to 0 if RX or TRX mode"
    if (boss):
        writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGPLLRESWHENLOCKED"), 0, readback, system)
        writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGPLLRES"), 0x0, readback, system)
    else:
        writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGPLLRESWHENLOCKED"), 4, readback, system)
        writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGPLLRES"), 0x4, readback, system)

    #[0x023] CLKGPLLIntCur
    writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGPLLINTCURWHENLOCKED"), 0x5, readback, system)
    writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGPLLINTCUR"), 0x5, readback, system)
    #[0x024] CLKGPLLPropCur
    writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGPLLPROPCURWHENLOCKED"), 0x5, readback, system)
    writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGPLLPROPCUR"), 0x5, readback, system)
    #[0x025] CLKGCDRPropCur
    writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGCDRPROPCURWHENLOCKED"), 0x5, readback, system)
    writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGCDRPROPCUR"), 0x5, readback, system)
    #[0x026] CLKGCDRIntCur
    writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGCDRINTCURWHENLOCKED"), 0x5, readback, system)
    writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGCDRINTCUR"), 0x5, readback, system)
    #[0x027] CLKGCDRFFPropCur
    writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGCDRFEEDFORWARDPROPCURWHENLOCKED"), 0x5, readback, system)
    writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGCDRFEEDFORWARDPROPCUR"), 0x5, readback, system)
    #[0x028] CLKGFLLIntCur
    writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGFLLINTCURWHENLOCKED"), 0x0, readback, system)
    writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGFLLINTCUR"), 0x5, readback, system)
    #[0x029] CLKGFFCAP
    writeReg(getNode("LPGBT.RWF.CALIBRATION.CDRCOCONNECTCDR"), 0x0, readback, system)
    writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGCAPBANKOVERRIDEENABLE"), 0x0, readback, system)
    writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGFEEDFORWARDCAPWHENLOCKED"), 0x3, readback, system) # quickstart suggests 0 but manual suggests 3
    writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGFEEDFORWARDCAP"), 0x3, readback, system)           # quickstart suggests 0 but manual suggests 3
    #[0x02a] CLKGCntOverride
    writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGCOOVERRIDEVC"), 0x0, readback, system)
    writeReg(getNode("LPGBT.RWF.CALIBRATION.CDRCOREFCLKSEL"), 0x0, readback, system)
    writeReg(getNode("LPGBT.RWF.CALIBRATION.CDRCOENABLEPLL"), 0x0, readback, system)
    writeReg(getNode("LPGBT.RWF.CALIBRATION.CDRCOENABLEFD"), 0x0, readback, system)
    writeReg(getNode("LPGBT.RWF.CALIBRATION.CDRCOENABLECDR"), 0x0, readback, system)
    writeReg(getNode("LPGBT.RWF.CALIBRATION.CDRCODISDATACOUNTERREF"), 0x0, readback, system)
    writeReg(getNode("LPGBT.RWF.CALIBRATION.CDRCODISDESVBIASGEN"), 0x0, readback, system)
    writeReg(getNode("LPGBT.RWF.CALIBRATION.CDRCOCONNECTPLL"), 0x0, readback, system)
    #[0x02c] CLKGWaitTime
    #writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGWAITCDRTIME"), 0x8, readback, system)
    writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGWAITPLLTIME"), 0x8, readback, system)

    #[0x02d] CLKGLFConfig0
    if (boss):
        if (override_lockcontrol):
            writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGDISABLEFRAMEALIGNERLOCKCONTROL"), 0x1, readback, system)
            writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGLOCKFILTERENABLE"), 0x0, readback, system)
            writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGWAITCDRTIME"), 0xa, readbac, systemk)
            #writeReg(getNode("LPGBT.RW.BERT.SKIPDISABLE"),1, readback, system)
        else:
            writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGDISABLEFRAMEALIGNERLOCKCONTROL"), 0x0, readback, system)
            writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGLOCKFILTERENABLE"), 0x1, readback, system)
    else:
        # I am not sure what to do here
        writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGDISABLEFRAMEALIGNERLOCKCONTROL"), 0x0, readback, system)
        writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGLOCKFILTERENABLE"), 0x0, readback, system)

    writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGCAPBANKSELECT_8"), 0x0, readback, system)
    writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGCAPBANKSELECT_7TO0"), 0x0, readback, system) #[0x02b] CLKGOverrideCapBank

    writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGLOCKFILTERLOCKTHRCOUNTER"), 0x9, readback, system)

    #[0x02e] CLKGLFConfig1
    writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGLOCKFILTERRELOCKTHRCOUNTER"), 0x9, readback, system)
    writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGLOCKFILTERUNLOCKTHRCOUNTER"), 0x9, readback, system)

    writeReg(getNode("LPGBT.RWF.CALIBRATION.PSFSMCLKALWAYSON"), 0x0, readback, system) #quickstart recommends 0


def configure_phase_shifter(boss, readback, system):
    if (boss):
        # turn on phase shifter clock
        writeReg(getNode("LPGBT.RWF.PHASE_SHIFTER.PS1DELAY_8"), 0x0, readback, system)
        writeReg(getNode("LPGBT.RWF.PHASE_SHIFTER.PS1DELAY_7TO0"), 0x0, readback, system)
        writeReg(getNode("LPGBT.RWF.PHASE_SHIFTER.PS1ENABLEFINETUNE"), 0x0, readback, system)
        writeReg(getNode("LPGBT.RWF.PHASE_SHIFTER.PS1DRIVESTRENGTH"), 0x3, readback, system)
        writeReg(getNode("LPGBT.RWF.PHASE_SHIFTER.PS1FREQ"), 0x1, readback, system)
        writeReg(getNode("LPGBT.RWF.PHASE_SHIFTER.PS1PREEMPHASISMODE"), 0x0, readback, system)


if __name__ == '__main__':

    # Parsing arguments
    parser = argparse.ArgumentParser(description='LpGBT Configuration for ME0 Optohybrid')
    parser.add_argument("-s", "--system", action="store", dest="system", help="system = chc or backend or dongle")
    parser.add_argument("-l", "--lpgbt", action="store", dest="lpgbt", help="lpgbt = boss or sub")
    parser.add_argument("-c", "--config", action="store", dest="config", default="cern", help="config = cern (default) or basic")
    parser.add_argument("-e", "--configure_elinks", action="store", dest="configure_elinks", default=1, help="configure_elinks = 1 (default) or 0")
    parser.add_argument("-p", "--force_pusm_ready", action="store", dest="force_pusm_ready", default=0, help="force_pusm_ready = 1 or 0 (default)")
    parser.add_argument("-r", "--reset_before_config", action="store", dest="reset_before_config", default=0, help="reset_before_config = 1 or 0 (default)")
    parser.add_argument("-wd", "--watchdog_disable", action="store", dest="watchdog_disable", default=0, help="watchdog_disable = 1 or 0 (default)")
    parser.add_argument("-b", "--loopback", action="store", dest="loopback", default=1, help="loopback = 1 (default) or 0")
    parser.add_argument("-ol", "--override_lockcontrol", action="store", dest="override_lockcontrol", default=1, help="override_lockcontrol = 1 (default) or 0")
    parser.add_argument("-oc", "--override_cdr", action="store", dest="override_cdr", default=0, help="override_cdr = 1 or 0 (default)")
    args = parser.parse_args()

    if args.system == "chc":
        print ("Using Rpi CHeeseCake for configuration")
    elif args.system == "backend":
        #print ("Using Backend for configuration")
        print ("Only chc (Rpi Cheesecake) supported at the moment")
        sys.exit()
    elif args.system == "dongle":
        #print ("Using USB Dongle for configuration")
        print ("Only chc (Rpi Cheesecake) supported at the moment")
        sys.exit()
    else:
        print ("Only valid options: chc, backend, dongle")
        sys.exit()

    boss = None
    if args.lpgbt is None:
        print ("Please select boss or sub")
        sys.exit()
    elif (args.lpgbt=="boss"):
        print ("Configuring LPGBT as boss")
        boss=1
    elif (args.lpgbt=="sub"):
        print ("Configuring LPGBT as sub")
        boss=0
    else:
        print ("Please select boss or sub")
        sys.exit()
    if boss is None:
        sys.exit()

    cernconfig = 1
    if args.config=="cern":
        cernconfig = 1
    elif args.config=="basic":
        cernconfig = 0
    else:
        print ("Config option can only be cern or basic")
        sys.exit()

    if args.configure_elinks not in [0,1]:
        print ("Only 0 or 1 allowed for configure_elinks")
        sys.exit()
    if args.force_pusm_ready not in [0,1]:
        print ("Only 0 or 1 allowed for force_pusm_ready")
        sys.exit()
    if args.reset_before_config not in [0,1]:
        print ("Only 0 or 1 allowed for reset_before_config")
        sys.exit()
    if args.watchdog_disable not in [0,1]:
        print ("Only 0 or 1 allowed for watchdog_disable")
        sys.exit()
    if args.loopback not in [0,1]:
        print ("Only 0 or 1 allowed for loopback")
        sys.exit()
    if args.override_lockcontrol not in [0,1]:
        print ("Only 0 or 1 allowed for override_lockcontrol")
        sys.exit()
    if args.override_cdr not in [0,1]:
        print ("Only 0 or 1 allowed for override_cdr")
        sys.exit()

    # Configuring LPGBT
    readback = 0
    main(args.system, boss, cernconfig, args.configure_elinks, args.force_pusm_ready, args.reset_before_config, args.watchdog_disable, args.loopback, args.override_lockcontrol, args.override_cdr, readback)

    print ("==================================")
    print ("Checking register configuration...")
    print ("==================================")

    # Checking LPGBT configuration
    readback = 1
    main(args.system, boss, cernconfig, args.configure_elinks, args.force_pusm_ready, args.reset_before_config, args.watchdog_disable, args.loopback, args.override_lockcontrol, args.override_cdr, readback)

    # Check READY status
    pusmstate = readReg(getNode("LPGBT.RO.PUSM.PUSMSTATE"), args.system)
    if (pusmstate==18):
        print ("LPGBT status is READY")
