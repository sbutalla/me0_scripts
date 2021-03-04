## General

Script for configuring LpGBTs on ME0 Optohybrid using either RPi+Cheesecake (preferred option) or USB dongle

lpGBT naming :

master (ASIAGO schematics) == boss (in software)

slave (ASIAGO schematics) == sub (in software)

## Installation

```
git clone https://github.com/andrewpeck/me0_scripts.git
cd me0_scripts
git checkout cheesecake_integration
cd ..
```

The scripts depend on the cython-hidapi library (https://github.com/trezor/cython-hidapi)

It can be built from source with:

```
git clone https://github.com/trezor/cython-hidapi.git
cd cython-hidapi
git submodule update --init
python setup.py build
sudo python setup.py install
```

```
cd me0_scripts
```

or alternatively it can be installed by Pip

## Using Backend

Login as root

Set some environment variables (after compiling the 0xbefe repo):

```
export ADDRESS_TABLE="<Absolute Path for 0xbefe/address_table/gem/generated/me0_cvp13/gem_amc.xml>"
export ME0_LIBRWREG_SO="<Absolute Path for 0xbefe/scripts/boards/cvp13/rwreg/librwreg.so>"
```

Comment out the following lines in lpgbt_rpi_chc.py:
```
import RPi.GPIO as GPIO
import smbus
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
self.bus = smbus.SMBus(device_bus)
self.lpgbt_address = 0x70
def __del__(self):
    self.bus.close()
    GPIO.cleanup()
```

### Configuration

Configure the master/boss lpgbt:

```
python lpgbt_config.py -s backend -l boss -o <OH_LINK> -g <GBT_LINK>
```

Configure the slave/sub lpgbt:

```
python lpgbt_config.py -s backend -l sub -o <OH_LINK> -g <GBT_LINK>
```

Enable TX2 for VTRX+ if required:

```
python lpgbt_vtrx.py -s backend -l boss -o <OH_LINK> -g <GBT_LINK> -t name -c TX2 -e 1
```

## Using CHeeseCake

Comment out the following line in rw_reg_lpgbt.py:
```
import rw_reg
```

### Configuration

Configure the master/boss lpgbt:

```
python lpgbt_config.py -s chc -l boss
```

Configure the slave/sub lpgbt:

```
python lpgbt_config.py -s chc -l sub
```

Enable TX2 for VTRX+ if required:

```
python lpgbt_vtrx.py -s chc -l boss -t name -c TX2 -e 1
```

### Checking lpGBT Status

Check the status of the master/boss lpgbt:

```
python lpgbt_status.py -s chc -l boss
```

Check the status of the slave/sub lpgbt:

```
python lpgbt_status.py -s chc -l sub
```

### Fusing

Fuse the master/boss lpgbt with Cheesecake from text file produced by lpgbt_config.py:

```
python lpgbt_efuse.py -s chc -l boss -f input_file -i config_boss.txt
```

Fuse the slave/sub lpgbt with Cheesecake from text file produced by lpgbt_config.py:

```
python lpgbt_efuse.py -s chc -l sub -f input_file -i config_sub.txt`
```

### Eye Opening Monitor

Take an eye scan:

```
python lpgbt_eye.py -s chc -l boss
```

Create an image:

```
python lpgbt_eye_plot.py -d <DIR NAME for EYE SCAN RESULTS>
```

### BERT

Take a bert scan, for example for DLFRAME (other data sources also possible, check script):

```
python lpgbt_bert.py -s chc -l boss -b DLFRAME
```




