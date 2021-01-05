from rw_reg_dongle_chc import *
from time import sleep, time
import sys
import argparse

FUSE_TIMEOUT_MS = 500
TOTAL_EFUSE_ON_TIME_MS = 0

def main(system, boss, input_fusing_file, reset_before_config, fuse_minimal, readback=0):
    gbt_rpi_chc.disarm_fuse(0)
    gbt_rpi_chc.disarm_fuse(1)

    print("Parsing xml file...")
    parseXML()
    print("Parsing complete...")

    # Initialization (for CHeeseCake: reset and config_select)
    rw_initialize(system, boss)
    print("Initialization Done")

    # Readback rom register to make sure communication is OK
    if system != "dryrun":
        check_rom_readback()

    # Optionally reset LPGBT
    if (reset_before_config):
        reset_lpgbt(readback)

    if input_config_file is not None:
        fuse_from_file(input_fusing_file)

    if fuse_minimal:
        fuse_minimal_configuration()

def fuse_from_file(filename):
    f = open(filename, 'r')
    config = f.read()
    config = config.split('\n')
    data = 0x0

    write_fuse_magic(1)

    print("Fusing from file \"%s\"" % filename)
    en = "No"
    while (en != "yes"):
        en = raw_input("please type \"yes\" to continue: ")

    for reg_addr in range(0, len(config) - 1):

        # maximum fusible register
        # DONT FUSE 0xEF HERE.. put it in a separate function for safety w/ updateEnable
        if (reg_addr >= 0xef):
            return

        if (reg_addr % 4 == 0):
            data = 0

        value = int(config[reg_addr], 16)
        data |= value << (8 * reg_addr % 4)

        if (reg_addr % 4 == 3) and data != 0:
            write_blow_and_check_fuse(reg_addr & 0xfffc, data, True)

    write_fuse_magic(0)

def check_fuse_block_data(adr, data, fullblock=False):

    fuse_block_adr    = adr & 0xfffc
    fuse_block_subadr = adr % 4

    mpoke(0x10e, 0xff&(fuse_block_adr>>8)) # adr high bits 15:8 [0x10e] FUSEBlowAddH
    mpoke(0x10f, 0xff&(fuse_block_adr>>0)) # adr low bits 7:0 [0x10f] FUSEBlowAddL

    # write fuseread on
    # [0x109] FUSEControl
    # Bit 7:4 - FuseBlowPulseLength[3:0] - Duration of fuse blowing pulse (default:12).
    # Bit 1 - FuseRead - Execute fuse readout sequence.
    # Bit 0 - FuseBlow - Execute fuse blowing sequence.
    mpoke(0x109, 0xC2)


    valid = False
    while (not valid):
        valid = (0x1 & ((mpeek(0x1a1)) >> 2))

    read=4*[0]

    read[0] = mpeek(0x1a2) # [0x1a2] FUSEValuesA
    read[1] = mpeek(0x1a3) # [0x1a3] FUSEValuesB
    read[2] = mpeek(0x1a4) # [0x1a4] FUSEValuesC
    read[3] = mpeek(0x1a5) # [0x1a5] FUSEValuesD

    # write fuseread off
    # [0x109] FUSEControl
    # Bit 7:4 - FuseBlowPulseLength[3:0] - Duration of fuse blowing pulse (default:12).
    # Bit 1 - FuseRead - Execute fuse readout sequence.
    # Bit 0 - FuseBlow - Execute fuse blowing sequence.
    mpoke(0x109, 0xC0)

    read_dword = 0

    if (fullblock):
        read_dword = (read[0]) | (read[1]<<8) | (read[2] << 16) | (read[3] << 24);
    else:
        read_dword = read[fuse_block_subadr]

    print "\tCHECKING FUSE ADR=%X, BLOCK=%X sub%X, VALID=%d, DATA_EXPECT=%X, DATA_READ=%X" % (adr, fuse_block_adr, fuse_block_subadr, valid, data, read_dword)
    return data==read_dword


def write_fuse_block_data(adr, data, fullblock=False):


    fuse_block_adr    = adr & 0xfffc
    fuse_block_subadr = adr % 4


    ok = 1


    # write address
    ok &= writeReg(0x10e, 0xff&(fuse_block_adr>>8)) # [0x10e] FUSEBlowAddH
    ok &= writeReg(0x10f, 0xff&(fuse_block_adr>>0)) # [0x10f] FUSEBlowAddL


    # zero out the rest of the address block to prevent accidental fusing
    if (not fullblock):
       ok &= writeAndCheckAddr(0x10A, 0)
       ok &= writeAndCheckAddr(0x10B, 0)
       ok &= writeAndCheckAddr(0x10C, 0)
       ok &= writeAndCheckAddr(0x10D, 0)


    if (fullblock):
        ok &= writeAndCheckAddr(0x10A, 0xff & (data >> 0))
        ok &= writeAndCheckAddr(0x10B, 0xff & (data >> 8))
        ok &= writeAndCheckAddr(0x10C, 0xff & (data >> 16))
        ok &= writeAndCheckAddr(0x10D, 0xff & (data >> 24))


    else:
        if (fuse_block_subadr==0):
            ok &= writeAndCheckAddr(0x10A, data)
        elif (fuse_block_subadr==1):
            ok &= writeAndCheckAddr(0x10B, data)
        elif (fuse_block_subadr==2):
            ok &= writeAndCheckAddr(0x10C, data)
        elif (fuse_block_subadr==3):
            ok &= writeAndCheckAddr(0x10D, data)


    if (not ok):
        print "Failed to read back fuse wdata block"
        sys.exit()


    return ok

def blow_fuse():
    global TOTAL_EFUSE_ON_TIME_MS


    adr = 0;


    adr |= mpeek (0x10e) << 8
    adr |= mpeek (0x10f) << 0


    rd = 0;
    rd |= mpeek(0x10A) << 0
    rd |= mpeek(0x10B) << 8
    rd |= mpeek(0x10C) << 16
    rd |= mpeek(0x10D) << 24
    print ("Blowing Fuse with ADR=%04X, DATA=%08X" % (adr, rd))


    mpoke(0x109, 0xC0)
    ###ARE YOU SURE YOU WANT TO FUSE###
    #gbt_rpi_chc.arm_fuse(boss)
    t0_efusepower = time()


    # https://pdf1.alldatasheet.com/datasheet-pdf/view/931712/TI1/LP2985A.html
    #sleep (0.01) # datasheet says the startup time is around 10ms with 150mA load (we have almost no load when using PIZZA)


    # write fuseblow on
    # [0x109] FUSEControl
    # Bit 7:4 - FuseBlowPulseLength[3:0] - Duration of fuse blowing pulse (default:12).
    # Bit 1 - FuseRead - Execute fuse readout sequence.
    # Bit 0 - FuseBlow - Execute fuse blowing sequence.
    mpoke(0x109, 0xC1) # wr


    #wait for fuseblowdone
    done = 0;
    t0 = time()
    while (done==0):
        done = (0x1 & ((mpeek(0x1a1)) >> 1))
        if int(round((time() - t0) * 1000)) > FUSE_TIMEOUT_MS:
            gbt_rpi_chc.disarm_fuse(boss)
            mpoke(0x109, 0xC0) # wr
            TOTAL_EFUSE_ON_TIME_MS += int(round((time() - t0_efusepower) * 1000))
            print "ERROR: Fusing operation took longer than %dms and was terminated due to a timeout" % FUSE_TIMEOUT_MS
            print "Total efuse power on time: %dms" % TOTAL_EFUSE_ON_TIME_MS
            sys.exit()




    gbt_rpi_chc.disarm_fuse(boss)
    TOTAL_EFUSE_ON_TIME_MS += int(round((time() - t0_efusepower) * 1000))
    print "Total efuse power on time: %dms" % TOTAL_EFUSE_ON_TIME_MS


    err = (0x1 & ((mpeek(0x1a1)) >> 3))
    print "\tFuse blown, err=%d" % err


    # write fuseblow on
    # [0x109] FUSEControl
    # Bit 7:4 - FuseBlowPulseLength[3:0] - Duration of fuse blowing pulse (default:12).
    # Bit 1 - FuseRead - Execute fuse readout sequence.
    # Bit 0 - FuseBlow - Execute fuse blowing sequence.
    mpoke(0x109, 0xC0) # wr

# sets fuse value, blows the fuse, and checks the result
# it can operate on a sub-address (one byte out of 4 in the fuse block)
# whenever fullblock is set to false
def write_blow_and_check_fuse  (adr,data,fullblock=False):
   if write_fuse_block_data(adr, data, fullblock):
      blow_fuse()
      check_fuse_block_data(adr,data,fullblock)

def fuse_chip_id():


   print ("Fusing chip ID and user ID...")


   #ans = raw_input("enter chip ID to fuse: ")
   #chip_id = int(ans, 0)
   #print ("fusing with chip id 0x%08X: " % chip_id)


   ans = raw_input("enter user ID to fuse: ")
   user_id = int(ans, 0)
   print ("fusing with user id 0x%08X: " % user_id)


   print ("INITIATING FUSING PROCEDURE OF CHIPID + USERID REGISTER")


   en="No"
   while (en!="yes"):
        en = raw_input ("please type \"yes\" to continue: ")


   write_fuse_magic(True)


   #Load fuse address into the REG_FUSEBLOWADDL and REG_FUSEBlowAddH registers.


   write_blow_and_check_fuse (0x003,(0 >> 0)  & 0xff) #[0x003] CHIPID3 BITS [ 7: 0]
   write_blow_and_check_fuse (0x002,(0 >> 8)  & 0xff) #[0x002] CHIPID2 BITS [15: 8]
   write_blow_and_check_fuse (0x001,(0 >> 16) & 0xff) #[0x001] CHIPID1 BITS [23:16]
   write_blow_and_check_fuse (0x000,(0 >> 24) & 0xff) #[0x000] CHIPID0 BITS [31:24]


   write_blow_and_check_fuse (0x007,(user_id >> 0)  & 0xff) #[0x007] USERID3 BITS [ 7: 0]
   write_blow_and_check_fuse (0x006,(user_id >> 8)  & 0xff) #[0x006] USERID2 BITS [15: 8]
   write_blow_and_check_fuse (0x005,(user_id >> 16) & 0xff) #[0x005] USERID1 BITS [23:16]
   write_blow_and_check_fuse (0x004,(user_id >> 24) & 0xff) #[0x004] USERID0 BITS [31:24]


   write_fuse_magic(False)

def fuse_minimal_config():


   # [0x020] CLKGConfig0
   # Bit 7:4 - CLKGCalibrationEndOfCount[3:0] - Selects the VCO calibration race goal in number of clock cycles between refClk (refClkCounter) and vco_40MHz (vcoClkCounter) (2^(CLKGCalibrationEndOfCount[3:0]+1)); default: 12
   # Bit 3:0 - CLKGBiasGenConfig[3:0] - Bias DAC for the charge pumps [0 : 8 : 120] uA; default: 8
   write_blow_and_check_fuse(0x020, 0xC8)


   # [0x025] CLKGCDRPropCur
   # Bit 7:4 - CLKGCDRPropCurWhenLocked[3:0] - CDR's Alexander phase detector proportional current path when in locked state [0 : 5.46 : 82] uA; default: 5
   # Bit 3:0 - CLKGCDRPropCur[3:0] - CDR's Alexander phase detector proportional current path when in locking state [0 : 5.46 : 82] uA; default: 5
   write_blow_and_check_fuse(0x025, 0x55)


   # [0x026] CLKGCDRIntCur
   # Bit 7:4 - CLKGCDRIntCurWhenLocked[3:0] - CDR's Alexander phase detector integral current path when in locked state [0 : 5.46 : 82] uA; default: 5
   # Bit 3:0 - CLKGCDRIntCur[3:0] - CDR's Alexander phase detector integral integral current path when in locking state [0 : 5.46 : 82] uA; default: 5
   write_blow_and_check_fuse(0x026, 0x55)


   # [0x039] LDConfigH
   # Line driver configuration register
   # Bit 7 - LDEmphasisEnable - Enable pre-emphasis in the line driver. The amplitude of the pre-emphasis is controlled by LDEmphasisAmp[6:0] and the duration by LDEmphasisShort.
   # Bit 6:0 - LDModulationCurrent[6:0] - Sets high-speed line driver modulation current: Im = 137 uA * LDModulationCurrent[6:0]
   write_blow_and_check_fuse(0x039, 0x20)


def write_fuse_magic(self, fuse_enable):
    value = 0
    if (fuse_enable):
        value = 0xA3
    # Load a magic number 0xA3 to the REG_FUSEMAGIC register to unlock fuse blowing.
    # [0x110] FuseMagic [7:0]
    writeReg(0x110, value)  # wr






















