from rw_reg_dongle_chc import *
from time import sleep
import sys
import os
import glob
import argparse

def main(system, count, eq_attn, eq_cap, eq_res3, eq_res2, eq_res1, eq_res0, boss):

    print ("Parsing xml file...")
    parseXML()
    print ("Parsing complete...")

    # Initialization (for CHeeseCake: reset and config_select)
    rw_initialize(system, boss)
    print ("Initialization Done")

    # Readback rom register to make sure communication is OK
    if system!="dryrun":
        check_rom_readback()

    # Check if lpGBT is READY
    if system!="dryrun":
        pusmstate = readReg(getNode("LPGBT.RO.PUSM.PUSMSTATE"))
        if (pusmstate==18):
            print ("lpGBT status is READY")
        else:
            print ("lpGBT is not READY, configure lpGBT first")
            if system=="chc":
                chc_terminate()
            sys.exit()

    cntsel = count
    writeReg(getNode("LPGBT.RW.EOM.EOMENDOFCOUNTSEL"), cntsel, 0)
    writeReg(getNode("LPGBT.RW.EOM.EOMENABLE"), 1, 0)

    #ymin=1
    #ymax=30
    ymin=0
    ymax=31
    xmin=0
    xmax=64

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

    eq_attn_node = getNode("LPGBT.RWF.EQUALIZER.EQATTENUATION")
    eq_cap_node = getNode("LPGBT.RWF.EQUALIZER.EQCAP")
    eq_res3_node = getNode("LPGBT.RWF.EQUALIZER.EQRES3")
    eq_res2_node = getNode("LPGBT.RWF.EQUALIZER.EQRES2")
    eq_res1_node = getNode("LPGBT.RWF.EQUALIZER.EQRES1")
    eq_res0_node = getNode("LPGBT.RWF.EQUALIZER.EQRES0")

    if os.path.isdir("eye_scan_results"):
        files = glob.glob("eye_scan_results/*.py", recursive=True)
        for f in files:
            os.remove(f)
    else:
        os.mkdir("eye_scan_results")

    print ("\n")
    # Start Loop Over Equalizer Settings
    for eq_attn_setting in eq_attn:
        writeReg(eq_attn_node, int(eq_attn_setting,16), 0)
        for eq_cap_setting in eq_cap:
            writeReg(eq_cap_node, int(eq_cap_setting,16), 0)
            for eq_res3_setting in eq_res3:
                writeReg(eq_res3_node, int(eq_res3_setting,16), 0)
                for eq_res2_setting in eq_res2:
                    writeReg(eq_res2_node, int(eq_res2_setting,16), 0)
                    for eq_res1_setting in eq_res1:
                        writeReg(eq_res1_node, int(eq_res1_setting,16), 0)
                        for eq_res0_setting in eq_res0:
                            writeReg(eq_res0_node, int(eq_res0_setting,16), 0)
                            print ("Scanning EQATTENUATION = " + eq_attn_setting)
                            print ("Scanning EQCAP = " + eq_cap_setting)
                            print ("Scanning EQRES3 = " + eq_res3_setting)
                            print ("Scanning EQRES2 = " + eq_res2_setting)
                            print ("Scanning EQRES1 = " + eq_res1_setting)
                            print ("Scanning EQRES0 = " + eq_res0_setting)

                            #eyeimage = [[0 for y in range(32)] for x in range(64)]
                            eyeimage = [[0 for y in range(31)] for x in range(64)]
                            cntvalmax = 0
                            cntvalmin = 2**20

                            # Start loop for Eye Scan
                            for y_axis in range (ymin,ymax):
                                # update yaxis
                                writeReg(eomvofsel, y_axis, 0)

                                for x_axis in range (xmin,xmax):
                                    if (x_axis >= 32):
                                        x_axis_wr = 63-(x_axis-32)
                                    else:
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
                            # End loop for Eye Scan
                            sys.stdout.write("\n")

                            print ("Counter value max=%d \n" % cntvalmax)
                            f = open("eye_scan_results/eye_data_eqa_"+eq_attn_setting+"_eqc_"+eq_cap_setting+"_eqr3_"+eq_res3_setting+"_eqr2_"+eq_res2_setting+"_eqr1_"+eq_res1_setting+"_eqr0_"+eq_res0_setting+".py", "w+")
                            f.write("eye_data=[\n")
                            for y  in range (ymin,ymax):
                                f.write("    [")
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
    # End Loop Over Equalizer Settings

    # Setting back Default Equalizer settings
    writeReg(getNode("LPGBT.RWF.EQUALIZER.EQATTENUATION"), 0x3, 0)
    writeReg(getNode("LPGBT.RWF.EQUALIZER.EQCAP"), 0x0, 0)
    writeReg(getNode("LPGBT.RWF.EQUALIZER.EQRES0"), 0x0, 0)
    writeReg(getNode("LPGBT.RWF.EQUALIZER.EQRES1"), 0x0, 0)
    writeReg(getNode("LPGBT.RWF.EQUALIZER.EQRES2"), 0x0, 0)
    writeReg(getNode("LPGBT.RWF.EQUALIZER.EQRES3"), 0x0, 0)

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
    parser.add_argument("-s", "--system", action="store", dest="system", help="system = chc or backend or dongle or dryrun")
    parser.add_argument("-l", "--lpgbt", action="store", dest="lpgbt", help="lpgbt = boss or sub")
    parser.add_argument("-c", "--count", action="store", dest="count", default="0x7", help="EOMendOfCountSel[3:0] in hex")
    parser.add_argument("-eqa", "--eq_attn", action="store", nargs='+', dest="eq_attn", default=["0x3"], help="EQAttenuation[1:0] (in hex) = See lpGBT manual Section 15.1.5 for options, default=[0x3]")
    parser.add_argument("-eqc", "--eq_cap", action="store", nargs='+', dest="eq_cap", default=["0x0"], help="EQCap[1:0] (in hex) = See lpGBT manual Section 15.1.5 for options, default=[0x0]")
    parser.add_argument("-eqr3", "--eq_res3", action="store", nargs='+', dest="eq_res3", default=["0x0"], help="EQRes3[1:0] (in hex) = See lpGBT manual Section 15.1.5 for options, default=[0x0]")
    parser.add_argument("-eqr2", "--eq_res2", action="store", nargs='+', dest="eq_res2", default=["0x0"], help="EQRes2[1:0] (in hex) = See lpGBT manual Section 15.1.5 for options, default=[0x0]")
    parser.add_argument("-eqr1", "--eq_res1", action="store", nargs='+', dest="eq_res1", default=["0x0"], help="EQRes1[1:0] (in hex) = See lpGBT manual Section 15.1.5 for options, default=[0x0]")
    parser.add_argument("-eqr0", "--eq_res0", action="store", nargs='+', dest="eq_res0", default=["0x0"], help="EQRes0[1:0] (in hex) = See lpGBT manual Section 15.1.5 for options, default=[0x0]")
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

    if int(args.count,16) > 15:
        print ("EOMendOfCountSel[3:0] can be max 4 bits")
        sys.exit()

    for e in args.eq_attn:
        if int(e,16) > 3:
            print ("Setting can be max 2 bits, therefore: 0x0, 0x1, 0x2, 0x3")
            sys.exit()
    for e in args.eq_cap:
        if int(e,16) > 3:
            print ("Setting can be max 2 bits, therefore: 0x0, 0x1, 0x2, 0x3")
            sys.exit()
    for e in args.eq_res3:
        if int(e,16) > 3:
            print ("Setting can be max 2 bits, therefore: 0x0, 0x1, 0x2, 0x3")
            sys.exit()
    for e in args.eq_res2:
        if int(e,16) > 3:
            print ("Setting can be max 2 bits, therefore: 0x0, 0x1, 0x2, 0x3")
            sys.exit()
    for e in args.eq_res1:
        if int(e,16) > 3:
            print ("Setting can be max 2 bits, therefore: 0x0, 0x1, 0x2, 0x3")
            sys.exit()
    for e in args.eq_res0:
        if int(e,16) > 3:
            print ("Setting can be max 2 bits, therefore: 0x0, 0x1, 0x2, 0x3")
            sys.exit()

    main(args.system, int(args.count,16), args.eq_attn, args.eq_cap, args.eq_res3, args.eq_res2, args.eq_res1, args.eq_res0, boss)
