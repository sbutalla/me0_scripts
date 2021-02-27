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

or alternatively it can be installed by Pip

## Using Backend

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

Configure thr master/boss lpgbt:

```python lpgbt_config.py -s backend -l boss -o <OH_LINK> -g <GBT_LINK>```

Configure thr slave/sub lpgbt:

```python lpgbt_config.py -s backend -l sub -o <OH_LINK> -g <GBT_LINK>```

Enable TX2 for VTRX+ if required:

```python lpgbt_vtrx.py -s backend -l boss -o <OH_LINK> -g <GBT_LINK> -t name -c TX2 -e 1```

## Using CHeeseCake

Comment out the following line in rw_reg_lpgbt.py:
```
import rw_reg
```

### Configuration

Configure the master/boss lpgbt:

```python lpgbt_config.py -s chc -l boss```

and likewise configure the slave/sub lpgbt:

```python lpgbt_config.py -s chc -l sub```

Enable TX2 for VTRX+ if required:

```python lpgbt_vtrx.py -s chc -l boss -t name -c TX2 -e 1```

### Checking lpGBT Status

Check the status of the master/boss lpgbt:

```python lpgbt_status.py -s chc -l boss```

Check the status of the slave/sub lpgbt:

```python lpgbt_status.py -s chc -l sub```

### Fusing

Fuse the master/boss lpgbt with Cheesecake from text file produced by lpgbt_config.py:

```python lpgbt_efuse.py -s chc -l boss -f input_file -i config_boss.txt```

and likewise fuse the slave/sub lpgbt with Cheesecake from text file produced by lpgbt_config.py:

```python lpgbt_efuse.py -s chc -l sub -f input_file -i config_sub.txt```

### Eye Opening Monitor

Take an eye scan:

```python lpgbt_eye.py -s chc -l boss```

Create an image:

```python lpgbt_eye_plot.py```

### BERT

Take a bert scan, for example for DLFRAME (other data sources also possible, check script):

```python lpgbt_bert.py -s chc -l boss -b DLFRAME```
