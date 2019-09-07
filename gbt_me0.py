#!/usr/bin/env python

from rw_reg import *
from time import *
import array
import struct

DEBUG=False

class Colors:            
    WHITE   = '\033[97m' 
    CYAN    = '\033[96m' 
    MAGENTA = '\033[95m' 
    BLUE    = '\033[94m' 
    YELLOW  = '\033[93m' 
    GREEN   = '\033[92m' 
    RED     = '\033[91m' 
    ENDC    = '\033[0m'  

ADDR_IC_ADDR = None
ADDR_IC_WRITE_DATA = None
ADDR_IC_EXEC_WRITE = None
ADDR_IC_EXEC_READ = None

ADDR_LINK_RESET = None

def main():

    command = ""
    ohSelect = 0
    gbtSelect = 0

    if len(sys.argv) < 4:
        print('Usage: gbt.py <oh_num> <gbt_num> <command>')
        print('available commands:')
        print('  config <config_filename_txt>:   Configures the GBT with the given config file (must use the txt version of the config file, can be generated with the GBT programmer software)')
        print('  led_show:   Makes a little show on the ASIAGO LED')
        return
    else:
        ohSelect = int(sys.argv[1])
        gbtSelect = int(sys.argv[2])
        command = sys.argv[3]

    if ohSelect > 11:
        printRed("The given OH index (%d) is out of range (must be 0-11)" % ohSelect)
        return
    if gbtSelect > 2:
        printRed("The given GBT index (%d) is out of range (must be 0-2)" % gbtSelect)
        return

    parseXML()

    initGbtRegAddrs()

    heading("Hello, I'm your GBT controller :)")

    if (checkGbtReady(ohSelect, gbtSelect) == 1):
        selectGbt(ohSelect, gbtSelect)
    else:
        printRed("Sorry, OH%d GBT%d link is not ready.. check the following: your OH is on, the fibers are plugged in correctly, the CTP7 TX polarity is correct, and muy importante, check that your GBTX is fused with at least the minimal config.." % (ohSelect, gbtSelect))
        return

    if (command == 'config'):
        if len(sys.argv) < 5:
            print("For this command, you also need to provide a config file")
            return

        subheading('Configuring OH%d GBT%d' % (ohSelect, gbtSelect))
        filename = sys.argv[4]
        if filename[-3:] != "txt":
            printRed("Seems like the file is not a txt file, please provide a txt file generated with the GBT programmer software")
            return
        if not os.path.isfile(filename):
            printRed("Can't find the file %s" % filename)
            return

        timeStart = clock()

        regs = downloadConfig(ohSelect, gbtSelect, filename)

        totalTime = clock() - timeStart
        print('time took = ' + str(totalTime) + 's')

    elif command == 'destroy':
        subheading('Destroying configuration of OH%d GBT%d' % (ohSelect, gbtSelect))
        destroyConfig()

    elif command == 'led_show':
        asiago_led_show()

    else:
        printRed("Unrecognized command '%s'" % command)
        return

    print("")
    print("bye now..")

def asiago_led_show():
    wReg(ADDR_IC_ADDR, 0x054) # PIOOutH
    brightnessStart = 0
    while True: # cycle brightness from on to off and off to on approx once per second (assuming 100kHz update rate)
        brightnessEnd = 100
        step = 1
        if brightnessStart == 0:
            brightnessStart = 100
            brightnessEnd = -1
            step = -1
        else:
            brightnessStart = 0
            brightnessEnd = 101
            step = 1

        for b in range(brightnessStart, brightnessEnd, step): # one brightness cycle from on to off or off to on (100 steps per cycle)
            for i in range(10): # generate 10 clocks at a specific brightness
                for j in range(100): # generate a PWM waveform for one clock, setting the duty cycle according to the brightness
                    on = 0x80
                    if j >= b:
                        on = 0x00
                    wReg(ADDR_IC_WRITE_DATA, on)
                    wReg(ADDR_IC_EXEC_WRITE, 1)



def downloadConfig(ohIdx, gbtIdx, filename):
    f = open(filename, 'r')

    #for now we'll operate with 8 bit words only
    writeReg(getNode("GEM_AMC.SLOW_CONTROL.IC.READ_WRITE_LENGTH"), 1)

    ret = []

    lines = 0
    addr = 0
    for line in f:
        value = int(line, 16)
        wReg(ADDR_IC_ADDR, addr)
        wReg(ADDR_IC_WRITE_DATA, value)
        wReg(ADDR_IC_EXEC_WRITE, 1)
        addr += 1
        lines += 1
        ret.append(value)

    print("Wrote %d registers to OH%d GBT%d" % (lines, ohIdx, gbtIdx))
    if lines < 366:
        printRed("looks like you gave me an incomplete file, since I found only %d registers, while a complete config should contain 366 registers")

    f.close()

    return ret

def destroyConfig():
    for i in range(0, 369):
        wReg(ADDR_IC_ADDR, i)
        wReg(ADDR_IC_WRITE_DATA, 0)
        wReg(ADDR_IC_EXEC_WRITE, 1)

def initGbtRegAddrs():
    global ADDR_IC_ADDR
    global ADDR_IC_WRITE_DATA
    global ADDR_IC_EXEC_WRITE
    global ADDR_IC_EXEC_READ
    ADDR_IC_ADDR = getNode('GEM_AMC.SLOW_CONTROL.IC.ADDRESS').real_address
    ADDR_IC_WRITE_DATA = getNode('GEM_AMC.SLOW_CONTROL.IC.WRITE_DATA').real_address
    ADDR_IC_EXEC_WRITE = getNode('GEM_AMC.SLOW_CONTROL.IC.EXECUTE_WRITE').real_address
    ADDR_IC_EXEC_READ = getNode('GEM_AMC.SLOW_CONTROL.IC.EXECUTE_READ').real_address

def initVfatRegAddrs():
    global ADDR_LINK_RESET
    ADDR_LINK_RESET = getNode('GEM_AMC.GEM_SYSTEM.CTRL.LINK_RESET').real_address

def selectGbt(ohIdx, gbtIdx):
    linkIdx = ohIdx * 3 + gbtIdx

    writeReg(getNode('GEM_AMC.SLOW_CONTROL.IC.GBTX_LINK_SELECT'), linkIdx)
    writeReg(getNode('GEM_AMC.SLOW_CONTROL.IC.GBTX_I2C_ADDR'), 0x70)

    return 0

def checkGbtReady(ohIdx, gbtIdx):
    return parseInt(readReg(getNode('GEM_AMC.OH_LINKS.OH%d.GBT%d_READY' % (ohIdx, gbtIdx))))

def check_bit(byteval,idx):
    return ((byteval&(1<<idx))!=0);

def debug(string):
    if DEBUG:
        print('DEBUG: ' + string)

def debugCyan(string):
    if DEBUG:
        printCyan('DEBUG: ' + string)

def heading(string):                                                                    
    print Colors.BLUE                                                             
    print '\n>>>>>>> '+str(string).upper()+' <<<<<<<'
    print Colors.ENDC                   
                                                      
def subheading(string):                         
    print Colors.YELLOW                                        
    print '---- '+str(string)+' ----',Colors.ENDC                    
                                                                     
def printCyan(string):                                                
    print Colors.CYAN                                    
    print string, Colors.ENDC                                                                     
                                                                      
def printRed(string):                                                                                                                       
    print Colors.RED                                                                                                                                                            
    print string, Colors.ENDC                                           

def hex(number):
    if number is None:
        return 'None'
    else:
        return "{0:#0x}".format(number)

def binary(number, length):
    if number is None:
        return 'None'
    else:
        return "{0:#0{1}b}".format(number, length + 2)

if __name__ == '__main__':
    main()
