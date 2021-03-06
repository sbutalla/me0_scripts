from rw_reg_lpgbt import *
from time import sleep, time
import sys
import argparse

config_boss_filename = "config_boss.txt"
config_sub_filename = "config_sub.txt"
config_boss = {}
config_sub = {}

# VFAT number: boss/sub, ohid, gbtid
# For GE2/1 GEB + Pizza
VFAT_TO_ELINK = {
        0  : ("sub"  , 0, 1),
        1  : ("sub"  , 0, 1),
        2  : ("sub"  , 0, 1),
        3  : ("boss" , 0, 0),
        4  : ("boss" , 0, 0),
        5  : ("boss" , 0, 0),
        6  : ("boss" , 1, 0),
        7  : ("boss" , 1, 0),
        8  : ("sub"  , 1, 1),
        9  : ("boss" , 1, 0),
        10 : ("sub"  , 1, 1),
        11 : ("sub"  , 1, 1)
}

# For ME0 GEB
#VFAT_TO_ELINK = {
#        0  : ("boss" , 0, 0),
#        1  : ("sub"  , 0, 1),
#        2  : ("boss" , 0, 0),
#        3  : ("boss" , 0, 0),
#        4  : ("sub"  , 0, 1),
#        5  : ("sub"  , 0, 1),
#        6  : ("boss" , 1, 0),
#        7  : ("sub"  , 1, 1),
#        8  : ("boss" , 1, 0),
#        9  : ("boss" , 1, 0),
#        10 : ("sub"  , 1, 1),
#        11 : ("sub"  , 1, 1)
#}

def getConfig (filename):
    f = open(filename, 'r')
    reg_map = {}
    for line in f.readlines():
        reg = int(line.split()[0], 16)
        data = int(line.split()[1], 16)
        reg_map[reg] = data
    f.close()
    return reg_map

def vfat_to_oh_gbt(vfat):
    lpgbt = VFAT_TO_ELINK[vfat][0]
    ohid  = VFAT_TO_ELINK[vfat][1]
    gbtid = VFAT_TO_ELINK[vfat][1]
    return lpgbt, ohid, gbtid

def lpgbt_elink_phase_scan(system, vfat_list, depth):
    print ("LPGBT Phase Scan depth=%s transactions" % (str(depth)))
    centers = [[0 for elink in range(28)] for vfat in range(12)]
    widths = [[0 for elink in range(28)] for vfat in range(12)]
    errs_list = [[[0 for phase in range(16)] for elink in range(28)] for vfat in range(12)]

    for vfat in vfat_list: # Loop over all vfats
        for elink in range(0,28): # Loop for all 28 RX elinks
            print ("VFAT%02d , ELINK %02d" % (vfat, elink))
            link_good = 16*[0]
            sync_err_cnt = 16*[0]
            cfg_run = 16*[0]
            errs = 16*[0]

            for phase in range(0, 16):
                # set phases for the vfat under test
                setVfatRxPhase(system, vfat, phase, elink)

                # Reset the link, give some time to accumulate any sync errors and then check VFAT comms
                sleep(0.1)
                vfat_oh_link_reset()
                sleep(0.001)

                # read cfg_run some number of times, check link good status and sync errors
                lpgbt, oh_select, gbt_select = vfat_to_oh_gbt(vfat)
            
                check_lpgbt_link_ready(oh_select, gbt_select)
                if system=="backend":
                    cfg_node = rw_reg.getNode('GEM_AMC.OH.OH%d.GEB.VFAT%d.CFG_RUN' % (oh_select, vfat-6*oh_select))
                else:
                    cfg_node = ""
                for iread in range(depth):
                    #vfat_cfg_run = read_backend_reg(cfg_node)
                    vfat_cfg_run = 0x00
                    if system=="backend":
                        output_cfg = rw_reg.readReg(cfg_node)
                    if output_cfg != "Bus Error":
                        vfat_cfg_run = int(output_cfg,16)
                    else:
                        vfat_cfg_run = 9999
                    cfg_run[phase] += (vfat_cfg_run != 0 and vfat_cfg_run != 1)
            
                if system=="backend":
                    link_node = rw_reg.getNode('GEM_AMC.OH_LINKS.OH%d.VFAT%d.LINK_GOOD' % (oh_select, vfat-6*oh_select))
                    sync_node = rw_reg.getNode('GEM_AMC.OH_LINKS.OH%d.VFAT%d.SYNC_ERR_CNT' % (oh_select, vfat-6*oh_select))
                else:
                    link_node = ""
                    sync_node = ""
                #link_good[vfat][phase]    = read_backend_reg(link_node)
                #sync_err_cnt[vfat][phase] = read_backend_reg(sync_node)
                link_good[phase] = 0x00
                sync_err_cnt[phase] = 0x00
                if system=="backend":
                    output_link_node = rw_reg.readReg(link_node)
                    if output_link_node != "Bus Error":
                        link_good[phase] = int(output_link_node,16)
                    else:
                        link_good[phase] = 0x00
                    output_sync_node = rw_reg.readReg(sync_node)
                    if output_sync_node != "Bus Error":
                        sync_err_cnt[phase] = int(output_sync_node,16)
                    else:
                        sync_err_cnt[phase] = 9999

            for phase in range(0, 16):
                errs[phase] = (not 1==link_good[phase]) + sync_err_cnt[phase] + cfg_run[phase]
                errs_list[vfat][elink][phase] = errs[phase]
            centers[vfat][elink], widths[vfat][elink] = find_phase_center(errs)

            setVfatRxPhase(system, vfat, 0, elink)

    sleep(0.1)
    vfat_oh_link_reset()

    for vfat in vfat_list:
        print ("")
        for elink in range(0,28):
            sys.stdout.write("VFAT%02d , ELINK %02d:" % (vfat, elink))
            for phase in range(0, 16):

                if (widths[vfat][elink]>0 and phase==centers[vfat][elink]):
                    char=Colors.GREEN + "+" + Colors.ENDC
                elif (errs_list[vfat][elink][phase]):
                    char=Colors.RED + "-" + Colors.ENDC
                else:
                    char = Colors.YELLOW + "x" + Colors.ENDC

                sys.stdout.write("%s" % char)
                sys.stdout.flush()
            sys.stdout.write(" (center=%d, width=%d)\n" % (centers[vfat][elink], widths[vfat][elink]))
            sys.stdout.flush()

def find_phase_center(err_list):
    # find the centers
    ngood        = 0
    ngood_max    = 0
    ngood_edge   = 0
    ngood_center = 0

    # duplicate the err_list to handle the wraparound
    err_list_doubled = err_list + err_list
    phase_max = len(err_list)-1

    for phase in range(0,len(err_list_doubled)):
        if (err_list_doubled[phase] == 0):
            ngood+=1
        else: # hit an edge
            if (ngood > 0 and ngood >= ngood_max):
                ngood_max  = ngood
                ngood_edge = phase
            ngood=0

    # cover the case when there are no edges, just pick the center
    if (ngood==len(err_list_doubled)):
        ngood_max  = ngood/2
        ngood_edge =len(err_list_doubled)-1

    if (ngood_max>0):
        ngood_width = ngood_max
        # even windows
        if (ngood_max % 2 == 0):
            ngood_center=ngood_edge-(ngood_max/2)-1;
            if (err_list_doubled[ngood_edge] > err_list_doubled[ngood_edge-ngood_max-1]):
                ngood_center=ngood_center
            else:
                ngood_center=ngood_center+1
        # oddwindows
        else:
            ngood_center=ngood_edge-(ngood_max/2)-1;

    ngood_center = ngood_center % phase_max - 1

    if (ngood_max==0):
        ngood_center=0

    return ngood_center, ngood_max

def setVfatRxPhase(system, vfat, phase, elink):

    lpgbt, oh_select, gbt_select = vfat_to_oh_gbt(vfat)

    if lpgbt == "boss":
        config = config_boss
    elif lpgbt == "sub":
        config = config_sub
    
    # set phase
    GBT_ELINK_SAMPLE_PHASE_BASE_REG = 0x0CC
    addr = GBT_ELINK_SAMPLE_PHASE_BASE_REG + elink
    value = (config[addr] & 0x0f) | (phase << 4)
    
    check_lpgbt_link_ready(oh_select, gbt_select)
    select_ic_link(oh_select, gbt_select)
    if system!= "dryrun" and system!= "backend":
        check_rom_readback()
    mpoke(addr, value)
    sleep(0.000001) # writing too fast for CVP13

if __name__ == '__main__':

    # Parsing arguments
    parser = argparse.ArgumentParser(description='LpGBT Elink and Phase Scan for each VFAT')
    parser.add_argument("-s", "--system", action="store", dest="system", help="system = backend or dryrun")
    #parser.add_argument("-l", "--lpgbt", action="store", dest="lpgbt", help="lpgbt = boss or sub")
    parser.add_argument("-v", "--vfats", action="store", dest="vfats", nargs='+', help="vfats = list of VFATs (0-11)")
    #parser.add_argument("-o", "--ohid", action="store", dest="ohid", help="ohid = 0-7 (only needed for backend)")
    #parser.add_argument("-g", "--gbtid", action="store", dest="gbtid", help="gbtid = 0, 1 (only needed for backend)")
    parser.add_argument("-d", "--depth", action="store", dest="depth", default="1000", help="depth = number of times to check for cfg_run error")
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
        print ("Dry Run - not actually running phase scan")
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

    # Parsing Registers XML File
    print("Parsing xml file...")
    parseXML()
    print("Parsing complete...")

    # Initialization (for CHeeseCake: reset and config_select)
    rw_initialize(args.system)
    print("Initialization Done\n")
    
    if not os.path.isfile(config_boss_filename):
        print (Colors.YELLOW + "Missing config file for boss: config_boss.txt" + Colors.ENDC)
        sys.exit()
    
    if not os.path.isfile(config_sub_filename):
        print (Colors.YELLOW + "Missing config file for sub: sub_boss.txt" + Colors.ENDC)
        sys.exit()

    config_boss = getConfig(config_boss_filename)
    config_sub  = getConfig(config_sub_filename)
    
    # Running Phase Scan
    try:
        lpgbt_elink_phase_scan(args.system, vfat_list, int(args.depth))
    except KeyboardInterrupt:
        print (Colors.RED + "Keyboard Interrupt encountered" + Colors.ENDC)
        rw_terminate()
    except EOFError:
        print (Colors.RED + "\nEOF Error" + Colors.ENDC)
        rw_terminate()

    # Termination
    rw_terminate()




