from rw_reg_lpgbt import *
from time import sleep, time
import sys
import argparse

def main(system, boss, type):

    if boss:
        print ("Reset boss lpGBT\n")
    else:
        print ("Reset sub lpGBT\n")

    if type=="pll_reset":
        if system=="backend":
            mpoke(0x12C, 0x80)
            sleep(2)
            mpoke(0x12C, 0x00)
        else:
            writeReg(getNode("LPGBT.RW.RESET.RSTPLLDIGITAL"), 0x01, 0)
            sleep(2)
            writeReg(getNode("LPGBT.RW.RESET.RSTPLLDIGITAL"), 0x00, 0)
    elif type=="full_reset":
        if system=="backend":
            mpoke(0x130, 0xA3)
            mpoke(0x12F, 0x80)
        else:
            writeReg(getNode("LPGBT.RW.POWERUP.PUSMFORCEMAGIC"), 0xA3, 0)
            writeReg(getNode("LPGBT.RW.POWERUP.PUSMFORCESTATE"), 0x01, 0)
            writeReg(getNode("LPGBT.RW.POWERUP.PUSMSTATEFORCED"), 0x00, 0)

    print ("Reset Done\n")
    
if __name__ == '__main__':

    # Parsing arguments
    parser = argparse.ArgumentParser(description='lpGBT Reset')
    parser.add_argument("-s", "--system", action="store", dest="system", help="system = chc or backend or dongle or dryrun")
    parser.add_argument("-l", "--lpgbt", action="store", dest="lpgbt", help="lpgbt = boss or sub")
    parser.add_argument("-o", "--ohid", action="store", dest="ohid", help="ohid = 0-7 (only needed for backend)")
    parser.add_argument("-g", "--gbtid", action="store", dest="gbtid", help="gbtid = 0, 1 (only needed for backend)")
    parser.add_argument("-t", "--type", action="store", dest="type", help="type = pll_reset or full_reset")
    args = parser.parse_args()

    if args.system == "chc":
        print ("Using Rpi CHeeseCake for reset")
    elif args.system == "backend":
        print ("Using Backend for reset")
    elif args.system == "dongle":
        #print ("Using USB Dongle for reset")
        print (Colors.YELLOW + "Only chc (Rpi Cheesecake) or dryrun supported at the moment" + Colors.ENDC)
        sys.exit()
    elif args.system == "dryrun":
        print ("Dry Run - not actually resetting lpGBT")
    else:
        print (Colors.YELLOW + "Only valid options: chc, backend, dongle, dryrun" + Colors.ENDC)
        sys.exit()

    boss = None
    if args.lpgbt is None:
        print (Colors.YELLOW + "Please select boss or sub" + Colors.ENDC)
        sys.exit()
    elif (args.lpgbt=="boss"):
        print ("Using boss LPGBT")
        boss=1
    elif (args.lpgbt=="sub"):
        print ("Using sub LPGBT")
        boss=0
    else:
        print (Colors.YELLOW + "Please select boss or sub" + Colors.ENDC)
        sys.exit()
    if boss is None:
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
    
    if args.type not in ["pll_reset", "full_reset"]:
        print (Colors.YELLOW + "Valid options for type = pll_reset, full_reset" + Colors.ENDC)
        sys.exit()

    # Parsing Registers XML File
    print("Parsing xml file...")
    parseXML()
    print("Parsing complete...")

    # Initialization (for CHeeseCake: reset and config_select)
    rw_initialize(args.system, boss, args.ohid, args.gbtid)
    print("Initialization Done\n")
    
    # Readback rom register to make sure communication is OK
    if args.system!="dryrun" and args.system!="backend":
        check_rom_readback()

    # Check if lpGBT is READY if running through backend
    #if args.system=="backend":
    #    check_lpgbt_link_ready(args.ohid, args.gbtid)

    # Configuring LPGBT
    try:
        main(args.system, boss, args.type)
    except KeyboardInterrupt:
        print (Colors.RED + "Keyboard Interrupt encountered" + Colors.ENDC)
        rw_terminate()
    except EOFError:
        print (Colors.RED + "\nEOF Error" + Colors.ENDC)
        rw_terminate()

    # Termination
    rw_terminate()
