from rw_reg_lpgbt import *
from time import sleep, time
import sys
import argparse
import random

# VFAT number: boss/sub, ohid, gbtid, elink 
# For GE2/1 GEB + Pizza
VFAT_TO_ELINK = {
        0  : ("sub"  , 1, 1, 6),
        1  : ("sub"  , 1, 1, 24),
        2  : ("sub"  , 1, 1, 27),
        3  : ("boss" , 1, 0, 6),
        4  : ("boss" , 1, 0, 27),
        5  : ("boss" , 1, 0, 25),
        6  : ("boss" , 0, 0, 6),
        7  : ("boss" , 0, 0, 25),
        8  : ("sub"  , 0, 1, 24),
        9  : ("boss" , 0, 0, 27),
        10 : ("sub"  , 0, 1, 6),
        11 : ("sub"  , 0, 1, 27)
}

# For ME0 GEB
#VFAT_TO_ELINK = {
#        0  : ("boss" , 0, 0, 6),
#        1  : ("sub"  , 0, 1, 24),
#        2  : ("boss" , 0, 0, 27),
#        3  : ("boss" , 0, 0, 6),
#        4  : ("sub"  , 0, 1, 27),
#        5  : ("sub"  , 0, 1, 25),
#        6  : ("boss" , 0, 0, 6),
#        7  : ("sub"  , 0, 1, 24),
#        8  : ("boss" , 0, 0, 27),
#        9  : ("boss" , 0, 0, 6),
#        10 : ("sub"  , 0, 1, 27),
#        11 : ("sub"  , 0, 1, 25),
#}

# Register to read/write
vfat_registers = {
        "HW_ID": "r",
        "HW_ID_VER": "r",
        "TEST_REG": "rw",
        "HW_CHIP_ID": "r"
}

class Colors:
    WHITE   = '\033[97m'
    CYAN    = '\033[96m'
    MAGENTA = '\033[95m'
    BLUE    = '\033[94m'
    YELLOW  = '\033[93m'
    GREEN   = '\033[92m'
    RED     = '\033[91m'
    ENDC    = '\033[0m'

def vfat_to_oh_gbt_elink(vfat):
    lpgbt = VFAT_TO_ELINK[vfat][0]
    ohid  = VFAT_TO_ELINK[vfat][1]
    gbtid = VFAT_TO_ELINK[vfat][1]
    elink = VFAT_TO_ELINK[vfat][3]
    return lpgbt, ohid, gbtid, elink
        
def lpgbt_vfat_bert(system, vfat_list, reg_list, niter, verbose):
    print ("LPGBT VFAT Bit Error Rate Test with %s transactions\n" % (str(niter)))
    errors = {}
    error_rates = {}
    for reg in reg_list:
        print ("Using register: " + reg)
        write_perm = 0
        if vfat_registers[reg] == "r":
            print ("Operation: READ Only\n")
        elif vfat_registers[reg] == "rw":
            print ("Operation: READ & WRITE\n")
            write_perm = 1
            
        vfat_oh_link_reset()

        errors[reg] = 12*[0]
        error_rates[reg] = 12*[0]
        for vfat in vfat_list:
            lpgbt, oh_select, gbt_select, elink = vfat_to_oh_gbt_elink(vfat)
            print ("VFAT#: %02d" %(vfat))
            
            check_lpgbt_link_ready(oh_select, gbt_select)
            if system=="backend":
                node = rw_reg.getNode('GEM_AMC.OH.OH%d.GEB.VFAT%d.%s' % (oh_select, vfat-6*oh_select, reg))
            else:
                node = ""
            
            t0 = time()
            for n in range(niter):
            
                # Reading the register first
                data_read_before = read_backend_reg(node)
                if not write_perm:
                    print ("Register value: " + hex(data_read_before))
                else:
                    if verbose:
                        print ("Register value before writing: " + hex(data_read_before))
                
                if not write_perm:
                    continue
                
                # Writing to the register
                data_write = random.randint(0, 255) # random number to write (8 bit)
                write_backend_reg(node, data_write)
                if verbose:
                    print ("Register value written: " + hex(data_write))
                
                # Reading the register after writing
                data_read_after = read_backend_reg(node)
                if verbose:
                    print ("Register value after writing: " + hex(data_read_after))
                    
                if data_read_after!=data_write:
                    errors[reg][vfat] += 1
                    
                # Print % completed every 1 minute
                if (time()-t0)>60: 
                    per_completed = "{:.2f}".format(100 * float(n)/float(niter))
                    print ("\nIteration completed: " + per_completed + "% \n")
                    t0 = time()
           
            if write_perm:
                print ("VFAT#: %02d, number of transactions: %d, number of errors: %d \n" %(vfat, niter, errors[reg][vfat]))
            else:
                print ("")
            error_rates[reg][vfat] = float(errors[reg][vfat])/float(niter)
          
        print ("Operations for register %s completed \n" % (reg))      
    
    for reg in reg_list:
        if vfat_registers[reg] == "rw":     
            print ("Error fractions for register: " + reg)
            for vfat in vfat_list:
                print ("VFAT#: %02d, fraction of errors: %s" %(vfat, "{:.4f}".format(error_rates[reg][vfat])))
            print ("") 

if __name__ == '__main__':

    # Parsing arguments
    parser = argparse.ArgumentParser(description='LpGBT VFAT Error Rate Test')
    parser.add_argument("-s", "--system", action="store", dest="system", help="system = backend or dryrun")
    #parser.add_argument("-l", "--lpgbt", action="store", dest="lpgbt", help="lpgbt = boss or sub")
    parser.add_argument("-v", "--vfatmask", action="store", dest="vfatmask", help="vfatmask = in binary (0b) or hex (0x) format for 12 VFATs (on 1 ME0 GEB)")
    #parser.add_argument("-o", "--ohid", action="store", dest="ohid", help="ohid = 0-7 (only needed for backend)")
    #parser.add_argument("-g", "--gbtid", action="store", dest="gbtid", help="gbtid = 0, 1 (only needed for backend)")
    parser.add_argument("-r", "--reg", action="store", dest="reg", nargs='+', help="reg = register names to read/write: HW_ID (read), HW_ID_VER (read), TEST_REG (read/write), HW_CHIP_ID (read)")
    parser.add_argument("-n", "--niter", action="store", dest="niter", default="1", help="niter = number of times to perform the read/write")
    parser.add_argument("-z", "--verbose", action="store_true", dest="verbose", default=False, help="Set for more verbosity")
    args = parser.parse_args()

    if args.system == "chc":
        #print ("Using Rpi CHeeseCake for configuration")
        print ("Only Backend or dryrun supported")
        sys.exit()
    elif args.system == "backend":
        print ("Using Backend for configuration")
        #print ("Only chc (Rpi Cheesecake) or dryrun supported at the moment")
        #sys.exit()
    elif args.system == "dongle":
        #print ("Using USB Dongle for configuration")
        print ("Only Backend or dryrun supported")
        sys.exit()
    elif args.system == "dryrun":
        print ("Dry Run - not actually running vfat bert")
    else:
        print ("Only valid options: backend, dryrun")
        sys.exit()
    
    vfatmask_int = 0
    if args.vfatmask is None:
        print ("Enter a mask for the 12 VFATs")
        sys.exit()
    elif "0b" in args.vfatmask:
        vfatmask_int = int(args.vfatmask,2)
    elif "0x" in args.vfatmask:
        vfatmask_int = int(args.vfatmask,16)
    else:
        print ("Enter a mask in binary (0b) or hex (0x) format")
        sys.exit()
    if vfatmask_int>(2**12 - 1):
        print ("VFAT mask can be maximum 12 bits (for 12 VFATS on 1 ME0 GEB)")
        sys.exit()
    
    if args.reg is None:
        print ("Enter list of registers to read/write on VFAT")
        sys.exit()
    else:
        for r in args.reg:
            if r not in vfat_registers:
                print ("Only valid options: HW_ID (read), HW_ID_VER (read), TEST_REG (read/write), HW_CHIP_ID (read)")  
                sys.exit()  
       
    # Parsing Registers XML File
    print("Parsing xml file...")
    parseXML()
    print("Parsing complete...")

    # Initialization (for CHeeseCake: reset and config_select)
    rw_initialize(args.system)
    print("Initialization Done\n")
    
    # Construct a list of vfats to be scanned based on the mask
    vfat_list = []
    for vfat in range(0,12):
        if (0x1 & (vfatmask_int>>vfat)):
            vfat_list.append(vfat)
    
    # Running Phase Scan
    try:
        lpgbt_vfat_bert(args.system, vfat_list, args.reg, int(args.niter), args.verbose)
    except KeyboardInterrupt:
        print ("Keyboard Interrupt encountered")
        rw_terminate()
    except EOFError:
        print ("\nEOF Error")
        rw_terminate()

    # Termination
    rw_terminate()




