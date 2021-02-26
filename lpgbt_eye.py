from rw_reg_lpgbt import *
from time import sleep
import sys
import os
import argparse

def main(system, count, boss):

    cntsel = count
    writeReg(getNode("LPGBT.RW.EOM.EOMENDOFCOUNTSEL"), cntsel, 0)
    writeReg(getNode("LPGBT.RW.EOM.EOMENABLE"), 1, 0)

    # Equalizer settings
    writeReg(getNode("LPGBT.RWF.EQUALIZER.EQCAP"), 0x1, 0)
    writeReg(getNode("LPGBT.RWF.EQUALIZER.EQRES0"), 0x1, 0)
    writeReg(getNode("LPGBT.RWF.EQUALIZER.EQRES1"), 0x1, 0)
    writeReg(getNode("LPGBT.RWF.EQUALIZER.EQRES2"), 0x1, 0)
    writeReg(getNode("LPGBT.RWF.EQUALIZER.EQRES3"), 0x1, 0)

    #eyeimage = [[0 for y in range(32)] for x in range(64)]
    eyeimage = [[0 for y in range(31)] for x in range(64)]

    datavalregh = getNode("LPGBT.RO.EOM.EOMCOUNTERVALUEH")
    datavalregl = getNode("LPGBT.RO.EOM.EOMCOUNTERVALUEL")

    #cntvalregh = getNode("LPGBT.RO.EOM.EOMCOUNTER40MH")
    #cntvalregl = getNode("LPGBT.RO.EOM.EOMCOUNTER40ML")
    eomphaseselreg = getNode("LPGBT.RW.EOM.EOMPHASESEL")
    eomstartreg = getNode("LPGBT.RW.EOM.EOMSTART")
    eomstatereg = getNode("LPGBT.RO.EOM.EOMSMSTATE")
    eombusyreg = getNode("LPGBT.RO.EOM.EOMBUSY")
    eomendreg = getNode("LPGBT.RO.EOM.EOMEND")
    eomvofsel = getNode("LPGBT.RW.EOM.EOMVOFSEL")

    cntvalmax = 0
    cntvalmin = 2**20

    #ymin=1
    #ymax=30
    ymin=0
    ymax=31
    xmin=0
    xmax=64

    print ("Starting loops: \n")
    for y_axis in range (ymin,ymax):
        # update yaxis
        writeReg(eomvofsel, y_axis, 0)

        for x_axis in range (xmin,xmax):
            #if (x_axis >= 32):
            #    x_axis_wr = 63-(x_axis-32)
            #else:
            x_axis_wr = x_axis

            # update xaxis
            writeReg(eomphaseselreg, x_axis_wr, 0)

            # wait few miliseconds
            sleep(0.005)

            # start measurement
            writeReg(eomstartreg, 0x1, 0)

            # wait until measurement is finished
            busy = 1
            end = 0
            while (busy and not end):
                if system!="dryrun":
                    busy = readReg(eombusyreg)
                    end = readReg(eomendreg)
                else:
                    busy = 0
                    end = 1

            countervalue = (readReg(datavalregh)) << 8 |readReg(datavalregl)
            if (countervalue > cntvalmax):
                cntvalmax = countervalue
            if (countervalue < cntvalmin):
                cntvalmin = countervalue
            eyeimage[x_axis][y_axis] = countervalue

            # deassert eomstart bit
            writeReg(eomstartreg, 0x0, 0)

            #sys.stdout.write("%x" % (eyeimage[x_axis][y_axis]/1000))
            sys.stdout.write("%x" % (eyeimage[x_axis][y_axis]))
            sys.stdout.flush()

        sys.stdout.write("\n")
        #percent_done = 100. * (y_axis*64. +64. ) / (32.*64.)
        #print ("%f percent done" % percent_done)
    print ("\nEnd Loops \n")

    print ("Counter value max=%d" % cntvalmax)
    if not os.path.isdir("eye_scan_results"):
        os.mkdir("eye_scan_results")
    f = open ("eye_scan_results/eye_data.txt", "w+")
    f.write ("eye_data=[\n")
    for y  in range (ymin,ymax):
        f.write ("    [")
        for x in range (xmin,xmax):
            # normalize for plotting
            if system!="dryrun":
                f.write("%d" % (100*(cntvalmax - eyeimage[x][y])/(cntvalmax-cntvalmin)))
            else:
                f.write("0")
            if (x<(xmax-1)):
                f.write(",")
            else:
                f.write("]")
        if (y<(ymax-1)):
            f.write(",\n")
        else:
            f.write("]\n")

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
    parser.add_argument("-s", "--system", action="store", dest="system", help="system = chc or backend or dongle or dryrun")
    parser.add_argument("-l", "--lpgbt", action="store", dest="lpgbt", help="lpgbt = only boss allowed")
    parser.add_argument("-o", "--ohid", action="store", dest="ohid", help="ohid = 0-7 (only needed for backend)")
    parser.add_argument("-g", "--gbtid", action="store", dest="gbtid", help="gbtid = 0, 1 (only needed for backend)")
    parser.add_argument("-c", "--count", action="store", dest="count", default="0x7", help="EOMendOfCountSel[3:0] in hex")
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
        print ("EYE for boss LPGBT")
        boss=1
    elif (args.lpgbt=="sub"):
        #print ("EYE for sub LPGBT")
        print ("EYE only for boss since sub is only TX mode")
        boss=0
        sys.exit()
    else:
        print ("Please select boss")
        sys.exit()
    if boss is None:
        sys.exit()
    
    if args.system == "backend":
        if args.ohid is None:
            print ("Need OHID for backend")
            sys.exit()
        if args.gbtid is None:
            print ("Need GBTID for backend")
            sys.exit()
        if int(args.ohid)>7:
            print ("Only OHID 0-7 allowed")
            sys.exit()
        if int(args.gbtid)>1:
            print ("Only GBTID 0 and 1 allowed")
            sys.exit() 
    else:
        if args.ohid is not None or args.gbtid is not None:
            print ("OHID and GBTID only needed for backend")
            sys.exit()

    if int(args.count,16) > 15:
        print ("EOMendOfCountSel[3:0] can be max 4 bits")
        sys.exit()

    # Parsing Registers XML File
    print("Parsing xml file...")
    parseXML()
    print("Parsing complete...")

    # Initialization (for CHeeseCake: reset and config_select)
    rw_initialize(args.system, boss, args.ohid, args.gbtid)
    print("Initialization Done\n")
    
    # Readback rom register to make sure communication is OK
    if args.system!="dryrun":
        check_rom_readback()

    # Check if lpGBT is READY
    check_lpgbt_ready(args.ohid, args.gbtid)

    try:
        main(args.system, int(args.count,16), boss)
    except KeyboardInterrupt:
        print ("\nKeyboard Interrupt encountered")
        rw_terminate()
    except EOFError:
        print ("\nEOF Error")
        rw_terminate()

    # Termination
    rw_terminate()

