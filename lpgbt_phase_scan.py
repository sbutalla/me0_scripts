#!/usr/bin/env python

from rw_reg import *

import time
import sys

ADDR_IC_ADDR             = None
ADDR_IC_WRITE_DATA       = None
ADDR_IC_EXEC_WRITE       = None
ADDR_IC_EXEC_READ        = None
ADDR_IC_GBTX_I2C_ADDR    = None
ADDR_IC_GBTX_LINK_SELECT = None
ADDR_LINK_RESET          = None

def checkGbtReady(ohIdx, gbtIdx):
    #print ('Checking GEM_AMC.OH_LINKS.OH%d.GBT%d_READY' % (ohIdx, gbtIdx))
    return parseInt(readReg(getNode('GEM_AMC.OH_LINKS.OH%d.GBT%d_READY' % (ohIdx, gbtIdx))))

def getConfig (filename):

    f = open(filename, 'r')
    ret = []
    lines = 0
    addr = 0
    for line in f:
        value = int(line, 16)
        addr += 1
        ret.append(value)
    f.close()

    return ret

config_master = getConfig("config_master.txt")
config_slave  = getConfig("config_slave.txt")

class Colors:
    WHITE   = '\033[97m'
    CYAN    = '\033[96m'
    MAGENTA = '\033[95m'
    BLUE    = '\033[94m'
    YELLOW  = '\033[93m'
    GREEN   = '\033[92m'
    RED     = '\033[91m'
    ENDC    = '\033[0m'

VFAT_TO_ELINK = {
        0  : ("slave"  , "classic" , 6),
        1  : ("slave"  , "classic" , 24),
        2  : ("slave"  , "classic" , 27),
        3  : ("master" , "classic" , 6),
        4  : ("master" , "classic" , 27),
        5  : ("master" , "classic" , 25),
        6  : ("master" , "spicy"   , 6),
        7  : ("master" , "spicy"   , 25),
        8  : ("slave"  , "spicy"   , 24),
        9  : ("master" , "spicy"   , 27),
        10 : ("slave"  , "spicy"   , 6),
        11 : ("slave"  , "spicy"   , 27)
        }

def vfat_to_oh_gbt_elink (vfat):

    lpgbt = VFAT_TO_ELINK[vfat][0]
    slot  = VFAT_TO_ELINK[vfat][1]
    elink = VFAT_TO_ELINK[vfat][2]

    slave_select = (lpgbt=="slave")
    spicy_select = (slot=="spicy")

    oh_select = pizza_select * 2 + spicy_select
    gbt_select = slave_select
    return (oh_select, gbt_select, elink)

def lpgbt_communication_test (pizza_select, vfat_list, depth):

    wReg(ADDR_LINK_RESET, 1)

    cfg_run = 12*[0]

    depth = 1000

    for vfat in vfat_list:

        (oh_select, gbt_select, elink) = vfat_to_oh_gbt_elink (vfat)
        node = getNode('GEM_AMC.OH.OH%d.GEB.VFAT%d.CFG_RUN' % (oh_select, vfat-6*oh_select)).real_address
        for iread in range(depth):
            cfg_run[vfat] += (rReg(node) != 0)

        print ("VFAT#%02d: reads=%d, errs=%d" % (vfat, depth, cfg_run[vfat]))


def lpgbt_phase_scan (pizza_select, vfat_list, depth):

    print ("LPGBT Phase Scan depth=%s transactions" % (vfat_mask, str(depth)))

    link_good    = [[0 for phase in range(16)] for vfat in range(12)]
    sync_err_cnt = [[0 for phase in range(16)] for vfat in range(12)]
    cfg_run      = [[0 for phase in range(16)] for vfat in range(12)]
    errs         = [[0 for phase in range(16)] for vfat in range(12)]

    for phase in range(0, 16):

        print('Scanning phase %d' % phase)

        # set phases for all vfats under test
        for vfat in vfat_list:
            setVfatRxPhase(vfat, phase)

        time.sleep(0.01)

        # reset the link, give some time to lock and accumulate any sync errors and then check VFAT comms
        wReg(ADDR_LINK_RESET, 1)

        # read cfg_run some number of times
        for vfat in vfat_list:

            (oh_select, gbt_select, elink) = vfat_to_oh_gbt_elink (vfat)
            if (checkGbtReady(oh_select, gbt_select) == 0):
                break

            node = getNode('GEM_AMC.OH.OH%d.GEB.VFAT%d.CFG_RUN' % (oh_select, vfat-6*oh_select)).real_address
            for iread in range(depth):
                cfg_run[vfat][phase] += (parseInt(rReg(node))!=0)

        # set phases
        for vfat in vfat_list:
            (oh_select, gbt_select, elink) = vfat_to_oh_gbt_elink (vfat)
            if (checkGbtReady(oh_select, gbt_select) == 0):
                break

            #print "reading GEM_AMC.OH_LINKS.OH%d.VFAT%d.LINK_GOOD" % (oh_select, vfat-6*oh_select)
            link_good[vfat][phase]    = parseInt(readReg(getNode('GEM_AMC.OH_LINKS.OH%d.VFAT%d.LINK_GOOD' % (oh_select, vfat-6*oh_select))))
            sync_err_cnt[vfat][phase] = parseInt(readReg(getNode('GEM_AMC.OH_LINKS.OH%d.VFAT%d.SYNC_ERR_CNT' % (oh_select, vfat-6*oh_select))))

            print("\tResults of VFAT#%02d: link_good=%d, sync_err_cnt=%02d, cfg_run_errs=%d" % (vfat, link_good[vfat][phase], sync_err_cnt[vfat][phase], cfg_run[vfat][phase]))

    centers = 16*[0]
    widths  = 16*[0]

    for vfat in vfat_list:
        for phase in range(0, 16):
            errs[vfat][phase] = (not 1==link_good[vfat][phase]) + sync_err_cnt[vfat][phase] + cfg_run[vfat][phase]
        (centers[vfat], width[vfat]) = find_phase_center (errs[vfat])

    print ("phase : 0123456789ABCDEF")
    for vfat in vfat_list:
        sys.stdout.write("VFAT%02d: " % (vfat))
        for phase in range(0, 16):

            if (width[vfat]>0 and phase==center[vfat]):
                char=Colors.GREEN + "+" + Colors.ENDC
            elif (errs[vfat][phase]):
                char=Colors.GREEN + "-" + Colors.ENDC
            else:
                char = Colors.RED + "x" + Colors.ENDC

            sys.stdout.write("%s" % char)
            sys.stdout.flush()
        sys.stdout.write(" (center=%d, width=%d)\n" % (centers[vfat], width[vfat]))
        sys.stdout.flush()


    # set phases for all vfats under test
    best_phase = 0x9
    for vfat in vfat_list:
        setVfatRxPhase(vfat,best_phase)

def find_phase_center (err_list):

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

    # cover the case when there are no edges... just pick the center
    if (ngood==len(err_list_doubled)):
        ngood_max  = ngood / 2
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

    return (ngood_center, ngood_max)

def setVfatRxPhase(vfat, phase):

    (oh_select, gbt_select, elink) = vfat_to_oh_gbt_elink (vfat)

    config = config_master
    if (gbt_select % 2 != 0):
        config = config_slave

    # set phase
    GBT_ELIKN_SAMPLE_PHASE_BASE_REG = 0x0CC
    addr = GBT_ELIKN_SAMPLE_PHASE_BASE_REG + elink
    value = (config[addr] & 0x0f) | (phase << 4)

    if (gbt_select % 2 ==0):
        name="master"
    else:
        name="slave"

    #print ("writing %02X to adr=%04X for %s elink %d" % (value, addr, name, elink))

    link_select = oh_select*2 + gbt_select;
    writeReg(getNode('GEM_AMC.SLOW_CONTROL.IC.GBTX_LINK_SELECT'), link_select)

    wReg(ADDR_IC_ADDR,             addr)
    wReg(ADDR_IC_WRITE_DATA,       value)
    wReg(ADDR_IC_GBTX_I2C_ADDR,    0x70)
    wReg(ADDR_IC_GBTX_LINK_SELECT, link_select)
    wReg(ADDR_IC_EXEC_WRITE,       1)

    writeReg(getNode('GEM_AMC.GEM_SYSTEM.CTRL.LINK_RESET'), 1)

def initGbtRegAddrs():

    global ADDR_IC_ADDR
    global ADDR_IC_WRITE_DATA
    global ADDR_IC_EXEC_WRITE
    global ADDR_IC_EXEC_READ
    global ADDR_IC_GBTX_I2C_ADDR
    global ADDR_IC_GBTX_LINK_SELECT
    global ADDR_LINK_RESET

    ADDR_IC_WRITE_DATA       = getNode('GEM_AMC.SLOW_CONTROL.IC.WRITE_DATA').real_address
    ADDR_IC_EXEC_WRITE       = getNode('GEM_AMC.SLOW_CONTROL.IC.EXECUTE_WRITE').real_address
    ADDR_IC_EXEC_READ        = getNode('GEM_AMC.SLOW_CONTROL.IC.EXECUTE_READ').real_address
    ADDR_IC_GBTX_I2C_ADDR    = getNode('GEM_AMC.SLOW_CONTROL.IC.GBTX_I2C_ADDR').real_address
    ADDR_IC_GBTX_LINK_SELECT = getNode('GEM_AMC.SLOW_CONTROL.IC.GBTX_LINK_SELECT').real_address
    ADDR_LINK_RESET          = getNode('GEM_AMC.GEM_SYSTEM.CTRL.LINK_RESET').real_address
    ADDR_IC_ADDR             = getNode('GEM_AMC.SLOW_CONTROL.IC.ADDRESS').real_address

def test_find_phase_center ():

    def check_finder (center, width, errs):
        if (center,width) == find_phase_center (errs):
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

    if len(sys.argv) < 3:
        print('Usage: lpgbt_phase_scan.py <pizza_num> <vfat_mask> <depth>')
        sys.exit()

    pizza_select = int(sys.argv[1],0)
    vfat_mask    = int(sys.argv[2],0)
    depth        = int (sys.argv[3])

    # construct a list of vfats to be scanned based on the mask
    vfat_list = []
    for vfat in range(0,12):
        if (0x1 & (vfat_mask>>vfat)):
            vfat_list.append(vfat)

    parseXML()
    initGbtRegAddrs()

    if (len(sys.argv)>4 and sys.argv[4]=="test"):
        lpgbt_communication_test (pizza_select, vfat_list, depth)
    else:
        import cProfile
        #cProfile.run('lpgbt_phase_scan (pizza_select, vfat_list, depth)')
        lpgbt_phase_scan (pizza_select, vfat_list, depth )
