from rw_reg_lpgbt import *
from time import sleep, time
import sys
import argparse

config_boss_filename = "config_boss.txt"
config_sub_filename = "config_sub.txt"
config_boss = {}
config_sub = {}

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


def getConfig (filename):
    f = open(filename, 'r')
    reg_map = {}
    for line in f.readlines():
        reg = int(line.split()[0], 16)
        data = int(line.split()[1], 16)
        reg_map[reg] = data
    f.close()
    return reg_map

def vfat_to_oh_gbt_elink(vfat):
    lpgbt = VFAT_TO_ELINK[vfat][0]
    ohid  = VFAT_TO_ELINK[vfat][1]
    gbtid = VFAT_TO_ELINK[vfat][1]
    elink = VFAT_TO_ELINK[vfat][3]
    return lpgbt, ohid, gbtid, elink
        
def lpgbt_communication_test(system, vfat_list, depth):
    print ("LPGBT VFAT Communication Check depth=%s transactions" % (str(depth)))
    
    vfat_oh_link_reset()
    cfg_run = 12*[0]
    for vfat in vfat_list:
        lpgbt, oh_select, gbt_select, elink = vfat_to_oh_gbt_elink(vfat)
           
        check_lpgbt_link_ready(oh_select, gbt_select)
        if system=="backend":
            cfg_node = rw_reg.getNode('GEM_AMC.OH.OH%d.GEB.VFAT%d.CFG_RUN' % (oh_select, vfat-6*oh_select))
        else:
            cfg_node = ""
        for iread in range(depth):
            vfat_cfg_run = read_backend_reg(cfg_node)
            cfg_run[vfat] += (vfat_cfg_run != 0)
        print ("VFAT#%02d: reads=%d, errs=%d" % (vfat, depth, cfg_run[vfat]))

def lpgbt_phase_scan(system, vfat_list, depth, best_phase):
    print ("LPGBT Phase Scan depth=%s transactions" % (str(depth)))

    link_good    = [[0 for phase in range(16)] for vfat in range(12)]
    sync_err_cnt = [[0 for phase in range(16)] for vfat in range(12)]
    cfg_run      = [[0 for phase in range(16)] for vfat in range(12)]
    errs         = [[0 for phase in range(16)] for vfat in range(12)]

    for phase in range(0, 16):
        print('Scanning phase %d' % phase)

        # set phases for all vfats under test
        for vfat in vfat_list:
            setVfatRxPhase(system, vfat, phase)

        sleep(0.01)

        # reset the link, give some time to lock and accumulate any sync errors and then check VFAT comms
        vfat_oh_link_reset()

        # read cfg_run some number of times, check link good status and sync errors
        for vfat in vfat_list:
            lpgbt, oh_select, gbt_select, elink = vfat_to_oh_gbt_elink(vfat)
            
            check_lpgbt_link_ready(oh_select, gbt_select)   
            if system=="backend":        
                cfg_node = rw_reg.getNode('GEM_AMC.OH.OH%d.GEB.VFAT%d.CFG_RUN' % (oh_select, vfat-6*oh_select))
            else: 
                cfg_node = ""
            for iread in range(depth):
                vfat_cfg_run = read_backend_reg(cfg_node)
                cfg_run[vfat][phase] += (vfat_cfg_run != 0)
            
            if system=="backend":
                link_node = rw_reg.getNode('GEM_AMC.OH_LINKS.OH%d.VFAT%d.LINK_GOOD' % (oh_select, vfat-6*oh_select))
                sync_node = rw_reg.getNode('GEM_AMC.OH_LINKS.OH%d.VFAT%d.SYNC_ERR_CNT' % (oh_select, vfat-6*oh_select))
            else:
                link_node = ""
                sync_node = ""
            link_good[vfat][phase]    = read_backend_reg(link_node)
            sync_err_cnt[vfat][phase] = read_backend_reg(sync_node)

            print("\tResults of VFAT#%02d: link_good=%d, sync_err_cnt=%02d, cfg_run_errs=%d" % (vfat, link_good[vfat][phase], sync_err_cnt[vfat][phase], cfg_run[vfat][phase]))

    centers = 12*[0]
    widths  = 12*[0]

    for vfat in vfat_list:
        for phase in range(0, 16):
            errs[vfat][phase] = (not 1==link_good[vfat][phase]) + sync_err_cnt[vfat][phase] + cfg_run[vfat][phase]
        centers[vfat], widths[vfat] = find_phase_center(errs[vfat])

    print ("phase : 0123456789ABCDEF")
    for vfat in vfat_list:
        sys.stdout.write("VFAT%02d: " % (vfat))
        for phase in range(0, 16):

            if (widths[vfat]>0 and phase==center[vfat]):
                char=Colors.GREEN + "+" + Colors.ENDC
            elif (errs[vfat][phase]):
                char=Colors.GREEN + "-" + Colors.ENDC
            else:
                char = Colors.RED + "x" + Colors.ENDC

            sys.stdout.write("%s" % char)
            sys.stdout.flush()
        sys.stdout.write(" (center=%d, width=%d)\n" % (centers[vfat], widths[vfat]))
        sys.stdout.flush()

    # set phases for all vfats under test
    print ("Setting all VFAT phases to: " + str(hex(best_phase)))
    for vfat in vfat_list:
        setVfatRxPhase(system, vfat, best_phase)

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

def setVfatRxPhase(system, vfat, phase):

    lpgbt, oh_select, gbt_select, elink = vfat_to_oh_gbt_elink (vfat)

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

    vfat_oh_link_reset()

def test_find_phase_center():
    def check_finder(center, width, errs):
        if (center,width) == find_phase_center(errs):
            print "OK"
        else:
            print "FAIL"
    check_finder (5, 5,  [1,1,1,0,0,0,0,0,1,1,0,0,1,1,1,1]) # normal window
    check_finder (3, 4,  [1,0,0,0,0,1,1,1,1,1,0,0,0,1,1,1]) # symmetric goes to higher number (arbitrary)
    check_finder (0, 5,  [0,0,0,1,1,1,1,0,0,0,0,1,1,1,0,0]) # wraparound
    check_finder (3, 4,  [2,0,0,0,0,1,1,1,0,0,0,1,1,1,1,1]) # offset right
    check_finder (2, 4,  [1,0,0,0,0,2,1,1,0,0,0,1,1,1,1,1]) # offset left
    check_finder (0, 0,  [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]) # all bad (default to zero)
    check_finder (7, 16, [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]) # all good, pick the center (arbitrary)

if __name__ == '__main__':

    # Parsing arguments
    parser = argparse.ArgumentParser(description='LpGBT Phase Scan')
    parser.add_argument("-s", "--system", action="store", dest="system", help="system = backend or dryrun")
    #parser.add_argument("-l", "--lpgbt", action="store", dest="lpgbt", help="lpgbt = boss or sub")
    parser.add_argument("-v", "--vfatmask", action="store", dest="vfatmask", help="vfatmask = in binary (0b) or hex (0x) format for 12 VFATs (on 1 ME0 GEB)")
    #parser.add_argument("-o", "--ohid", action="store", dest="ohid", help="ohid = 0-7 (only needed for backend)")
    #parser.add_argument("-g", "--gbtid", action="store", dest="gbtid", help="gbtid = 0, 1 (only needed for backend)")
    parser.add_argument("-d", "--depth", action="store", dest="depth", default="1000", help="depth = number of times to check for cfg_run error")
    parser.add_argument("-b", "--bestphase", action="store", dest="bestphase", default="0x9", help="bestphase = Best value of the elinkRX phase (in hex)")
    parser.add_argument("-t", "--test", action="store", dest="test", default="0", help="test = enter 1 for only testing vfat communication, default is 0")
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
    
    vfatmask_int = 0
    if args.vfatmask is None:
        print (Colors.YELLOW + "Enter a mask for the 12 VFATs" + Colors.ENDC)
        sys.exit()
    elif "0b" in args.vfatmask:
        vfatmask_int = int(args.vfatmask,2)
    elif "0x" in args.vfatmask:
        vfatmask_int = int(args.vfatmask,16)
    else:
        print (Colors.YELLOW + "Enter a mask in binary (0b) or hex (0x) format" + Colors.ENDC)
        sys.exit()
    if vfatmask_int>(2**12 - 1):
        print (Colors.YELLOW + "VFAT mask can be maximum 12 bits (for 12 VFATS on 1 ME0 GEB)" + Colors.ENDC)
        sys.exit()
    
    if args.test not in ["0", "1"]:
        print (Colors.YELLOW + "Test option can only be 0 or 1" + Colors.ENDC)
        sys.exit()
        
    if "0x" not in args.bestphase:
        print (Colors.YELLOW + "Enter best phase in hex format" + Colors.ENDC)
        sys.exit()
    best_phase = int(args.bestphase, 16)
    if best_phase>16:
        print (Colors.YELLOW + "Phase can only be 4 bits" + Colors.ENDC)
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
    
    if not os.path.isfile(config_boss_filename):
        print (Colors.YELLOW + "Missing config file for boss: config_boss.txt" + Colors.ENDC)
        sys.exit()
    
    if not os.path.isfile(config_sub_filename):
        print (Colors.YELLOW + "Missing config file for sub: sub_boss.txt" + Colors.ENDC)
        sys.exit()

    global config_boss
    global config_sub
    config_boss = getConfig(config_boss_filename)
    config_sub  = getConfig(config_sub_filename)
    
    # Running Phase Scan
    try:
        if args.test == "1":
            lpgbt_communication_test(args.system, vfat_list, int(args.depth))
        else:
            lpgbt_phase_scan(args.system, vfat_list, int(args.depth), best_phase)
    except KeyboardInterrupt:
        print (Colors.RED + "Keyboard Interrupt encountered" + Colors.ENDC)
        rw_terminate()
    except EOFError:
        print (Colors.RED + "\nEOF Error" + Colors.ENDC)
        rw_terminate()

    # Termination
    rw_terminate()




