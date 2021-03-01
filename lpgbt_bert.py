from rw_reg_lpgbt import *
from time import sleep
import sys
import argparse

BERT_source_coarse ={}
BERT_source_coarse["DISABLED"] = 0x0 # Checker disabled
BERT_source_coarse["ULDG0"] = 0x1 # Uplink data group 0
BERT_source_coarse["ULDG1"] = 0x2 # Uplink data group 1
BERT_source_coarse["ULDG2"] = 0x3 # Uplink data group 2
BERT_source_coarse["ULDG3"] = 0x4 # Uplink data group 3
BERT_source_coarse["ULDG4"] = 0x5 # Uplink data group 4
BERT_source_coarse["ULDG5"] = 0x6 # Uplink data group 5
BERT_source_coarse["ULDG6"] = 0x7 # Uplink data group 6
BERT_source_coarse["ULEC"] = 0x8 # Uplink data group EC
BERT_source_coarse["DLDG0"] = 0x9 # Downlink data group 0
BERT_source_coarse["DLDG1"] = 0xa # Downlink data group 1
BERT_source_coarse["DLDG2"] = 0xb # Downlink data group 2
BERT_source_coarse["DLDG3"] = 0xc # Downlink data group 3
BERT_source_coarse["DLEC"] = 0xd # Downlink data group EC
BERT_source_coarse["DLFRAME"] = 0xe # Downlink deserializer frame

BERT_measure_time ={}
BERT_measure_time["BC_MT_2e5"] = 0x0
BERT_measure_time["BC_MT_2e7"] = 0x1
BERT_measure_time["BC_MT_2e9"] = 0x2
BERT_measure_time["BC_MT_2e11"] = 0x3
BERT_measure_time["BC_MT_2e13"] = 0x4
BERT_measure_time["BC_MT_2e15"] = 0x5
BERT_measure_time["BC_MT_2e17"] = 0x6
BERT_measure_time["BC_MT_2e19"] = 0x7
BERT_measure_time["BC_MT_2e21"] = 0x8
BERT_measure_time["BC_MT_2e23"] = 0x9
BERT_measure_time["BC_MT_2e25"] = 0xa
BERT_measure_time["BC_MT_2e27"] = 0xb
BERT_measure_time["BC_MT_2e29"] = 0xc
BERT_measure_time["BC_MT_2e31"] = 0xd
BERT_measure_time["BC_MT_2e33"] = 0xe
BERT_measure_time["BC_MT_2e35"] = 0xf

BERT_source_fine ={}
BERT_source_fine["UL_PRBS7_DR1_CHN0"] = 0x0 # Check PRBS7 sequence on channel 0 for data rate equal to 1
BERT_source_fine["UL_PRBS7_DR1_CHN1"] = 0x1 # Check PRBS7 sequence on channel 1 for data rate equal to 1
BERT_source_fine["UL_PRBS7_DR1_CHN2"] = 0x2 # Check PRBS7 sequence on channel 2 for data rate equal to 1
BERT_source_fine["UL_PRBS7_DR1_CHN3"] = 0x3 # Check PRBS7 sequence on channel 3 for data rate equal to 1
BERT_source_fine["UL_PRBS7_DR2_CHN0"] = 0x4 # Check PRBS7 sequence on channel 0 for data rate equal to 2
BERT_source_fine["UL_PRBS7_DR2_CHN2"] = 0x5 # Check PRBS7 sequence on channel 2 for data rate equal to 2
BERT_source_fine["UL_PRBS7_DR3_CHN0"] = 0x6 # Check PRBS7 sequence on channel 0 for data rate equal to 3
BERT_source_fine["UL_FIXED"] = 0x7 # Check the data against constant pattern

BERT_source_fine["DL_PRBS7_DR1_CHN0"] = 0x0 # Check PRBS7 sequence on channel 0 for data rate equal to 1
BERT_source_fine["DL_PRBS7_DR1_CHN1"] = 0x1 # Check PRBS7 sequence on channel 1 for data rate equal to 1
BERT_source_fine["DL_PRBS7_DR1_CHN2"] = 0x2 # Check PRBS7 sequence on channel 2 for data rate equal to 1
BERT_source_fine["DL_PRBS7_DR1_CHN3"] = 0x3 # Check PRBS7 sequence on channel 3 for data rate equal to 1
BERT_source_fine["DL_PRBS7_DR2_CHN0"] = 0x4 # Check PRBS7 sequence on channel 0 for data rate equal to 2
BERT_source_fine["DL_PRBS7_DR2_CHN2"] = 0x5 # Check PRBS7 sequence on channel 2 for data rate equal to 2
BERT_source_fine["DL_PRBS7_DR3_CHN0"] = 0x6 # Check PRBS7 sequence on channel 0 for data rate equal to 3
BERT_source_fine["DL_FIXED"] = 0x7 # Check the data against constant pattern

BERT_source_fine["ULEC"] = 0x0
BERT_source_fine["DLEC"] = 0x0

BERT_source_fine["DLDATA_PRBS"] = 0x0
BERT_source_fine["DLDATA_FIXED"] = 0x1 # Checks the group data in the downlink frame
BERT_source_fine["DLFRAME_PRBS7"] = 0x2 # PRBS7 (no header)
BERT_source_fine["DLFRAME_PRBS15"] = 0x3 # PRBS15 (no header)
BERT_source_fine["DLFRAME_PRBS23"] = 0x4 # PRBS23 (no header)
BERT_source_fine["DLFRAME_PRBS31"] = 0x5 # PRBS31 (no header)
BERT_source_fine["DLFRAME_FIXED"] = 0x7 # Check the data against constant pattern

def main(system, bert_source, time, boss):

    # Getting the register nodes
    bert_coarse_node = getNode("LPGBT.RW.BERT.COARSEBERTSOURCE")
    bert_fine_node = getNode("LPGBT.RW.BERT.FINEBERTSOURCE")
    bert_time_node = getNode("LPGBT.RW.BERT.BERTMEASTIME")
    bert_skipdisable_node = getNode("LPGBT.RW.BERT.SKIPDISABLE")
    bert_start_node = getNode("LPGBT.RW.BERT.BERTSTART")
    bert_done_node = getNode("LPGBT.RO.BERT.BERTDONE")
    bert_error_node = getNode("LPGBT.RO.BERT.BERTPRBSERRORFLAG")
    bert_result0_node = getNode("LPGBT.RO.BERT.BERTERRORCOUNT0")
    bert_result1_node = getNode("LPGBT.RO.BERT.BERTERRORCOUNT1")
    bert_result2_node = getNode("LPGBT.RO.BERT.BERTERRORCOUNT2")
    bert_result3_node = getNode("LPGBT.RO.BERT.BERTERRORCOUNT3")
    bert_result4_node = getNode("LPGBT.RO.BERT.BERTERRORCOUNT4")

    # Setting Measurement Time
    bert_time_setting = BERT_measure_time[time]
    n_clocks_exp = int(time.split("_2e")[1])
    n_clocks = 2**n_clocks_exp
    print ("Measurement time: " + time + " , setting: " + str(hex(bert_time_setting)) + " , number of clock cycles: 2^" + str(n_clocks_exp) + "\n")
    writeReg(bert_time_node, bert_time_setting, 0)

    # Looping over the coarse BERT sources
    for bert in bert_source:
        if bert == "DISABLED":
            print ("Skipping DISABLED Coarse BERT Source")
            continue

        bert_coarse_setting = BERT_source_coarse[bert]
        print ("BERT for Coarse BERT Source: " + bert + " , setting: " + str(hex(bert_coarse_setting)) + "\n")
        writeReg(bert_coarse_node, bert_coarse_setting, 0)

        bert_fine_list = []
        bert_skipdisable_setting = 0x0
        bits_per_clock_cycle = 0
        if "ULDG" in bert:
            bert_fine_list.append("UL_PRBS7_DR1_CHN0")
            bert_fine_list.append("UL_PRBS7_DR1_CHN1")
            bert_fine_list.append("UL_PRBS7_DR1_CHN2")
            bert_fine_list.append("UL_PRBS7_DR1_CHN3")
            bits_per_clock_cycle = 8 # Uplink contains 8 bits per clock cycle (320 Mbps)
        elif "DLDG" in bert:
            bert_fine_list.append("DL_PRBS7_DR3_CHN0")
            bits_per_clock_cycle = 8 # Downlink contains 8 bits per clock cycle (320 Mbps)
        elif "DLFRAME" in bert:
            bert_fine_list.append("DLFRAME_PRBS7")
            bert_skipdisable_setting = 0x1
            bits_per_clock_cycle = 64 # Downlink frame contains 64 bits per clock cycle (2.56 Gbps)
        elif "EC" in bert:
            bert_fine_list.append(bert)
            bits_per_clock_cycle = 2 # EC contains 2 bits per clock cycle (80 Mbps)
        else:
            continue

        bits_checked = n_clocks * bits_per_clock_cycle
        writeReg(bert_skipdisable_node, bert_skipdisable_setting, 0)
        #writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGDISABLEFRAMEALIGNERLOCKCONTROL") , 0x1, 0)
        #writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGLOCKFILTERENABLE"), 0x0, 0) # quickstart recommends 0
        #writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGWAITCDRTIME"), 0xa, 0)

        # Looping over the fine BERT sources
        for bert_fine in bert_fine_list:
            bert_fine_setting = BERT_source_fine[bert_fine]
            print ("BERT for Fine BERT Source: " + bert_fine + " , setting: " + str(hex(bert_fine_setting)))
            writeReg(bert_fine_node, bert_fine_setting, 0)

            # Start the measurement
            print ("Starting BERT")
            writeReg(bert_start_node, 0x1, 0)

            done = 0
            while (done==0):
                if system!="dryrun":
                    done = readReg(bert_done_node)
                else:
                    done = 1
                #print ("BERT done = %d" % done)
            err = readReg(bert_error_node)
            if (err):
                print ("ERROR: no data received")
                break

            # Read the BER result
            bert_result = 0
            bert_result |= readReg(bert_result0_node) << 0
            bert_result |= readReg(bert_result1_node) << 8
            bert_result |= readReg(bert_result2_node) << 16
            bert_result |= readReg(bert_result3_node) << 24
            bert_result |= readReg(bert_result4_node) << 32

            # Stop the measurement by deaserting the start bit
            print ("Stopping BERT")
            writeReg(bert_start_node, 0x0, 0)

            # Calculate Bit Error Rate
            ber = float(bert_result) / float(bits_checked)
            print ("Result for coarse BERT source: " + bert + " and fine BERT source: " + bert_fine)
            print ("BER = " + str(ber) + "\n")

        writeReg(bert_fine_node, 0x0, 0)
        writeReg(bert_coarse_node, 0x0, 0)

def check_rom_readback():
    romreg=readReg(getNode("LPGBT.RO.ROMREG"))
    if (romreg != 0xA5):
        print ("ERROR: no communication with LPGBT. ROMREG=0x%x, EXPECT=0x%x" % (romreg, 0xA5))
        rw_terminate()
    else:
        print ("Successfully read from ROM. I2C communication OK")

if __name__ == '__main__':
    # Parsing arguments
    parser = argparse.ArgumentParser(description='LPGBT Bit Error Rate Test (BERT)')
    parser.add_argument("-s", "--system", action="store", dest="system", help="system = chc or backend or dongle or dryrun")
    parser.add_argument("-l", "--lpgbt", action="store", dest="lpgbt", help="lpgbt = only boss allowed")
    parser.add_argument("-o", "--ohid", action="store", dest="ohid", help="ohid = 0-7 (only needed for backend)")
    parser.add_argument("-g", "--gbtid", action="store", dest="gbtid", help="gbtid = 0, 1 (only needed for backend)")
    parser.add_argument("-b", "--bert_source", action="store", nargs='+', dest="bert_source", help="COURSE BERT SOURCE = See lpGBT manual Table 14.4 for options")
    parser.add_argument("-t", "--time", action="store", dest="time", default="BC_MT_2e35", help="TIME = measurement time (See lpGBT manual Table 14.5 for options), default: BC_MT_2e35")
    args = parser.parse_args()

    if args.system == "chc":
        print ("Using Rpi CHeeseCake for checking configuration")
    elif args.system == "backend":
        #print ("Using Backend for checking configuration")
        print (Colors.YELLOW + "Only chc (Rpi Cheesecake) or dryrun supported at the moment" + Colors.ENDC)
        sys.exit()
    elif args.system == "dongle":
        #print ("Using USB Dongle for checking configuration")
        print (Colors.YELLOW + "Only chc (Rpi Cheesecake) or dryrun supported at the moment" + Colors.ENDC)
        sys.exit()
    elif args.system == "dryrun":
        print ("Dry Run - not actually running on lpGBT")
    else:
        print (Colors.YELLOW + "Only valid options: chc, backend, dongle, dryrun" + Colors.ENDC)
        sys.exit()

    boss = None
    if args.lpgbt is None:
        print (Colors.YELLOW + "Please select boss" + Colors.ENDC)
        sys.exit()
    elif (args.lpgbt=="boss"):
        print ("BER for boss LPGBT")
        boss=1
    elif (args.lpgbt=="sub"):
        print ("Only boss LPGBT allowed for BER")
        boss=0
    else:
        print (Colors.YELLOW + "Please select boss" + Colors.ENDC)
        sys.exit()
    if boss is None:
        sys.exit()

    if args.bert_source is None:
        print (Colors.YELLOW + "Need a BERT source" + Colors.ENDC)
        sys.exit()
        
    if args.system == "backend":
        if args.ohid is None:
            print (Colors.YELLOW + "Need OHID for backend" + Colors.ENDC)
            sys.exit()
        if args.gbtid is None:
            print (Colors.YELLOW + "Need GBTID for backend" + Colors.ENDC)
            sys.exit()
        if int(args.ohid)>7:
            print (Colors.YELLOW + "Only OHID 0-7 allowed" + Colors.ENDC)
            sys.exit()
        if int(args.gbtid)>1:
            print (Colors.YELLOW + "Only GBTID 0 and 1 allowed" + Colors.ENDC)
            sys.exit() 
    else:
        if args.ohid is not None or args.gbtid is not None:
            print (Colors.YELLOW + "OHID and GBTID only needed for backend" + Colors.ENDC)
            sys.exit()

    for bert in args.bert_source:
        if bert not in BERT_source_coarse:
            print (Colors.YELLOW + "Invalid course BERT source : " + bert + " (See lpGBT manual Table 14.4 for options)" + Colors.ENDC)
            sys.exit()

    if args.time not in BERT_measure_time:
        print (Colors.YELLOW + "Invalid BERT measurement time (See lpGBT manual Table 14.5 for options)" + Colors.ENDC)
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
        main(args.system, args.bert_source, args.time, boss)
    except KeyboardInterrupt:
        print (Colors.RED + "\nKeyboard Interrupt encountered" + Colors.ENDC)
        rw_terminate()
    except EOFError:
        print (Colors.RED + "\nEOF Error" + Colors.ENDC)
        rw_terminate()

    # Termination
    rw_terminate()
