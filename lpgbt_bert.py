from rw_reg_dongle import *
from time import sleep

def main():

    parseXML()
    print "parsing complete..."

    romreg=readReg(getNode("LPGBT.RO.ROMREG"))
    if (romreg != 0xa5):
        print "Error: no communication with LPGBT. ROMREG=0x%x, EXPECT=0x%x" % (romreg, 0xa5)
        return

    writeReg(getNode("LPGBT.RW.BERT.SKIPDISABLE"),1)

    # // select the data source for the measurement
    #writeReg(getNode("LPGBT.RW.BERT.COARSEBERTSOURCE"),0xe)
    #writeReg(getNode("LPGBT.RW.BERT.BERTSOURCE"),2)
    mpoke(0x126, 0xc3)

    # set the measurement time to 2**31 clock cycles (2.1G * 25 ns = 53.6s)
    writeReg(getNode("LPGBT.RW.BERT.BERTMEASTIME"),15)

    # Downlink frame contains 64 bits (2.56 Gbps)
    bits_per_clock_cycle = 64

    bits_checked = 2**31 * bits_per_clock_cycle


    #
    # writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGDISABLEFRAMEALIGNERLOCKCONTROL") ,1)
    # writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGLOCKFILTERENABLE"), 0x0) # quickstart recommends 0
    # writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGWAITCDRTIME"), 0xa)

    # start the measurement

    writeReg(getNode("LPGBT.RW.BERT.BERTSTART"),1)

    done = 0
    while (done==0):
        done = readReg (getNode("LPGBT.RO.BERT.BERTDONE"))
        print "BERT done = %d" % done

    err = readReg (getNode("LPGBT.RO.BERT.BERTPRBSERRORFLAG"))
    if (err):
        print ("ERROR: no data received")
        return

    print mpeek (0x1bf)

    # read the result
    bert_result = 0
    bert_result |= readReg(getNode("LPGBT.RO.BERT.BERTERRORCOUNT0")) << 0
    bert_result |= readReg(getNode("LPGBT.RO.BERT.BERTERRORCOUNT1")) << 8
    bert_result |= readReg(getNode("LPGBT.RO.BERT.BERTERRORCOUNT2")) << 16
    bert_result |= readReg(getNode("LPGBT.RO.BERT.BERTERRORCOUNT3")) << 24
    bert_result |= readReg(getNode("LPGBT.RO.BERT.BERTERRORCOUNT4")) << 32

    # stop the measurement by deaserting the start bit
    writeReg(getNode("LPGBT.RW.BERT.BERTSTART"),0)
    writeReg(getNode("LPGBT.RW.BERT.COARSEBERTSOURCE"),0)
    writeReg(getNode("LPGBT.RW.BERT.BERTSOURCE"),0)

    # calculate Bit Error Rate
    ber = bert_result / bits_checked

    print ber

if __name__ == '__main__':
    main()


