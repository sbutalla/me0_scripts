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

    cntsel = 0x7
    #num_clocks = 2**(cntsel + 1)
    writeReg(getNode("LPGBT.RW.EOM.EOMENDOFCOUNTSEL"), cntsel)
    writeReg(getNode("LPGBT.RW.EOM.EOMENABLE"), 1)

    writeReg(getNode("LPGBT.RWF.EQUALIZER.EQCAP"), 1)
    writeReg(getNode("LPGBT.RWF.EQUALIZER.EQRES0"), 1)
    writeReg(getNode("LPGBT.RWF.EQUALIZER.EQRES1"), 1)
    writeReg(getNode("LPGBT.RWF.EQUALIZER.EQRES2"), 1)
    writeReg(getNode("LPGBT.RWF.EQUALIZER.EQRES3"), 1)

    eyeimage = [[0 for y in range(32)] for x in range(64)]

    datavalregh = getNode("LPGBT.RO.EOM.EOMCOUNTERVALUEH")
    datavalregl = getNode("LPGBT.RO.EOM.EOMCOUNTERVALUEL")

    #cntvalregh = getNode("LPGBT.RO.EOM.EOMCOUNTER40MH")
    #cntvalregl = getNode("LPGBT.RO.EOM.EOMCOUNTER40ML")
    eomphaseselreg = getNode("LPGBT.RW.EOM.EOMPHASESEL")
    eomstartreg = getNode("LPGBT.RW.EOM.EOMSTART")
    eomstatereg = getNode("LPGBT.RO.EOM.EOMSMSTATE")
    eomvofsel = getNode("LPGBT.RW.EOM.EOMVOFSEL")

    cntvalmax = 0
    cntvalmin = 2**20

    ymin=1
    ymax=30
    xmin=0
    xmax=64

    for y_axis in range (ymin,ymax):
        # update yaxis
        writeReg(eomvofsel, y_axis)

        for x_axis in range (xmin,xmax):
            if (x_axis >= 32):
                x_axis_wr = 63-(x_axis-32)
            else:
                x_axis_wr = x_axis

            # update xaxis
            writeReg(eomphaseselreg, x_axis_wr)

            # wait few miliseconds
            sleep(0.002)

            # start measurement
            writeReg(eomstartreg, 0x1)

            # wait until measurement is finished
            status = 0
            while (status == 0):
                status = readReg(eomstatereg)

            #num_clocks_read = (readReg(cntvalregh)) << 8 |readReg(cntvalregl)
            countervalue = (readReg(datavalregh)) << 8 |readReg(datavalregl)
            if (countervalue > cntvalmax):
                cntvalmax = countervalue
            if (countervalue < cntvalmin):
                cntvalmin = countervalue

            #print (num_clocks_read)
            #print (num_clocks)

            eyeimage[x_axis][y_axis] = countervalue
            #print (4149 - countervalue)

            # deassert eomstart bit
            writeReg(eomstartreg, 0x0)

            #line = line + ("%x" % (eyeimage[x][y]/260))
            #print ("%x" % (eyeimage[x_axis][y_axis]/260))

            #print countervalue/1000
            sys.stdout.write("%x" % (eyeimage[x_axis][y_axis]/1000))
            sys.stdout.flush()

        sys.stdout.write("\n")

        #percent_done = 100. * (y_axis*64. +64. ) / (32.*64.)
        #print ("%f percent done" % percent_done)

    print ("Counter value max=%d" % cntvalmax)
    f = open ("eye_data.py", "w+")
    f.write ("eye_data=[\n")
    for y  in range (ymin,ymax):
        f.write ("    [")
        for x in range (xmin,xmax):
            # normalize for plotting
            f.write("%d" % (100*(cntvalmax - eyeimage[x][y])/(cntvalmax-cntvalmin)))
            if (x<(xmax-1)):
                f.write(",")
            else:
                f.write("]")
        if (y<(ymax-1)):
            f.write(",\n")
        else:
            f.write("]\n")

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
    parser = argparse.ArgumentParser(description='LPGBT EYE')
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
        print ("EYE for boss LPGBT")
        boss=1
    elif (args.lpgbt=="sub"):
        print ("EYE for sub LPGBT")
        boss=0
    else:
        print ("Please select boss or sub")
        sys.exit()
    if boss is None:
        sys.exit()

    main(args.system, boss)
