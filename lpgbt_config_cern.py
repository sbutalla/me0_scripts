from rw_reg_dongle import *

def configLPGBT():

    parseXML()

    mpeek (0x1ca)

    response1 = mpeek(0x141)
    print 'Reading register 0x141 : 0x%.2x'%(response1)

    # Demonstrated control of RefClk termination:
    #mpoke(0x03b,0x01)

    response2 = mpeek(0x03b)
    print 'Reading register 0x03b : 0x%.2x'%(response2)

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

    # datapath configuration
    mpoke(0x132,0x10) # enabled fec counter for the downlink
    #mpoke(0x132,0x10 | 0x2) # enabled fec counter for the downlink

    #$# Uplink:  ePort Inputs DLL"s
    #$mpoke(0x034,0xa1)

    #$# Uplink: ePort Inputs Group 1 at 640 Mbps:
    #$mpoke(0x0c5,0x9a)
    #$mpoke(0x0d0,0x02)
    #$mpoke(0x0d2,0x02)

    #    Set H.S. Uplink Driver current:
    mpoke(0x039,0x20)

    #   Enable PowerGood @ 1.0 V, Delay 100 ms:
    mpoke(0x03e,0xdc)

    # Select TO0 internal signal:
    mpoke(0x133,2) #40 mhz clock

    # setup & enable ch0 in eTx group 3:
    #mpoke(0x0a7,0x80)
    #mpoke(0x0b8,0x03)
    #mpoke(0x0aa,0x10)

    # select test pattern for eTx group 3: (initial value from Ted : 0x40 (PRBS), 0xc0 = constant, 0x80 = binary)
    #mpoke(0x11d,0x40)

    writeReg(getNode("LPGBT.RWF.CHIPCONFIG.HIGHSPEEDDATAININVERT"), 0x1)
    writeReg(getNode("LPGBT.RWF.CHIPCONFIG.HIGHSPEEDDATAOUTINVERT"), 0x0)

    writeReg(getNode("LPGBT.RWF.CALIBRATION.FAMAXHEADERFOUNDCOUNT"), 0xA)
    writeReg(getNode("LPGBT.RWF.CALIBRATION.FAMAXHEADERFOUNDCOUNTAFTERNF"), 0xA)
    writeReg(getNode("LPGBT.RWF.CALIBRATION.FAMAXHEADERNOTFOUNDCOUNT"), 0xA)
    writeReg(getNode("LPGBT.RWF.CALIBRATION.FAMAXSKIPCYCLECOUNTAFTERNF"), 0xA)

    writeReg(getNode("LPGBT.RWF.CALIBRATION.EPRXUNLOCKTHRESHOLD"), 0x5)

    writeReg(getNode("LPGBT.RWF.EQUALIZER.EQATTENUATION"), 0x3)
    #writeReg(getNode("LPGBT.RW.BERT.SKIPDISABLE"),1)
    #writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGDISABLEFRAMEALIGNERLOCKCONTROL"), 0x1)
    #writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGLOCKFILTERENABLE"), 0x0)
    #writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGWAITCDRTIME"), 0xa)
    #writeReg(getNode("LPGBT.RW.RESET.RSTFRAMEALIGNER"), 1)

    # Finally, Set pll&dllConfigDone to run chip:
    mpoke(0x0ef,0x06)

    #writeReg(getNode("LPGBT.RWF.CHIPCONFIG.CHIPADDRESSBAR"), 0x7)
    # pattern
    #constPatternSerializer(0xaaaaaaaa)

    #writeReg(getNode("LPGBT.RW.TESTING.LDDATASOURCE"), 0x1)

def constPatternSerializer(pattern=0xaabbccdd):
    print('Configuring lpGBT to generate constant pattern on up-link : 0x%.8x'%(pattern))
    # Select H.S. Uplink Test Pattern: (Table 14.1 lpGBT manual)
    mpoke(0x118,0x0C)  ## const pattern
    #mpoke(0x118,0x07)  ## clock
    #mpoke(0x118,0x01)  #prbs 7
    mpoke(0x119,0x00)  ## take data from serializer
    for i in range(0,4):
        cPattern = ( pattern & (0xFF << 8*(3-i)) ) >> (8*(3-i))
        print('Configuring 0x%.3x -- 0x%.2x'%(0x11e+i, cPattern))
        mpoke(0x11e+i,cPattern)

#def constPatternEPorts(pattern=0x77778888):
#    print('Configuring lpGBT in pattern mode from eports')
#    mpoke(0x118, 0x00) ## data mode for serializer
#    # data source for groups
#    elink_data_source = 0b100 ## 0 - eport data, 1 - prbs, 2 - cntup, 3 - cntdwn, 4 - const patter, 5 - const pattern inv, ...
#    mpoke(0x119, (0b00 << 6) | (elink_data_source << 3) | (elink_data_source << 0) ) ## data mode for serializer = 0 (data from elinks) and group 0
#    mpoke(0x11a, (elink_data_source << 3) | (elink_data_source << 0) ) # groups 3,2
#    mpoke(0x11b, (elink_data_source << 3) | (elink_data_source << 0) ) # groups 5,4
#    mpoke(0x11c, (elink_data_source << 0)) # group 6
#
#    # set pattern
#    for i in range(0,4):
#        cPattern = ( pattern & (0xFF << 8*(3-i)) ) >> (8*(3-i))
#        print('Configuring 0x%.3x -- 0x%.2x'%(0x11e+i, cPattern))
#        mpoke(0x11e+i,cPattern)
#
#
if __name__ == '__main__':
   configLPGBT()
