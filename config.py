from rw_reg_dongle import *

master = 0
slave  = 0
configure_elinks=1
force_pusm_ready=0
reset_before_config=0
override_lockcontrol=0
override_cdr=0
vcorail_current_mode=0

def main():

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
        writeReg(getNode("LPGBT.RW.RESET.RSTPLLDIGITAL"), 1)
        writeReg(getNode("LPGBT.RW.RESET.RSTFUSES"), 1)
        writeReg(getNode("LPGBT.RW.RESET.RSTCONFIG"), 1)
        writeReg(getNode("LPGBT.RW.RESET.RSTRXLOGIC"), 1)
        writeReg(getNode("LPGBT.RW.RESET.RSTTXLOGIC"), 1)

        writeReg(getNode("LPGBT.RW.RESET.RSTPLLDIGITAL"), 0)
        writeReg(getNode("LPGBT.RW.RESET.RSTFUSES"), 0)
        writeReg(getNode("LPGBT.RW.RESET.RSTCONFIG"), 0)
        writeReg(getNode("LPGBT.RW.RESET.RSTRXLOGIC"), 0)
        writeReg(getNode("LPGBT.RW.RESET.RSTTXLOGIC"), 0)

    # [0x01f] EPRXLOCKFILTER
    writeReg(getNode("LPGBT.RWF.CALIBRATION.EPRXLOCKTHRESHOLD"), 5)
    writeReg(getNode("LPGBT.RWF.CALIBRATION.EPRXRELOCKTHRESHOLD"), 5)

    # [0x020] CLKGConfig0
    writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGCALIBRATIONENDOFCOUNT"), 12)
    writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGBIASGENCONFIG"), 8)

    #[0x021] CLKGConfig1
    writeReg(getNode("LPGBT.RWF.CALIBRATION.CDRCONTROLOVERRIDEENABLE") ,0)
    writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGDISABLEFRAMEALIGNERLOCKCONTROL") ,0)

    #default: 1 when in RX/TRX mode, 0 when in TX mode
    if (master):
        writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGCDRRES") ,1)
    else:
        writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGCDRRES") ,0)

    writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGVCODAC") ,8)
    writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGVCORAILMODE") ,vcorail_current_mode) #0 = voltage mode, 1 = current mode
    # quick start suggests voltage mode but manual suggests current mode as default

    # [0x022] CLKGPllRes
    #"default: 4; set to 0 if RX or TRX mode"
    if (master):
        writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGPLLRESWHENLOCKED"), 0)
        writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGPLLRES"), 0x0)
    else:
        writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGPLLRESWHENLOCKED"), 4)
        writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGPLLRES"), 0x4)

    #[0x023] CLKGPLLIntCur
    writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGPLLINTCURWHENLOCKED"), 0x5)
    writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGPLLINTCUR"), 0x5)
    #[0x024] CLKGPLLPropCur
    writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGPLLPROPCURWHENLOCKED"), 0x5)
    writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGPLLPROPCUR"), 0x5)
    #[0x025] CLKGCDRPropCur
    writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGCDRPROPCURWHENLOCKED"), 0x5)
    writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGCDRPROPCUR"), 0x5)
    #[0x026] CLKGCDRIntCur
    writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGCDRINTCURWHENLOCKED"), 0x5)
    writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGCDRINTCUR"), 0x5)
    #[0x027] CLKGCDRFFPropCur
    writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGCDRFEEDFORWARDPROPCURWHENLOCKED"), 0x5)
    writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGCDRFEEDFORWARDPROPCUR"), 0x5)
    #[0x028] CLKGFLLIntCur
    writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGFLLINTCURWHENLOCKED"), 0x0)
    writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGFLLINTCUR"), 0x5)
    #[0x029] CLKGFFCAP
    writeReg(getNode("LPGBT.RWF.CALIBRATION.CDRCOCONNECTCDR"), 0x0)
    writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGCAPBANKOVERRIDEENABLE"), 0x0)
    writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGFEEDFORWARDCAPWHENLOCKED"), 0x3) # quickstart suggests 0 but manual suggests 3
    writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGFEEDFORWARDCAP"), 0x3)           # quickstart suggests 0 but manual suggests 3
    #[0x02a] CLKGCntOverride
    writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGCOOVERRIDEVC"), 0x0)
    writeReg(getNode("LPGBT.RWF.CALIBRATION.CDRCOREFCLKSEL"), 0x0)
    writeReg(getNode("LPGBT.RWF.CALIBRATION.CDRCOENABLEPLL"), 0x0)
    writeReg(getNode("LPGBT.RWF.CALIBRATION.CDRCOENABLEFD"), 0x0)
    writeReg(getNode("LPGBT.RWF.CALIBRATION.CDRCOENABLECDR"), 0x0)
    writeReg(getNode("LPGBT.RWF.CALIBRATION.CDRCODISDATACOUNTERREF"), 0x0)
    writeReg(getNode("LPGBT.RWF.CALIBRATION.CDRCODISDESVBIASGEN"), 0x0)
    writeReg(getNode("LPGBT.RWF.CALIBRATION.CDRCOCONNECTPLL"), 0x0)
    #[0x02c] CLKGWaitTime
    writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGWAITCDRTIME"), 0x8)
    writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGWAITPLLTIME"), 0x8)


    #[0x02d] CLKGLFConfig0
    if (master):

        writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGLOCKFILTERENABLE"), 0x0) # quickstart recommends 0
        if (override_lockcontrol):
            writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGDISABLEFRAMEALIGNERLOCKCONTROL"), 0x1)
        else:
            writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGDISABLEFRAMEALIGNERLOCKCONTROL"), 0x0)

    else:
        writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGDISABLEFRAMEALIGNERLOCKCONTROL"), 0x0)
        if (override_lockcontrol):
            writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGLOCKFILTERENABLE"), 0x0)
        else:
            writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGLOCKFILTERENABLE"), 0x1) # quickstart recommends 0

    #writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGCAPBANKSELECT_8"), 0x0)
    #writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGCAPBANKSELECT_7TO0"), 0x0) #[0x02b] CLKGOverrideCapBank

    writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGLOCKFILTERLOCKTHRCOUNTER"), 0x9)

    #[0x02e] CLKGLFConfig1
    writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGLOCKFILTERRELOCKTHRCOUNTER"), 0x9)
    writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGLOCKFILTERUNLOCKTHRCOUNTER"), 0x9)

    writeReg(getNode("LPGBT.RWF.CALIBRATION.PSFSMCLKALWAYSON"), 0x0) #quickstart recommends 0

    print "Configuring uplink..."

    #2.2.2. Uplink: ePort Inputs DLL's
    #[0x034] EPRXDllConfig
    writeReg(getNode("LPGBT.RWF.CALIBRATION.EPRXDLLCURRENT"), 0x1)
    writeReg(getNode("LPGBT.RWF.CALIBRATION.EPRXDLLCONFIRMCOUNT"), 0x1)
    writeReg(getNode("LPGBT.RWF.CALIBRATION.EPRXDLLFSMCLKALWAYSON"), 0x0)
    writeReg(getNode("LPGBT.RWF.CALIBRATION.EPRXDLLCOARSELOCKDETECTION"), 0x0)
    writeReg(getNode("LPGBT.RWF.CALIBRATION.EPRXENABLEREINIT"), 0x0)
    writeReg(getNode("LPGBT.RWF.CALIBRATION.EPRXDATAGATINGENABLE"), 0x1)

    #if (override_cdr):
    #    writeReg(getNode("LPGBT.RWF.CALIBRATION.CDRCONTROLOVERRIDEENABLE") ,1)
    #    writeReg(getNode("LPGBT.RWF.CALIBRATION.CDRCOCONNECTCDR") ,1)
    #    writeReg(getNode("LPGBT.RWF.CALIBRATION.CDRCOREFCLKSEL") ,0) # 0 = data/4, 1=external
    #    writeReg(getNode("LPGBT.RWF.CALIBRATION.CDRCOENABLEPLL"), 1) # enable the enablePLL switch. 0 = disable, 1 = enable
    #    writeReg(getNode("LPGBT.RWF.CALIBRATION.CDRCOENABLEFD"), 1)
    #    writeReg(getNode("LPGBT.RWF.CALIBRATION.CDRCOENABLECDR"), 1)
    #    writeReg(getNode("LPGBT.RWF.CALIBRATION.CDRCODISDATACOUNTERREF"), 1)
    #    writeReg(getNode("LPGBT.RWF.CALIBRATION.CDRCODISDESVBIASGEN"), 1)
    #    writeReg(getNode("LPGBT.RWF.CALIBRATION.CDRCOCONNECTPLL"), 1)

    #2.2.3. Uplink: Line driver settings (if high speed transmitter is used)
    #[0x039] LDConfigH
    writeReg(getNode("LPGBT.RWF.LINE_DRIVER.LDMODULATIONCURRENT"), 32)

    if (configure_elinks):
        print "Configuring elink inputs..."

        # Enable Elink-inputs

        #set banks to 320 Mbps
        writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX0DATARATE"), 1)
        writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX1DATARATE"), 1)
        writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX2DATARATE"), 1)
        writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX3DATARATE"), 1)
        writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX4DATARATE"), 1)
        writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX5DATARATE"), 1)
        writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX6DATARATE"), 1)

        #set banks to fixed phase
        writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX0TRACKMODE"), 0)
        writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX1TRACKMODE"), 0)
        writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX2TRACKMODE"), 0)
        writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX3TRACKMODE"), 0)
        writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX4TRACKMODE"), 0)
        writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX5TRACKMODE"), 0)
        writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX6TRACKMODE"), 0)

        #enable inputs
        writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX00ENABLE"), 1)
        writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX01ENABLE"), 1)
        writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX02ENABLE"), 1)
        writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX03ENABLE"), 1)

        writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX10ENABLE"), 1)
        writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX11ENABLE"), 1)
        writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX12ENABLE"), 1)
        writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX13ENABLE"), 1)

        writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX20ENABLE"), 1)
        writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX21ENABLE"), 1)
        writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX22ENABLE"), 1)
        writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX23ENABLE"), 1)

        writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX30ENABLE"), 1)
        writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX31ENABLE"), 1)
        writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX32ENABLE"), 1)
        writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX33ENABLE"), 1)

        writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX40ENABLE"), 1)
        writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX41ENABLE"), 1)
        writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX42ENABLE"), 1)
        writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX43ENABLE"), 1)

        writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX50ENABLE"), 1)
        writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX51ENABLE"), 1)
        writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX52ENABLE"), 1)
        writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX53ENABLE"), 1)

        writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX60ENABLE"), 1)
        writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX61ENABLE"), 1)
        writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX62ENABLE"), 1)
        writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX63ENABLE"), 1)

        writeReg(getNode("LPGBT.RWF.CALIBRATION.PSDLLCONFIRMCOUNT"), 0x1) # 4 40mhz clock cycles to confirm lock
        writeReg(getNode("LPGBT.RWF.CALIBRATION.PSDLLCURRENTSEL"), 0x1)

        #enable 100 ohm termination
        for i in range (28):
            writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX_CHN_CONTROL.EPRX%dTERM" % i), 1)


    if (master):
        print "Configuring downlink..."

        #2.2.6. Downlink: Frame aligner settings (if high speed receiver is used)

        # downlink

        #[0x02f] FAMaxHeaderFoundCount
        writeReg(getNode("LPGBT.RWF.CALIBRATION.FAMAXHEADERFOUNDCOUNT"), 0xA)
        #[0x030] FAMaxHeaderFoundCountAfterNF
        writeReg(getNode("LPGBT.RWF.CALIBRATION.FAMAXHEADERFOUNDCOUNTAFTERNF"), 0xA)
        #[0x031] FAMaxHeaderNotFoundCount
        writeReg(getNode("LPGBT.RWF.CALIBRATION.FAMAXHEADERNOTFOUNDCOUNT"), 0xA)
        #[0x032] FAFAMaxSkipCycleCountAfterNF
        writeReg(getNode("LPGBT.RWF.CALIBRATION.FAMAXSKIPCYCLECOUNTAFTERNF"), 0xA)

        writeReg(getNode("LPGBT.RWF.CALIBRATION.EPRXUNLOCKTHRESHOLD"), 0x5)



    if (master and configure_elinks):

        #[0x0a7] EPTXDataRate
        writeReg(getNode("LPGBT.RWF.EPORTTX.EPTX0DATARATE"), 0x3)
        writeReg(getNode("LPGBT.RWF.EPORTTX.EPTX1DATARATE"), 0x3)
        writeReg(getNode("LPGBT.RWF.EPORTTX.EPTX2DATARATE"), 0x3)
        writeReg(getNode("LPGBT.RWF.EPORTTX.EPTX3DATARATE"), 0x3)

        #EPTXxxEnable
        writeReg(getNode("LPGBT.RWF.EPORTTX.EPTX12ENABLE"), 0x1) #master 6
        writeReg(getNode("LPGBT.RWF.EPORTTX.EPTX10ENABLE"), 0x1) #master 4
        writeReg(getNode("LPGBT.RWF.EPORTTX.EPTX20ENABLE"), 0x1) #master 8
        writeReg(getNode("LPGBT.RWF.EPORTTX.EPTX00ENABLE"), 0x1) #master 0
        writeReg(getNode("LPGBT.RWF.EPORTTX.EPTX23ENABLE"), 0x1) #master 11
        writeReg(getNode("LPGBT.RWF.EPORTTX.EPTX02ENABLE"), 0x1) #master 2

        #EPTXxxDriveStrength
        writeReg(getNode("LPGBT.RWF.EPORTTX.EPTX_CHN_CONTROL.EPTX6DRIVESTRENGTH"), 0x3) #master 6
        writeReg(getNode("LPGBT.RWF.EPORTTX.EPTX_CHN_CONTROL.EPTX4DRIVESTRENGTH"), 0x3) #master 4
        writeReg(getNode("LPGBT.RWF.EPORTTX.EPTX_CHN_CONTROL.EPTX8DRIVESTRENGTH"), 0x3) #master 8
        writeReg(getNode("LPGBT.RWF.EPORTTX.EPTX_CHN_CONTROL.EPTX0DRIVESTRENGTH"), 0x3) #master 0
        writeReg(getNode("LPGBT.RWF.EPORTTX.EPTX_CHN_CONTROL.EPTX11DRIVESTRENGTH"), 0x3) #master 11
        writeReg(getNode("LPGBT.RWF.EPORTTX.EPTX_CHN_CONTROL.EPTX2DRIVESTRENGTH"), 0x3) #master 2

        # enable mirror feature
        writeReg(getNode("LPGBT.RWF.EPORTTX.EPTX0MIRRORENABLE"), 0x1)
        writeReg(getNode("LPGBT.RWF.EPORTTX.EPTX1MIRRORENABLE"), 0x1)
        writeReg(getNode("LPGBT.RWF.EPORTTX.EPTX2MIRRORENABLE"), 0x1)
        writeReg(getNode("LPGBT.RWF.EPORTTX.EPTX3MIRRORENABLE"), 0x1)

        #turn on 40MHz clocks

        writeReg(getNode("LPGBT.RWF.EPORTCLK.EPCLK3FREQ"), 0x1)
        writeReg(getNode("LPGBT.RWF.EPORTCLK.EPCLK5FREQ"), 0x1)
        writeReg(getNode("LPGBT.RWF.EPORTCLK.EPCLK6FREQ"), 0x1)
        writeReg(getNode("LPGBT.RWF.EPORTCLK.EPCLK7FREQ"), 0x1)
        writeReg(getNode("LPGBT.RWF.EPORTCLK.EPCLK15FREQ"), 0x1)
        writeReg(getNode("LPGBT.RWF.EPORTCLK.EPCLK16FREQ"), 0x1)

        writeReg(getNode("LPGBT.RWF.EPORTCLK.EPCLK3DRIVESTRENGTH"), 0x3)
        writeReg(getNode("LPGBT.RWF.EPORTCLK.EPCLK5DRIVESTRENGTH"), 0x3)
        writeReg(getNode("LPGBT.RWF.EPORTCLK.EPCLK6DRIVESTRENGTH"), 0x3)
        writeReg(getNode("LPGBT.RWF.EPORTCLK.EPCLK7DRIVESTRENGTH"), 0x3)
        writeReg(getNode("LPGBT.RWF.EPORTCLK.EPCLK15DRIVESTRENGTH"), 0x3)
        writeReg(getNode("LPGBT.RWF.EPORTCLK.EPCLK16DRIVESTRENGTH"), 0x3)

    if (master):

        # turn on 80 Mbps EC clock
        writeReg(getNode("LPGBT.RWF.EPORTCLK.EPCLK28FREQ"), 0x2)
        writeReg(getNode("LPGBT.RWF.EPORTCLK.EPCLK28DRIVESTRENGTH"), 0x3)

        # turn on phase shifter clock
        writeReg(getNode("LPGBT.RWF.PHASE_SHIFTER.PS1DELAY_8"), 0x0)
        writeReg(getNode("LPGBT.RWF.PHASE_SHIFTER.PS1DELAY_7TO0"), 0x0)
        writeReg(getNode("LPGBT.RWF.PHASE_SHIFTER.PS1ENABLEFINETUNE"), 0x0)
        writeReg(getNode("LPGBT.RWF.PHASE_SHIFTER.PS1DRIVESTRENGTH"), 0x3)
        writeReg(getNode("LPGBT.RWF.PHASE_SHIFTER.PS1FREQ"), 0x1)
        writeReg(getNode("LPGBT.RWF.PHASE_SHIFTER.PS1PREEMPHASISMODE"), 0x0)

    print ("Configuring external control channels...")

    # enable EC output
    writeReg(getNode("LPGBT.RWF.EPORTTX.EPTXECENABLE"), 0x1)
    # enable EC input
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRXECENABLE"), 0x1)
    writeReg(getNode("LPGBT.RWF.EPORTRX.EPRXECTERM"), 0x1)

    print ("Configuring hsio inversion...")
    if (master):
        writeReg(getNode("LPGBT.RWF.CHIPCONFIG.HIGHSPEEDDATAININVERT"), 0x1)
    if (slave):
        writeReg(getNode("LPGBT.RWF.CHIPCONFIG.HIGHSPEEDDATAOUTINVERT"), 0x1)

    print ("Configuring gpio...")
    if (master):
        writeReg(getNode("LPGBT.RWF.PIO.PIODIRH"), 0x80 | 0x01) # set as outputs
        writeReg(getNode("LPGBT.RWF.PIO.PIODIRL"), 0x01 | 0x02) # set as outputs
        writeReg(getNode("LPGBT.RWF.PIO.PIOOUTH"), 0x80) # enable LED
        writeReg(getNode("LPGBT.RWF.PIO.PIOOUTL"), 0x00) #
    if (slave):
        writeReg(getNode("LPGBT.RWF.PIO.PIODIRH"), 0x02 | 0x04 | 0x08) # set as outputs
        writeReg(getNode("LPGBT.RWF.PIO.PIODIRL"), 0x00 | 0x00) # set as outputs
        writeReg(getNode("LPGBT.RWF.PIO.PIOOUTH"), 0x00) #
        writeReg(getNode("LPGBT.RWF.PIO.PIOOUTL"), 0x00) #


    print ("Finishing configuration...")
    #2.2.11. Finishing configuration
    #[0x0ef] POWERUP2
    writeReg(getNode("LPGBT.RWF.POWERUP.DLLCONFIGDONE"), 0x1)
    writeReg(getNode("LPGBT.RWF.POWERUP.PLLCONFIGDONE"), 0x1)

    if (force_pusm_ready):
        writeReg(getNode("LPGBT.RW.POWERUP.PUSMFORCESTATE"), 0x1)
        writeReg(getNode("LPGBT.RW.POWERUP.PUSMFORCEMAGIC"), 0xA3)
        writeReg(getNode("LPGBT.RW.POWERUP.PUSMSTATEFORCED"), 18)
        writeReg(getNode("LPGBT.RWF.POWERUP.PUSMPLLWDOGDISABLE"),0x1)
        writeReg(getNode("LPGBT.RWF.POWERUP.PUSMDLLWDOGDISABLE"),0x1)
    else:
        writeReg(getNode("LPGBT.RW.POWERUP.PUSMFORCESTATE"), 0x0)
        writeReg(getNode("LPGBT.RW.POWERUP.PUSMFORCEMAGIC"), 0x0)
        writeReg(getNode("LPGBT.RWF.POWERUP.PUSMPLLWDOGDISABLE"),0x0)
        writeReg(getNode("LPGBT.RWF.POWERUP.PUSMDLLWDOGDISABLE"),0x0)


if __name__ == '__main__':
   main()
