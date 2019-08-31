from rw_reg_dongle import *
from time import sleep

def main():

    parseXML()
    print "parsing complete..."

    romreg=readReg(getNode("LPGBT.RO.ROMREG"))
    if (romreg != 0xa5):
        print "Error: no communication with LPGBT. ROMREG=0x%x, EXPECT=0x%x" % (romreg, 0xa5)
        return

    # eom configuration (256 cycles = 6.4 us)

    writeReg(getNode("LPGBT.RW.EOM.EOMENDOFCOUNTSEL"), 0x1)
    #writeReg(getNode("LPGBT.RW.EOM.EOMENDOFCOUNTSEL"), 0x7)

    eyeimage = [[0 for y in range(32)] for x in range(64)]

    for y_axis  in range (32):

        # update yaxis

        writeReg(getNode("LPGBT.RW.EOM.EOMVOFSEL"), y_axis)

        for x_axis in range (64):

            # update xaxis
            writeReg(getNode("LPGBT.RW.EOM.EOMPHASESEL"), x_axis)

            # wait few miliseconds
            sleep(0.005)

            # start measurement
            writeReg(getNode("LPGBT.RW.EOM.EOMSTART"), 0x1)

            # wait until measurement is finished
            status = 0
            while (status != 0):
                status = readReg(getNode("LPGBT.RO.EOM.EOMSMSTATE"))

            countervalue = readReg(getNode("LPGBT.RO.EOM.EOMCOUNTER40MH")) << 8 |readReg(getNode("LPGBT.RO.EOM.EOMCOUNTER40ML"))

            eyeimage[x_axis][y_axis] = countervalue

            # deassert eomstart bit
            writeReg(getNode("LPGBT.RW.EOM.EOMSTART"), 0x0)


        percent_done = 100. * (y_axis*64. +64. ) / (32.*64.)
        print "%f percent done" % percent_done

    for y  in range (32):
        line = ""
        for x in range (64):
            if (eyeimage[x][y]>0):
                line = line + "x"
            else:
                line = line + "-"
        print line




if __name__ == '__main__':
    main()


