from rw_reg_lpgbt import *
from time import sleep, time
import sys
import argparse
import random

# VFAT number: boss/sub, ohid, gbtid, elink 
# For GE2/1 GEB + Pizza
VFAT_TO_ELINK = {
        0  : ("sub"  , 0, 1, 6),
        1  : ("sub"  , 0, 1, 24),
        2  : ("sub"  , 0, 1, 11),
        3  : ("boss" , 0, 0, 3),
        4  : ("boss" , 0, 0, 27),
        5  : ("boss" , 0, 0, 25),
        6  : ("boss" , 1, 0, 6), # 3
        7  : ("boss" , 1, 0, 25), # 25
        8  : ("sub"  , 1, 1, 24), # 24
        9  : ("boss" , 1, 0, 27), # 27
        10 : ("sub"  , 1, 1, 6), # 6
        11 : ("sub"  , 1, 1, 27) # 11
}

# For ME0 GEB
#VFAT_TO_ELINK = {
#        0  : ("boss" , 0, 0, 6),
#        1  : ("sub"  , 0, 1, 24),
#        2  : ("boss" , 0, 0, 11),
#        3  : ("boss" , 0, 0, 3),
#        4  : ("sub"  , 0, 1, 27),
#        5  : ("sub"  , 0, 1, 25),
#        6  : ("boss" , 1, 0, 6), # 3
#        7  : ("sub"  , 1, 1, 24), # 25
#        8  : ("boss" , 1, 0, 27), # 24
#        9  : ("boss" , 1, 0, 6), # 27
#        10 : ("sub"  , 1, 1, 27), # 6
#        11 : ("sub"  , 1, 1, 25) # 11
#}

# Register to read/write
vfat_registers = {
        "HW_ID": "r",
        "HW_ID_VER": "r",
        "TEST_REG": "rw",
        "HW_CHIP_ID": "r"
}

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
            n=0
            while n < niter:
            
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
                data_write = random.randint(0, (2**32 - 1)) # random number to write (32 bit)
                write_backend_reg(node, data_write)
                if verbose:
                    print ("Register value written: " + hex(data_write))
                
                # Reading the register after writing
                data_read_after = read_backend_reg(node)
                if verbose:
                    print ("Register value after writing: " + hex(data_read_after) + "\n")
                    
                if data_read_after!=data_write:
                    errors[reg][vfat] += 1
                    
                # Print % completed every 10 seconds
                if (time()-t0)>10: 
                    per_completed = "{:.2f}".format(100 * float(n)/float(niter))
                    print ("\nIteration completed: " + per_completed + "% \n")
                    t0 = time()
                n+=1
           
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
                result_string = ""
                if error_rates[reg][vfat]==0:
                    result_string += Colors.GREEN
                else:
                    result_string += Colors.YELLOW
                result_string += "VFAT#: %02d, fraction of errors: %s" %(vfat, "{:.4f}".format(error_rates[reg][vfat]))
                result_string += Colors.ENDC
                print (result_string)
            print ("") 

if __name__ == '__main__':

    # Parsing arguments
    parser = argparse.ArgumentParser(description='LpGBT VFAT Error Rate Test')
    parser.add_argument("-s", "--system", action="store", dest="system", help="system = backend or dryrun")
    #parser.add_argument("-l", "--lpgbt", action="store", dest="lpgbt", help="lpgbt = boss or sub")
    parser.add_argument("-v", "--vfats", action="store", dest="vfats", nargs='+', help="vfats = list of VFATs (0-11)")
    #parser.add_argument("-o", "--ohid", action="store", dest="ohid", help="ohid = 0-7 (only needed for backend)")
    #parser.add_argument("-g", "--gbtid", action="store", dest="gbtid", help="gbtid = 0, 1 (only needed for backend)")
    parser.add_argument("-r", "--reg", action="store", dest="reg", nargs='+', help="reg = register names to read/write: HW_ID (read), HW_ID_VER (read), TEST_REG (read/write), HW_CHIP_ID (read)")
    parser.add_argument("-n", "--niter", action="store", dest="niter", default="1", help="niter = number of times to perform the read/write")
    parser.add_argument("-z", "--verbose", action="store_true", dest="verbose", default=False, help="Set for more verbosity")
    args = parser.parse_args()

    if args.system == "chc":
        #print ("Using Rpi CHeeseCake for configuration")
        print (Colors.YELLOW + "Only Backend or dryrun supported" + Colors.ENDC)
        sys.exit()
    elif args.system == "backend":
        print ("Using Backend for configuration")
        #print ("Only chc (Rpi Cheesecake) or dryrun supported at the moment")
        #sys.exit()
    elif args.system == "dongle":
        #print ("Using USB Dongle for configuration")
        print (Colors.YELLOW + "Only Backend or dryrun supported" + Colors.ENDC)
        sys.exit()
    elif args.system == "dryrun":
        print ("Dry Run - not actually running vfat bert")
    else:
        print (Colors.YELLOW + "Only valid options: backend, dryrun" + Colors.ENDC)
        sys.exit()

    if args.vfats is None:
        print (Colors.YELLOW + "Enter VFAT numbers" + Colors.ENDC)
        sys.exit()
    vfat_list = []
    for v in args.vfats:
        v_int = int(v)
        if v_int not in range(0,12):
            print (Colors.YELLOW + "Invalid VFAT number, only allowed 0-11" + Colors.ENDC)
            sys.exit()
        vfat_list.append(v_int)

    if args.reg is None:
        print ("Enter list of registers to read/write on VFAT")
        sys.exit()
    else:
        for r in args.reg:
            if r not in vfat_registers:
                print (Colors.YELLOW + "Only valid options: HW_ID (read), HW_ID_VER (read), TEST_REG (read/write), HW_CHIP_ID (read)" + Colors.ENDC)  
                sys.exit()  
       
    # Parsing Registers XML File
    print("Parsing xml file...")
    parseXML()
    print("Parsing complete...")

    # Initialization (for CHeeseCake: reset and config_select)
    rw_initialize(args.system)
    print("Initialization Done\n")
    
    # Running Phase Scan
    try:
        lpgbt_vfat_bert(args.system, vfat_list, args.reg, int(args.niter), args.verbose)
    except KeyboardInterrupt:
        print (Colors.RED + "Keyboard Interrupt encountered" + Colors.ENDC)
        rw_terminate()
    except EOFError:
        print (Colors.RED + "\nEOF Error" + Colors.ENDC)
        rw_terminate()

    # Termination
    rw_terminate()




