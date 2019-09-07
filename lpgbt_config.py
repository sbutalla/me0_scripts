from rw_reg_dongle import *
from time import sleep

master = 0
slave  = 0
configure_elinks=1
force_pusm_ready=0
reset_before_config=0
vcorail_current_mode=0
watchdog_disable=0
loopback = 1
override_lockcontrol=1
override_cdr=0

def main(readback=0):

    print "Parsing xml file..."
    parseXML()
    print "Parsing complete..."

    if len(sys.argv) < 2:
        print "Please select master or slave"
        return
    elif (sys.argv[1]=="master"):
        print "Configuring LPGBT as master"
        master=1
        slave=0
    elif (sys.argv[1]=="slave"):
        print "Configuring LPGBT as slave"
        master=0
        slave=1
    else:
        print "Please select master or slave"
        return

    romreg=readReg(getNode("LPGBT.RO.ROMREG"))
    if (romreg != 0xa5):
        print "Error: no communication with LPGBT. ROMREG=0x%x, EXPECT=0x%x" % (romreg, 0xa5)
        return

    if (reset_before_config):
        writeReg(getNode("LPGBT.RW.RESET.RSTPLLDIGITAL"), 1, readback)
        writeReg(getNode("LPGBT.RW.RESET.RSTFUSES"), 1, readback)
        writeReg(getNode("LPGBT.RW.RESET.RSTCONFIG"), 1, readback)
        writeReg(getNode("LPGBT.RW.RESET.RSTRXLOGIC"), 1, readback)
        writeReg(getNode("LPGBT.RW.RESET.RSTTXLOGIC"), 1, readback)

        writeReg(getNode("LPGBT.RW.RESET.RSTPLLDIGITAL"), 0, readback)
        writeReg(getNode("LPGBT.RW.RESET.RSTFUSES"), 0, readback)
        writeReg(getNode("LPGBT.RW.RESET.RSTCONFIG"), 0, readback)
        writeReg(getNode("LPGBT.RW.RESET.RSTRXLOGIC"), 0, readback)
        writeReg(getNode("LPGBT.RW.RESET.RSTTXLOGIC"), 0, readback)

    #   Enable PowerGood @ 1.0 V, Delay 100 ms:
    mpoke(0x03e,0xdc)

    #    Configure ClockGen Block:
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

    #    Set H.S. Uplink Driver current:
    mpoke(0x039,0x20)

    #   Enable PowerGood @ 1.0 V, Delay 100 ms:
    mpoke(0x03e,0xdc)

    # Select TO0 internal signal:
    mpoke(0x133,2) #40 mhz clock
    mpoke(0x132,0x10) # enabled fec counter for the downlink

    # select test pattern for eTx group 3: (initial value from Ted : 0x40 (PRBS), 0xc0 = constant, 0x80 = binary)
    #mpoke(0x11d,0x40)

    # Finally, Set pll&dllConfigDone to run chip:
    mpoke(0x0ef,0x06)

    #       # [0x01f] EPRXLOCKFILTER
    #       writeReg(getNode("LPGBT.RWF.CALIBRATION.EPRXLOCKTHRESHOLD"), 5, readback)
    #       writeReg(getNode("LPGBT.RWF.CALIBRATION.EPRXRELOCKTHRESHOLD"), 5, readback)

    #       # [0x020] CLKGConfig0
    #       writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGCALIBRATIONENDOFCOUNT"), 12, readback)
    #       writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGBIASGENCONFIG"), 8, readback)

    #       #[0x021] CLKGConfig1
    #       writeReg(getNode("LPGBT.RWF.CALIBRATION.CDRCONTROLOVERRIDEENABLE") ,0, readback)

    #       #default: 1 when in RX/TRX mode, 0 when in TX mode
    #       if (master):
    #           writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGCDRRES") ,1, readback)
    #       else:
    #           writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGCDRRES") ,0, readback)

    #       writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGVCODAC") ,8, readback)
    #       writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGVCORAILMODE") ,vcorail_current_mode, readback) #0 = voltage mode, 1 = current mode
    #       # quick start suggests voltage mode but manual suggests current mode as default

    #       # [0x022] CLKGPllRes
    #       #"default: 4; set to 0 if RX or TRX mode"
    #       if (master):
    #           writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGPLLRESWHENLOCKED"), 0, readback)
    #           writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGPLLRES"), 0x0, readback)
    #       else:
    #           writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGPLLRESWHENLOCKED"), 4, readback)
    #           writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGPLLRES"), 0x4, readback)

    #       #[0x023] CLKGPLLIntCur
    #       writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGPLLINTCURWHENLOCKED"), 0x5, readback)
    #       writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGPLLINTCUR"), 0x5, readback)
    #       #[0x024] CLKGPLLPropCur
    #       writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGPLLPROPCURWHENLOCKED"), 0x5, readback)
    #       writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGPLLPROPCUR"), 0x5, readback)
    #       #[0x025] CLKGCDRPropCur
    #       writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGCDRPROPCURWHENLOCKED"), 0x5, readback)
    #       writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGCDRPROPCUR"), 0x5, readback)
    #       #[0x026] CLKGCDRIntCur
    #       writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGCDRINTCURWHENLOCKED"), 0x5, readback)
    #       writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGCDRINTCUR"), 0x5, readback)
    #       #[0x027] CLKGCDRFFPropCur
    #       writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGCDRFEEDFORWARDPROPCURWHENLOCKED"), 0x5, readback)
    #       writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGCDRFEEDFORWARDPROPCUR"), 0x5, readback)
    #       #[0x028] CLKGFLLIntCur
    #       writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGFLLINTCURWHENLOCKED"), 0x0, readback)
    #       writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGFLLINTCUR"), 0x5, readback)
    #       #[0x029] CLKGFFCAP
    #       writeReg(getNode("LPGBT.RWF.CALIBRATION.CDRCOCONNECTCDR"), 0x0, readback)
    #       writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGCAPBANKOVERRIDEENABLE"), 0x0, readback)
    #       writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGFEEDFORWARDCAPWHENLOCKED"), 0x3, readback) # quickstart suggests 0 but manual suggests 3
    #       writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGFEEDFORWARDCAP"), 0x3, readback)           # quickstart suggests 0 but manual suggests 3
    #       #[0x02a] CLKGCntOverride
    #       writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGCOOVERRIDEVC"), 0x0, readback)
    #       writeReg(getNode("LPGBT.RWF.CALIBRATION.CDRCOREFCLKSEL"), 0x0, readback)
    #       writeReg(getNode("LPGBT.RWF.CALIBRATION.CDRCOENABLEPLL"), 0x0, readback)
    #       writeReg(getNode("LPGBT.RWF.CALIBRATION.CDRCOENABLEFD"), 0x0, readback)
    #       writeReg(getNode("LPGBT.RWF.CALIBRATION.CDRCOENABLECDR"), 0x0, readback)
    #       writeReg(getNode("LPGBT.RWF.CALIBRATION.CDRCODISDATACOUNTERREF"), 0x0, readback)
    #       writeReg(getNode("LPGBT.RWF.CALIBRATION.CDRCODISDESVBIASGEN"), 0x0, readback)
    #       writeReg(getNode("LPGBT.RWF.CALIBRATION.CDRCOCONNECTPLL"), 0x0, readback)
    #       #[0x02c] CLKGWaitTime
    #       #writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGWAITCDRTIME"), 0x8, readback)
    #       writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGWAITPLLTIME"), 0x8, readback)

    #       #[0x02d] CLKGLFConfig0
    #       if (master):

    #           if (override_lockcontrol):
    #               writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGDISABLEFRAMEALIGNERLOCKCONTROL"), 0x1, readback)
    #               writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGLOCKFILTERENABLE"), 0x0, readback)
    #               writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGWAITCDRTIME"), 0xa, readback)
    #               #writeReg(getNode("LPGBT.RW.BERT.SKIPDISABLE"),1, readback)
    #           else:
    #               writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGDISABLEFRAMEALIGNERLOCKCONTROL"), 0x0, readback)
    #               writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGLOCKFILTERENABLE"), 0x1, readback)

    #       else:
    #           # I am not sure what to do here
    #           writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGDISABLEFRAMEALIGNERLOCKCONTROL"), 0x0, readback)
    #           writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGLOCKFILTERENABLE"), 0x0, readback)

    #       writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGCAPBANKSELECT_8"), 0x0, readback)
    #       writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGCAPBANKSELECT_7TO0"), 0x0, readback) #[0x02b] CLKGOverrideCapBank

    #       writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGLOCKFILTERLOCKTHRCOUNTER"), 0x9, readback)

    #       #[0x02e] CLKGLFConfig1
    #       writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGLOCKFILTERRELOCKTHRCOUNTER"), 0x9, readback)
    #       writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGLOCKFILTERUNLOCKTHRCOUNTER"), 0x9, readback)

    #       writeReg(getNode("LPGBT.RWF.CALIBRATION.PSFSMCLKALWAYSON"), 0x0, readback) #quickstart recommends 0

    print "Configuring uplink..."

    #2.2.2. Uplink: ePort Inputs DLL's
    #[0x034] EPRXDllConfig
    writeReg(getNode("LPGBT.RWF.CALIBRATION.EPRXDLLCURRENT"), 0x1, readback)
    writeReg(getNode("LPGBT.RWF.CALIBRATION.EPRXDLLCONFIRMCOUNT"), 0x1, readback)
    writeReg(getNode("LPGBT.RWF.CALIBRATION.EPRXDLLFSMCLKALWAYSON"), 0x0, readback)
    writeReg(getNode("LPGBT.RWF.CALIBRATION.EPRXDLLCOARSELOCKDETECTION"), 0x0, readback)
    writeReg(getNode("LPGBT.RWF.CALIBRATION.EPRXENABLEREINIT"), 0x0, readback)
    writeReg(getNode("LPGBT.RWF.CALIBRATION.EPRXDATAGATINGENABLE"), 0x1, readback)

    if (override_cdr):
        writeReg(getNode("LPGBT.RWF.CALIBRATION.CDRCONTROLOVERRIDEENABLE") ,1, readback)
        writeReg(getNode("LPGBT.RWF.CALIBRATION.CDRCOCONNECTCDR") ,1, readback)
        writeReg(getNode("LPGBT.RWF.CALIBRATION.CDRCOREFCLKSEL") ,0, readback) # 0 = data/4, 1=external
        writeReg(getNode("LPGBT.RWF.CALIBRATION.CDRCOENABLEPLL"), 1, readback) # enable the enablePLL switch. 0 = disable, 1 = enable
        writeReg(getNode("LPGBT.RWF.CALIBRATION.CDRCOENABLEFD"), 1, readback)
        writeReg(getNode("LPGBT.RWF.CALIBRATION.CDRCOENABLECDR"), 1, readback)
        writeReg(getNode("LPGBT.RWF.CALIBRATION.CDRCODISDATACOUNTERREF"), 1, readback)
        writeReg(getNode("LPGBT.RWF.CALIBRATION.CDRCODISDESVBIASGEN"), 1, readback)
        writeReg(getNode("LPGBT.RWF.CALIBRATION.CDRCOCONNECTPLL"), 1, readback)

    #2.2.3. Uplink: Line driver settings (if high speed transmitter is used)
    #[0x039] LDConfigH
    writeReg(getNode("LPGBT.RWF.LINE_DRIVER.LDMODULATIONCURRENT"), 32, readback)

    if (configure_elinks):
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


    if (master):
        print "Configuring downlink..."

        #2.2.6. Downlink: Frame aligner settings (if high speed receiver is used)

        # downlink

        #[0x02f] FAMaxHeaderFoundCount
        writeReg(getNode("LPGBT.RWF.CALIBRATION.FAMAXHEADERFOUNDCOUNT"), 0x0, readback)
        #[0x030] FAMaxHeaderFoundCountAfterNF
        writeReg(getNode("LPGBT.RWF.CALIBRATION.FAMAXHEADERFOUNDCOUNTAFTERNF"), 0xA, readback)
        ##[0x031] FAMaxHeaderNotFoundCount
        writeReg(getNode("LPGBT.RWF.CALIBRATION.FAMAXHEADERNOTFOUNDCOUNT"), 0xA, readback)
        ##[0x032] FAFAMaxSkipCycleCountAfterNF
        writeReg(getNode("LPGBT.RWF.CALIBRATION.FAMAXSKIPCYCLECOUNTAFTERNF"), 0xA, readback)
        writeReg(getNode("LPGBT.RWF.CALIBRATION.EPRXUNLOCKTHRESHOLD"), 0x5, readback)


    if (master and configure_elinks):

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

        #turn on 40MHz clocks

        writeReg(getNode("LPGBT.RWF.EPORTCLK.EPCLK3FREQ"), 0x1, readback)
        writeReg(getNode("LPGBT.RWF.EPORTCLK.EPCLK5FREQ"), 0x1, readback)
        writeReg(getNode("LPGBT.RWF.EPORTCLK.EPCLK6FREQ"), 0x1, readback)
        writeReg(getNode("LPGBT.RWF.EPORTCLK.EPCLK7FREQ"), 0x1, readback)
        writeReg(getNode("LPGBT.RWF.EPORTCLK.EPCLK15FREQ"), 0x1, readback)
        writeReg(getNode("LPGBT.RWF.EPORTCLK.EPCLK16FREQ"), 0x1, readback)

        writeReg(getNode("LPGBT.RWF.EPORTCLK.EPCLK3DRIVESTRENGTH"), 0x3, readback)
        writeReg(getNode("LPGBT.RWF.EPORTCLK.EPCLK5DRIVESTRENGTH"), 0x3, readback)
        writeReg(getNode("LPGBT.RWF.EPORTCLK.EPCLK6DRIVESTRENGTH"), 0x3, readback)
        writeReg(getNode("LPGBT.RWF.EPORTCLK.EPCLK7DRIVESTRENGTH"), 0x3, readback)
        writeReg(getNode("LPGBT.RWF.EPORTCLK.EPCLK15DRIVESTRENGTH"), 0x3, readback)
        writeReg(getNode("LPGBT.RWF.EPORTCLK.EPCLK16DRIVESTRENGTH"), 0x3, readback)

    if (master):

        # turn on 80 Mbps EC clock
        writeReg(getNode("LPGBT.RWF.EPORTCLK.EPCLK28FREQ"), 0x2, readback)
        writeReg(getNode("LPGBT.RWF.EPORTCLK.EPCLK28DRIVESTRENGTH"), 0x3, readback)

        # turn on phase shifter clock
        writeReg(getNode("LPGBT.RWF.PHASE_SHIFTER.PS1DELAY_8"), 0x0, readback)
        writeReg(getNode("LPGBT.RWF.PHASE_SHIFTER.PS1DELAY_7TO0"), 0x0, readback)
        writeReg(getNode("LPGBT.RWF.PHASE_SHIFTER.PS1ENABLEFINETUNE"), 0x0, readback)
        writeReg(getNode("LPGBT.RWF.PHASE_SHIFTER.PS1DRIVESTRENGTH"), 0x3, readback)
        writeReg(getNode("LPGBT.RWF.PHASE_SHIFTER.PS1FREQ"), 0x1, readback)
        writeReg(getNode("LPGBT.RWF.PHASE_SHIFTER.PS1PREEMPHASISMODE"), 0x0, readback)

    print ("Configuring external control channels...")

    # enable EC output
    writeReg(getNode("LPGBT.RWF.EPORTTX.EPTXECENABLE"), 0x1, readback)
    # enable EC input
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRXECENABLE"), 0x1, readback)
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRXECTERM"), 0x1, readback)

    print ("Configuring hsio inversion...")
    if (master):
        writeReg(getNode("LPGBT.RWF.CHIPCONFIG.HIGHSPEEDDATAININVERT"), 0x1, readback)
    if (slave):
        writeReg(getNode("LPGBT.RWF.CHIPCONFIG.HIGHSPEEDDATAOUTINVERT"), 0x1, readback)

    print ("Configuring gpio...")
    if (master):
        writeReg(getNode("LPGBT.RWF.PIO.PIODIRH"), 0x80 | 0x01, readback) # set as outputs
        writeReg(getNode("LPGBT.RWF.PIO.PIODIRL"), 0x01 | 0x02, readback) # set as outputs
        writeReg(getNode("LPGBT.RWF.PIO.PIOOUTH"), 0x80, readback) # enable LED
        writeReg(getNode("LPGBT.RWF.PIO.PIOOUTL"), 0x00, readback) #
    if (slave):
        writeReg(getNode("LPGBT.RWF.PIO.PIODIRH"), 0x02 | 0x04 | 0x08, readback) # set as outputs
        writeReg(getNode("LPGBT.RWF.PIO.PIODIRL"), 0x00 | 0x00, readback) # set as outputs
        writeReg(getNode("LPGBT.RWF.PIO.PIOOUTH"), 0x00, readback) #
        writeReg(getNode("LPGBT.RWF.PIO.PIOOUTL"), 0x00, readback) #

    mpoke(0x122,0x00) # prbs enable
    mpoke(0x123,0x00) # prbs enable
    mpoke(0x124,0x00) # prbs enable
    mpoke(0x125,0x00) # prbs enable

    writeReg(getNode("LPGBT.RW.TESTING.ULG6DATASOURCE"), 0x02, readback) #
    writeReg(getNode("LPGBT.RW.TESTING.ULG5DATASOURCE"), 0x02, readback) #
    writeReg(getNode("LPGBT.RW.TESTING.ULG4DATASOURCE"), 0x02, readback) #
    writeReg(getNode("LPGBT.RW.TESTING.ULG3DATASOURCE"), 0x02, readback) #
    writeReg(getNode("LPGBT.RW.TESTING.ULG2DATASOURCE"), 0x02, readback) #
    writeReg(getNode("LPGBT.RW.TESTING.ULG1DATASOURCE"), 0x02, readback) #
    writeReg(getNode("LPGBT.RW.TESTING.ULG0DATASOURCE"), 0x02, readback) #

    #       if (loopback):
    #           writeReg(getNode("LPGBT.RW.TESTING.LDDATASOURCE"), 0x1, readback)
    #       else:
    #           writeReg(getNode("LPGBT.RW.TESTING.LDDATASOURCE"), 0x0, readback)

    #       if (watchdog_disable):
    #           writeReg(getNode("LPGBT.RWF.POWERUP.PUSMPLLWDOGDISABLE"),0x1, readback)
    #           writeReg(getNode("LPGBT.RWF.POWERUP.PUSMDLLWDOGDISABLE"),0x1, readback)
    #       else:
    #           writeReg(getNode("LPGBT.RWF.POWERUP.PUSMPLLWDOGDISABLE"),0x0, readback)
    #           writeReg(getNode("LPGBT.RWF.POWERUP.PUSMDLLWDOGDISABLE"),0x0, readback)

    #       print ("Finishing configuration...")
    #       #2.2.11. Finishing configuration
    #       #[0x0ef] POWERUP2

    #       #writeReg(getNode("LPGBT.RWF.POWERUP.PUSMPLLTIMEOUTCONFIG"), 15, readback)
    #       #writeReg(getNode("LPGBT.RWF.POWERUP.PUSMDLLTIMEOUTCONFIG"), 15, readback)


    #       sleep(1)

    #       writeReg(getNode("LPGBT.RWF.POWERUP.DLLCONFIGDONE"), 0x1, readback)
    #       writeReg(getNode("LPGBT.RWF.POWERUP.PLLCONFIGDONE"), 0x1, readback)

    #       if (force_pusm_ready):
    #           writeReg(getNode("LPGBT.RW.POWERUP.PUSMFORCESTATE"), 0x1, readback)
    #           writeReg(getNode("LPGBT.RW.POWERUP.PUSMFORCEMAGIC"), 0xA3, readback)
    #           writeReg(getNode("LPGBT.RW.POWERUP.PUSMSTATEFORCED"), 18, readback)
    #           writeReg(getNode("LPGBT.RWF.POWERUP.PUSMPLLWDOGDISABLE"),0x1, readback)
    #           writeReg(getNode("LPGBT.RWF.POWERUP.PUSMDLLWDOGDISABLE"),0x1, readback)
    #       else:
    #           writeReg(getNode("LPGBT.RW.POWERUP.PUSMFORCESTATE"), 0x0, readback)
    #           writeReg(getNode("LPGBT.RW.POWERUP.PUSMFORCEMAGIC"), 0x0, readback)
    #           writeReg(getNode("LPGBT.RWF.POWERUP.PUSMPLLWDOGDISABLE"),0x0, readback)
    #           writeReg(getNode("LPGBT.RWF.POWERUP.PUSMDLLWDOGDISABLE"),0x0, readback)


if __name__ == '__main__':
   main(0)
   main(1)
