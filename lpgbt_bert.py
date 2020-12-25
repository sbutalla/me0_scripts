from rw_reg_dongle_chc import *
from time import sleep
import sys
import argparse

def main(system, boss):

    print ("Parsing xml file...")
    parseXML()
    print ("Parsing complete...")

    # Initialization (for CHeeseCake: reset and config_select)
    rw_initialize(system, boss)
    print ("Initialization Done")

    # Readback rom register to make sure communication is OK
    check_rom_readback()

    # Select the data source for the measurement
    writeReg(getNode("LPGBT.RW.BERT.COARSEBERTSOURCE"),14) # bert source to DLFRAME 
    writeReg(getNode("LPGBT.RW.BERT.FINEBERTSOURCE"),2) # prbs 7
    writeReg(getNode("LPGBT.RW.BERT.BERTMEASTIME"),15)
    writeReg(getNode("LPGBT.RW.BERT.SKIPDISABLE"),1)

    # Downlink frame contains 64 bits (2.56 Gbps)
    bits_per_clock_cycle = 64
    bits_checked = 2**31 * bits_per_clock_cycle

    # writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGDISABLEFRAMEALIGNERLOCKCONTROL") ,1)
    # writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGLOCKFILTERENABLE"), 0x0) # quickstart recommends 0
    # writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGWAITCDRTIME"), 0xa)

    # Start the measurement
    writeReg(getNode("LPGBT.RW.BERT.BERTSTART"),1)

    done = 0
    while (done==0):
        done = readReg(getNode("LPGBT.RO.BERT.BERTDONE"))
        print ("BERT done = %d" % done)

    err = readReg(getNode("LPGBT.RO.BERT.BERTPRBSERRORFLAG"))
    if (err):
        print ("ERROR: no data received")
        return

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
    print ("BER: " + str(ber))

    # Termination
    if system=="chc":
        chc_terminate()

def check_rom_readback():
    romreg=readReg(getNode("LPGBT.RO.ROMREG"))
    if (romreg != 0xA5):
        print ("ERROR: no communication with LPGBT. ROMREG=0x%x, EXPECT=0x%x" % (romreg, 0xA5))
        rw_terminate()
    else:
        print ("Successfully read from ROM. I2C communication OK")

if __name__ == '__main__':
    # Parsing arguments
    parser = argparse.ArgumentParser(description='LPGBT BER')
    parser.add_argument("-s", "--system", action="store", dest="system", help="system = chc or backend or dongle")
    parser.add_argument("-l", "--lpgbt", action="store", dest="lpgbt", help="lpgbt = boss or sub")

    if args.system == "chc":
        print ("Using Rpi CHeeseCake for checking configuration")
    elif args.system == "backend":
        #print ("Using Backend for checking configuration")
        print ("Only chc (Rpi Cheesecake) supported at the moment")
        sys.exit()
    elif args.system == "dongle":
        #print ("Using USB Dongle for checking configuration")
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
        print ("BER for boss LPGBT")
        boss=1
    elif (args.lpgbt=="sub"):
        print ("BER for sub LPGBT")
        boss=0
    else:
        print ("Please select boss or sub")
        sys.exit()
    if boss is None:
        sys.exit()

    main(args.system, boss)
