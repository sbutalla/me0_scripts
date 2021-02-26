from cmd import Cmd
import sys, os, subprocess
from rw_reg_lpgbt import *
import argparse

class Prompt(Cmd):

    def do_hello(self, args):
        """Says hello. If you provide a name, it will greet you with it."""
        if len(args) == 0:
            name = 'stranger'
        else:
            name = args
        print "Hello, %s" % name


    def do_read(self, args):
        """Reads register. USAGE: read <register name>. OUTPUT <address> <mask> <permission> <name> <value>"""
        reg = getNode(args)
        if reg is not None:
            address = reg.real_address
            if 'r' in str(reg.permission):
                print displayReg(reg)
            elif reg.isModule:
                print 'This is a module!'
            else:
                print hex(address),'\t',reg.name,'\t','No read permission!'
        else:
            print args,'not found!'


    def complete_read(self, text, line, begidx, endidx):
        return completeReg(text)


    def do_write(self, args):
        """Writes register. USAGE: write <register name> <register value>"""
        arglist = args.split()
        if len(arglist)!=2:
            print "Incorrect number of arguments!"
        else:
            reg = getNode(arglist[0])
            if reg is not None:
                try: value = parseInt(arglist[1])
                except:
                    print 'Write Value must be a number!'
                    return
                if 'w' in str(reg.permission):
                    print writeReg(reg,value)
                else:
                    print 'No write permission!'
            else:
                print arglist[0],'not found!'

    def complete_write(self, text, line, begidx, endidx):
        return completeReg(text)


    def do_readGroup(self, args): #INEFFICIENT
        """Read all registers below node in register tree. USAGE: readGroup <register/node name> """
        node = getNode(args)
        if node is not None:
            print 'NODE:',node.name
            kids = []
            getAllChildren(node, kids)
            print len(kids),'CHILDREN'
            for reg in kids:
                if 'r' in str(reg.permission): print displayReg(reg)
        else: print args,'not found!'

    def complete_readGroup(self, text, line, begidx, endidx):
        return completeReg(text)

    def do_readFW(self, args):
        """Quick read of all FW-related registers"""
        for reg in getNodesContaining('STATUS.FW'):
            if 'r' in str(reg.permission): print hex(reg.real_address),reg.permission,'\t',tabPad(reg.name,4),readRegStr(reg)

    def do_readKW(self, args):
        """Read all registers containing KeyWord. USAGE: readKW <KeyWord>"""
        if getNodesContaining(args) is not None and args!='':
            for reg in getNodesContaining(args):
                address = reg.real_address
                if 'r' in str(reg.permission):
                    print hex(address).rstrip('L'),reg.permission,'\t',tabPad(reg.name,7),readRegStr(reg)
                elif reg.isModule: print hex(address).rstrip('L'),reg.permission,'\t',tabPad(reg.name,7) #,'Module!'
                else: print hex(address).rstrip('L'),reg.permission,'\t',tabPad(reg.name,7) #,'No read permission!'
        else: print args,'not found!'



    def do_readAll(self, args):
        """Read all registers with read-permission"""
        for reg in getNodesContaining(''):
            if 'r' in (reg.permission):
                print displayReg(reg)

    def do_exit(self, args):
        """Exit program"""
        return True

    def do_readAddress(self, args):
        """ Directly read address. USAGE: readAddress <address> """
        try: reg = getNodeFromAddress(parseInt(args))
        except:
            print 'Error retrieving node.'
            return
        if reg is not None:
            address = reg.real_address
            if 'r' in str(reg.permission):
                print hex(address),'{0:#010x}'.format(reg.mask),reg.permission,'\t',reg.name,'\t',readRegStr(reg)
            elif reg.isModule:
                print 'This is a module!'
            else:
                print hex(address),'\t',reg.name,'\t','No read permission!'
        else:
            print args,'not found!'

    def do_readRawAddress(self, args):
        """Read raw address (from XML file). USAGE: readRawAddress <address> """
        try: print readRawAddress(args)
        except: print 'Error reading address. (reg_interface)'


    def do_mpeek(self,args):
        """Basic mpeek command to read register. USAGE: mpeek <address>"""
        print mpeek(args)

    def do_mpoke(self,args):
        """Basic mpoke command to write register. USAGE: mpoke <address> <value>"""
        arglist = args.split()
        if len(arglist)==2:
            print mpoke(arglist[0],arglist[1])
        else: print "Incorrect number of arguments!"


if __name__ == '__main__':
    # Parsing arguments
    parser = argparse.ArgumentParser(description='Register Interface for lpGBT')
    parser.add_argument("-s", "--system", action="store", dest="system", help="system = chc or backend or dongle or dryrun")
    parser.add_argument("-l", "--lpgbt", action="store", dest="lpgbt", help="lpgbt = boss or sub")
    parser.add_argument("-o", "--ohid", action="store", dest="ohid", help="ohid = 0-7 (only needed for backend)")
    parser.add_argument("-g", "--gbtid", action="store", dest="gbtid", help="gbtid = 0, 1 (only needed for backend)")
    args = parser.parse_args()

    if args.system == "chc":
        print ("Using Rpi CHeeseCake for interface")
    elif args.system == "backend":
        print ("Using Backend for interface")
        #print ("Only chc (Rpi Cheesecake) or dryrun supported at the moment")
        #sys.exit()
    elif args.system == "dongle":
        #print ("Using USB Dongle for interface")
        print ("Only chc (Rpi Cheesecake) or dryrun supported at the moment")
        sys.exit()
    elif args.system == "dryrun":
        print ("Dry Run - not actually interfacing with lpGBT")
    else:
        print ("Only valid options: chc, backend, dongle, dryrun")
        sys.exit()

    boss = None
    if args.lpgbt is None:
        print ("Please select boss or sub")
        sys.exit()
    elif (args.lpgbt=="boss"):
        print ("Configuring LPGBT as boss")
        boss=1
    elif (args.lpgbt=="sub"):
        print ("Configuring LPGBT as sub")
        boss=0
    else:
        print ("Please select boss or sub")
        sys.exit()
    if boss is None:
        sys.exit()
        
    if args.system == "backend":
        if args.ohid is None:
            print ("Need OHID for backend")
            sys.exit()
        if args.gbtid is None:
            print ("Need GBTID for backend")
            sys.exit()
        if int(args.ohid)>7:
            print ("Only OHID 0-7 allowed")
            sys.exit()
        if int(args.gbtid)>1:
            print ("Only GBTID 0 and 1 allowed")
            sys.exit() 
    else:
        if args.ohid is not None or args.gbtid is not None:
            print ("OHID and GBTID only needed for backend")
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

    try:
        prompt = Prompt()
        prompt.prompt = args.system
        prompt.cmdloop('Starting Register Command Line Interface.')
    except KeyboardInterrupt:
        print ("Keyboard Interrupt encountered")
        rw_terminate()
    except EOFError:
        print ("\nEOF Error")
        rw_terminate()
        
    # Termination
    rw_terminate()

