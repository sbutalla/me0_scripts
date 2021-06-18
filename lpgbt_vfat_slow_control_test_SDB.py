from rw_reg_lpgbt import *
from time import sleep, time
import sys
import argparse
import random

# VFAT number: boss/sub, ohid, gbtid, elink 
# For GE2/1 GEB + Pizza
VFAT_TO_ELINK_GE21 = {
        0  : ("sub"  , 0, 1, 6),
        1  : ("sub"  , 0, 1, 24),
        2  : ("sub"  , 0, 1, 11),
        3  : ("boss" , 0, 0, 3),
        4  : ("boss" , 0, 0, 27),
        5  : ("boss" , 0, 0, 25),
        6  : ("boss" , 1, 0, 6),
        7  : ("boss" , 1, 0, 16),
        8  : ("sub"  , 1, 1, 18),
        9  : ("boss" , 1, 0, 15),
        10 : ("sub"  , 1, 1, 3),
        11 : ("sub"  , 1, 1, 17)
}

# For ME0 GEB
VFAT_TO_ELINK_ME0 = {
        0  : ("sub"  , 0, 1, 6),
        1  : ("sub"  , 0, 1, 24),
        2  : ("sub"  , 0, 1, 11),
        3  : ("boss" , 0, 0, 3),
        4  : ("boss" , 0, 0, 27),
        5  : ("boss" , 0, 0, 25),
        6  : ("sub"  , 1, 1, 6),
        7  : ("sub"  , 1, 1, 24),
        8  : ("sub"  , 1, 1, 11),
        9  : ("boss" , 1, 0, 3),
        10  : ("boss" , 1, 0, 27),
        11  : ("boss" , 1, 0, 25),
}

VFAT_TO_ELINK = VFAT_TO_ELINK_ME0

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
    gbtid = VFAT_TO_ELINK[vfat][2]
    elink = VFAT_TO_ELINK[vfat][3]
    return lpgbt, ohid, gbtid, elink
        
def lpgbt_vfat_bert(system, vfat_list, reg_list, niter, runtime, verbose, fileName):
    outputFile = fileName + ".txt"

    file_out = open(outputFile, "w")
    if niter!=0:
        print ("LPGBT VFAT Bit Error Ratio Test with %d transactions\n" % (niter))
        file_out.write("LPGBT VFAT Bit Error Ratio Test with %d transactions\n\n" % (niter))
    elif runtime!=0:
        print ("LPGBT VFAT Bit Error Ratio Test for %.2f minutes\n" % (runtime))
        file_out.write("LPGBT VFAT Bit Error Ratio Test for %.2f minutes\n\n" % (runtime))
    errors = {}
    error_rates = {}
    bus_errors = {}

    vfat_oh_link_reset()
    sleep(0.1)

    link_good_node = {}
    sync_error_node = {}
    reg_node = {}
    sc_transactions_node = get_rwreg_node("GEM_AMC.SLOW_CONTROL.VFAT3.TRANSACTION_CNT")
    sc_crc_error_node = get_rwreg_node("GEM_AMC.SLOW_CONTROL.VFAT3.CRC_ERROR_CNT")
    sc_timeout_error_node = get_rwreg_node("GEM_AMC.SLOW_CONTROL.VFAT3.TIMEOUT_ERROR_CNT")
    initial_sc_transaction_count = read_backend_reg(sc_transactions_node)
    initial_sc_crc_error_count = read_backend_reg(sc_crc_error_node)
    initial_sc_timeout_error_count = read_backend_reg(sc_timeout_error_node)
    total_sc_transactions_alt = {}

    # Check ready and get nodes
    for vfat in vfat_list:
        lpgbt, oh_select, gbt_select, elink = vfat_to_oh_gbt_elink(vfat)
        check_lpgbt_link_ready(oh_select, gbt_select)

        link_good_node[vfat] = get_rwreg_node("GEM_AMC.OH_LINKS.OH%d.VFAT%d.LINK_GOOD" % (oh_select, vfat-6*oh_select))
        sync_error_node[vfat] = get_rwreg_node("GEM_AMC.OH_LINKS.OH%d.VFAT%d.SYNC_ERR_CNT" % (oh_select, vfat-6*oh_select))
        link_good = read_backend_reg(link_good_node[vfat])
        sync_err = read_backend_reg(sync_error_node[vfat])
        if system!="dryrun" and (link_good == 0 or sync_err > 0):
            print (Colors.RED + "Link is bad for VFAT# %02d"%(vfat) + Colors.ENDC)
            rw_terminate()

        reg_node[vfat] = {}
        for reg in reg_list:
            reg_node[vfat][reg] = get_rwreg_node("GEM_AMC.OH.OH%d.GEB.VFAT%d.%s" % (oh_select, vfat-6*oh_select, reg))

    # Loop over registers
    for reg in reg_list:
        print ("Using register: " + reg)
        file_out.write("Using register: \n" + reg)
        write_perm = 0
        if vfat_registers[reg] == "r":
            print ("Operation: READ Only\n")
            file_out.write("Operation: READ Only\n\n")
            if niter!=0:
                print ("Testing VFATs with %d transactions (read): "%(niter))
                file_out.write("Testing VFATs with %d transactions (read): \n"%(niter))
            elif runtime!=0:
                print ("Testing VFATs for %.2f minutes (read): "%(runtime))
                file_out.write("Testing VFATs for %.2f minutes (read): \n"%(runtime))
        elif vfat_registers[reg] == "rw":
            print ("Operation: READ & WRITE\n")
            file_out.write("Operation: READ & WRITE\n\n")
            if niter!=0:
                print ("Testing VFATs with %d transactions (read+write): "%(niter))
                file_out.write("Testing VFATs with %d transactions (read+write): \n"%(niter))
            elif runtime!=0:
                print ("Testing VFATs for %.2f minutes (read+write): "%(runtime))
                file_out.write("Testing VFATs for %.2f minutes (read+write): \n"%(runtime))
            write_perm = 1
        print (vfat_list)
        for vfat in vfat_list:
            file_out.write(str(vfat) + "  ")
        file_out.write("\n")
        print ("")
        file_out.write("\n")

        total_sc_transactions_alt[reg] = 0
        errors[reg] = 12*[0]
        error_rates[reg] = 12*[0]
        bus_errors[reg] = 12*[0]
        t0 = time()
        t00 = t0
        n=0
        continue_iteration = 1

        # Nr. of iterations
        while continue_iteration:
            if write_perm:
                data_write = random.randint(0, (2**32 - 1)) # random number to write (32 bit)

            # Loop over VFATs
            for vfat in vfat_list:
                # Writing to the register
                if write_perm:
                    data_write_output = simple_write_backend_reg(reg_node[vfat][reg], data_write, -9999)
                    total_sc_transactions_alt[reg] += 1
                    if data_write_output == -9999:
                        bus_errors[reg][vfat] += 1
                    if verbose:
                        print ("Register value written to VFAT# %02d: "%(vfat) + hex(data_write))
                        file_out.write("Register value written to VFAT# %02d: "%(vfat) + hex(data_write) + "\n")
                
                # Reading the register
                data_read = simple_read_backend_reg(reg_node[vfat][reg], -9999)
                total_sc_transactions_alt[reg] += 1
                if data_read == -9999:
                    bus_errors[reg][vfat] += 1
                if write_perm:
                    if verbose:
                        if data_read == data_write:
                            print (Colors.GREEN + "Register value after writing for VFAT# %02d: "%(vfat) + hex(data_read) + "\n" + Colors.ENDC)
                            file_out.write("Register value after writing for VFAT# %02d: "%(vfat) + hex(data_read) + "\n\n")
                        else:
                            print (Colors.RED + "Register value after writing for VFAT# %02d: "%(vfat) + hex(data_read) + "\n" + Colors.ENDC)
                            file_out.write("Register value after writing for VFAT# %02d: "%(vfat) + hex(data_read) + "\n\n")
                else:
                    print ("Register value read for VFAT# %02d: "%(vfat) + hex(data_read))
                    file_out.write("Register value read for VFAT# %02d: "%(vfat) + hex(data_read) + "\n")

                if write_perm and data_read!=data_write:
                    errors[reg][vfat] += 1
            if not write_perm:
                print ("")
                file_out.write("\n")

            # Print % completed every 1 minute
            if (time()-t0)>60:
                if niter!=0:
                    per_completed = "{:.4f}".format(100 * float(n)/float(niter))
                elif runtime!=0:
                    per_completed = "{:.4f}".format(100 * float(time()-t00)/float(runtime*60))
                time_elapsed_min = "{:.2f}".format(float(time()-t00)/60.00) # in minutes
                print ("\nIteration completed: " + per_completed + "% , Time elapsed: " + time_elapsed_min + " (min)")
                file_out.write("\nIteration completed: " + per_completed + "% , Time elapsed: " + time_elapsed_min + " (min)\n")
                t0 = time()

            n+=1
            continue_iteration = (n<niter) or ((time()-t00)<(runtime*60.0))

        if niter==0:
            niter = n
        time_taken = (time() - t00)/60.00 # in minutes
        if write_perm:
            for vfat in vfat_list:
                print ("VFAT#: %02d, number of transactions: %.2e, number of mismatch errors: %d \n" %(vfat, niter, errors[reg][vfat]))
                file_out.write("VFAT#: %02d, number of transactions: %.2e, number of mismatch errors: %d \n\n" %(vfat, niter, errors[reg][vfat]))
                error_rates[reg][vfat] = float(errors[reg][vfat])/float(niter)
            print ("%.2e Operations (read+write) for register %s completed, Time taken: %.2f minutes \n" % (niter, reg, time_taken))
            file_out.write("%.2e Operations (read+write) for register %s completed, Time taken: %.2f minutes \n\n" % (niter, reg, time_taken))
        else:
            print ("")
            file_out.write("\n")
            print ("%.2e Operations (read) for register %s completed, Time taken: %.2f minutes \n" % (niter, reg, time_taken))
            file_out.write("%.2e Operations (read) for register %s completed, Time taken: %.2f minutes \n\n" % (niter, reg, time_taken))

    final_sc_transaction_count = read_backend_reg(sc_transactions_node)
    final_sc_crc_error_count = read_backend_reg(sc_crc_error_node)
    final_sc_timeout_error_count = read_backend_reg(sc_timeout_error_node)
    total_sc_transactions = final_sc_transaction_count - initial_sc_transaction_count
    total_sc_crc_errors = final_sc_crc_error_count - initial_sc_crc_error_count
    total_sc_timeout_errors = final_sc_crc_error_count - initial_sc_timeout_error_count
    daq_downlink_data_packet_size = 904 # 113*8 bits
    daq_uplink_data_packet_size = 840 # 105*8 bits

    total_transaction_index = 0
    for reg in reg_list:
        if vfat_registers[reg] == "rw":
            total_transaction_index += 2
        else:
            total_transaction_index += 1

    for reg in reg_list:
        print ("Error test results for register: " + reg)
        file_out.write("Error test results for register: " + reg + "\n")
        weight = 0
        if vfat_registers[reg] == "rw":
            print ("Nr. of transactions (read+write): %.2e\n"%(niter))
            file_out.write("Nr. of transactions (read+write): %.2e\n\n"%(niter))
            weight = 2.0/total_transaction_index
        else:
            print ("Nr. of transactions (read): %.2e\n"%(niter))
            file_out.write("Nr. of transactions (read): %.2e\n\n"%(niter))
            weight = 1.0/total_transaction_index

        total_sc_transactions = total_sc_transactions_alt[reg] # since TRANSACTION_CNT is a 16-bit rolling register
        #sc_transactions_per_vfat_per_reg = (float(total_sc_transactions)/len(vfat_list)) * weight # only required when using the TRANSACTION_CNT register
        sc_transactions_per_vfat_per_reg = (float(total_sc_transactions)/len(vfat_list)) # when using the alternate counter
        sc_crc_errors_per_vfat_per_reg = (float(total_sc_crc_errors)/len(vfat_list)) * weight
        sc_crc_error_ratio = sc_crc_errors_per_vfat_per_reg / (sc_transactions_per_vfat_per_reg * daq_uplink_data_packet_size)
        sc_crc_error_ratio_ul = 1.0 / (sc_transactions_per_vfat_per_reg * daq_uplink_data_packet_size)
        sc_timeout_errors_per_vfat_per_reg = (float(total_sc_timeout_errors)/len(vfat_list)) * weight
        sc_timeout_error_ratio = sc_timeout_errors_per_vfat_per_reg / (sc_transactions_per_vfat_per_reg * daq_downlink_data_packet_size)
        sc_timeout_error_ratio_ul = 1.0 / (sc_transactions_per_vfat_per_reg * daq_downlink_data_packet_size)

        for vfat in vfat_list:
            link_good = read_backend_reg(link_good_node[vfat])
            sync_err = read_backend_reg(sync_error_node[vfat])
            if link_good == 1:
                print (Colors.GREEN + "VFAT#: %02d, link is GOOD"%(vfat) + Colors.ENDC)
                file_out.write("VFAT#: %02d, link is GOOD\n"%(vfat))
            else:
                print (Colors.RED + "VFAT#: %02d, link is BAD"%(vfat) + Colors.ENDC)
                file_out.write("VFAT#: %02d, link is BAD\n"%(vfat))
            if sync_err==0:
                print (Colors.GREEN + "VFAT#: %02d, nr. of sync errors: %d"%(vfat, sync_err) + Colors.ENDC)
                file_out.write("VFAT#: %02d, nr. of sync errors: %d\n"%(vfat, sync_err))
            else:
                print (Colors.RED + "VFAT#: %02d, nr. of sync errors: %d"%(vfat, sync_err) + Colors.ENDC)
                file_out.write("VFAT#: %02d, nr. of sync errors: %d\n"%(vfat, sync_err))

            n_sc_opr = 0
            if vfat_registers[reg] == "rw":
                n_sc_opr = niter*2;
            else:
                n_sc_opr = niter;
            n_bus_error = bus_errors[reg][vfat]
            n_bus_error_ratio = float(n_bus_error)/n_sc_opr
            n_bus_error_ratio_ul = 1.0/n_sc_opr

            if n_bus_error == 0:
                print (Colors.GREEN + "VFAT#: %02d, nr. of bus errors: %d, bus error ratio < %s"%(vfat, n_bus_error, "{:.2e}".format(n_bus_error_ratio_ul)) + Colors.ENDC)
                file_out.write("VFAT#: %02d, nr. of bus errors: %d, bus error ratio < %s"%(vfat, n_bus_error, "{:.2e}\n".format(n_bus_error_ratio_ul)))
            else:
                print (Colors.YELLOW + "VFAT#: %02d, nr. of bus errors: %d, bus error ratio: %s"%(vfat, n_bus_error, "{:.2e}".format(n_bus_error_ratio)) + Colors.ENDC)
                file_out.write("VFAT#: %02d, nr. of bus errors: %d, bus error ratio: %s"%(vfat, n_bus_error, "{:.2e}\n".format(n_bus_error_ratio)))

            if vfat_registers[reg] == "rw":
                result_string = ""
                result_write_string = ""
                error_rate_ul = 1.0/niter
                if error_rates[reg][vfat]==0:
                    result_string += Colors.GREEN
                    result_string += "VFAT#: %02d, nr. of register mismatch errors: %d, mismatch error ratio < %s" %(vfat, errors[reg][vfat],  "{:.2e}".format(error_rate_ul))
                    result_write_string += "VFAT#: %02d, nr. of register mismatch errors: %d, mismatch error ratio < %s" %(vfat, errors[reg][vfat],  "{:.2e}".format(error_rate_ul))
                else:
                    result_string += Colors.YELLOW
                    result_string += "VFAT#: %02d, nr. of register mismatch errors: %d, mismatch error ratio: %s" %(vfat, errors[reg][vfat],  "{:.2e}".format(error_rates[reg][vfat]))
                    result_write_string += "VFAT#: %02d, nr. of register mismatch errors: %d, mismatch error ratio: %s" %(vfat, errors[reg][vfat],  "{:.2e}".format(error_rates[reg][vfat]))
                result_string += Colors.ENDC
                print (result_string)
                file_out.write(result_write_string + "\n")

            if sc_crc_errors_per_vfat_per_reg == 0:
                print (Colors.GREEN + "VFAT#: %02d, nr. of CRC errors in slow control: %d, Bit Error Ratio (BER) for Uplink < %.2e"%(vfat, sc_crc_errors_per_vfat_per_reg, sc_crc_error_ratio_ul) + Colors.ENDC)
                file_out.write("VFAT#: %02d, nr. of CRC errors in slow control: %d, Bit Error Ratio (BER) for Uplink < %.2e\n"%(vfat, sc_crc_errors_per_vfat_per_reg, sc_crc_error_ratio_ul))
            else:
                print (Colors.YELLOW + "VFAT#: %02d, nr. of CRC errors in slow control: %d, Bit Error Ratio (BER) for Uplink: %.2e"%(vfat, sc_crc_errors_per_vfat_per_reg, sc_crc_error_ratio) + Colors.ENDC)
                file_out.write("VFAT#: %02d, nr. of CRC errors in slow control: %d, Bit Error Ratio (BER) for Uplink: %.2e\n"%(vfat, sc_crc_errors_per_vfat_per_reg, sc_crc_error_ratio))
            if sc_timeout_errors_per_vfat_per_reg == 0:
                print (Colors.GREEN + "VFAT#: %02d, nr. of Timeout errors in slow control: %d, Bit Error Ratio (BER) for Downlink < %.2e"%(vfat, sc_timeout_errors_per_vfat_per_reg, sc_timeout_error_ratio_ul) + Colors.ENDC)
                file_out.write("VFAT#: %02d, nr. of Timeout errors in slow control: %d, Bit Error Ratio (BER) for Downlink < %.2e\n"%(vfat, sc_timeout_errors_per_vfat_per_reg, sc_timeout_error_ratio_ul))
            else:
                print (Colors.YELLOW + "VFAT#: %02d, nr. of Timeout errors in slow control: %d, Bit Error Ratio (BER) for Downlink: %.2e"%(vfat, sc_timeout_errors_per_vfat_per_reg, sc_timeout_error_ratio) + Colors.ENDC)
                file_out.write("VFAT#: %02d, nr. of Timeout errors in slow control: %d, Bit Error Ratio (BER) for Downlink: %.2e\n"%(vfat, sc_timeout_errors_per_vfat_per_reg, sc_timeout_error_ratio))
            print ("")
            file_out.write("\n")
        print ("")
        file_out.write("\n")
    file_out.close()
if __name__ == '__main__':

    # Parsing arguments
    parser = argparse.ArgumentParser(description='LpGBT VFAT Slow Control Error Ratio Test')
    parser.add_argument("-s", "--system", action="store", dest="system", help="system = backend or dryrun")
    #parser.add_argument("-l", "--lpgbt", action="store", dest="lpgbt", help="lpgbt = boss or sub")
    parser.add_argument("-v", "--vfats", action="store", dest="vfats", nargs='+', help="vfats = list of VFATs (0-11)")
    #parser.add_argument("-o", "--ohid", action="store", dest="ohid", help="ohid = 0-7 (only needed for backend)")
    #parser.add_argument("-g", "--gbtid", action="store", dest="gbtid", help="gbtid = 0, 1 (only needed for backend)")
    parser.add_argument("-r", "--reg", action="store", dest="reg", nargs='+', help="reg = register names to read/write: HW_ID (read), HW_ID_VER (read), TEST_REG (read/write), HW_CHIP_ID (read)")
    parser.add_argument("-n", "--niter", action="store", dest="niter", help="niter = number of times to perform the read/write")
    parser.add_argument("-t", "--runtime", action="store", dest="runtime", help="runtime = time (in minutes) to perform the read/write")
    parser.add_argument("-a", "--addr", action="store_true", dest="addr", help="if plugin card addressing needs should be enabled")
    parser.add_argument("-z", "--verbose", action="store_true", dest="verbose", default=False, help="Set for more verbosity")
    parser.add_argument("-f", "--fileName", action="store", dest="fileName", default="vfat_slow_control_test_output", help="Specify output file name (default: vfat_slow_control_test_output.txt")
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

    niter = 0
    runtime = 0
    if args.niter is None and args.runtime is None:
        niter = 1
    elif args.niter is not None and args.runtime is not None:
        print (Colors.YELLOW + "Only enter either nr. of iterations or run time" + Colors.ENDC)
        sys.exit()
    elif args.niter is None and args.runtime is not None:
        runtime = float(args.runtime)
    elif args.niter is not None and args.runtime is None:
        niter = int(args.niter)

    if args.addr:
        print ("Enabling VFAT addressing for plugin cards")
        write_backend_reg(get_rwreg_node("GEM_AMC.GEM_SYSTEM.VFAT3.USE_VFAT_ADDRESSING"), 1)
        
    # Parsing Registers XML File
    print("Parsing xml file...")
    parseXML()
    print("Parsing complete...")

    # Initialization (for CHeeseCake: reset and config_select)
    rw_initialize(args.system)
    print("Initialization Done\n")
    
    # Running Phase Scan
    try:
        lpgbt_vfat_bert(args.system, vfat_list, args.reg, niter, runtime, args.verbose, args.file)
    except KeyboardInterrupt:
        print (Colors.RED + "Keyboard Interrupt encountered" + Colors.ENDC)
        rw_terminate()
    except EOFError:
        print (Colors.RED + "\nEOF Error" + Colors.ENDC)
        rw_terminate()

    # Termination
    rw_terminate()




