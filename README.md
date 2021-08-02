## General

Script for configuring lpGBTs on ME0 Optohybrid using either RPi+Cheesecake or Backend

lpGBT naming :

master (ASIAGO schematics) == boss (in software)

slave (ASIAGO schematics) == sub (in software)

## Installation

```
git clone https://github.com/andrewpeck/me0_scripts.git
cd me0_scripts
git checkout cheesecake_integration
```

## Powering On

After every power on, lpGBTs on ASIAGO need to be configured.

For unfused ASIAGOs: configure both lpGBTs using RPi-CHeeseCake

For fused ASIAGOs: reconfigure both lpGBTs using Backend or RPi-CHeeseCake


## Using Backend

Login as root

Set some environment variables (after compiling the 0xbefe repo):

```
export ADDRESS_TABLE="<Absolute Path for 0xbefe/address_table/gem/generated/me0_cvp13/gem_amc.xml>"
export ME0_LIBRWREG_SO="<Absolute Path for 0xbefe/scripts/boards/cvp13/rwreg/librwreg.so>"
export BOARD_TYPE="cvp13"
```

### Configuration

Configure the master/boss lpgbt:

```
python lpgbt_config.py -s dryrun -l boss
python lpgbt_config.py -s backend -l boss -o <OH_LINK_NR> -g <GBT_LINK_NR> -i config_boss.txt
```

Configure the slave/sub lpgbt:

```
python lpgbt_config.py -s dryrun -l sub
python lpgbt_config.py -s backend -l sub -o <OH_LINK_NR> -g <GBT_LINK_NR> -i config_sub.txt
```

Enable TX2 for VTRX+ if required:

```
python lpgbt_vtrx.py -s backend -l boss -o <OH_LINK_NR> -g <GBT_LINK_NR> -t name -c TX1 TX2 -e 1
```

## Using CHeeseCake

### Configuration

Configure the master/boss lpgbt:

```
python lpgbt_config.py -s chc -l boss
```

Configure the slave/sub lpgbt:

```
python lpgbt_config.py -s chc -l sub
```

Enable TX2 for VTRX+ if required (usually VTRX+ enabled during configuration):

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

Obtain the config .txt files first with a dryrun:

```
python lpgbt_config.py -s dryrun -l boss
python lpgbt_config.py -s dryrun -l sub

```

Fuse the USER IDs with Cheesecake:
```
python lpgbt_efuse.py -s chc -l boss -f user_id -u USER_ID_BOSS
python lpgbt_efuse.py -s chc -l sub -f user_id -u USER_ID_SUB
```

Fuse the master/boss lpgbt with Cheesecake from text file produced by lpgbt_config.py:

```
python lpgbt_efuse.py -s chc -l boss -f input_file -i config_boss.txt -v 1 -c 1
```

Fuse the slave/sub lpgbt with Cheesecake from text file produced by lpgbt_config.py:

```
python lpgbt_efuse.py -s chc -l sub -f input_file -i config_sub.txt -c 1
```

## Details of all scripts:

Use -h option for any script to check usage

```lpgbt_action_reset_wd.py```: either reset or disable/enable watchdog for lpGBT

```lpgbt_asense_monitor.py```: monitor asense on ME0 GEB

```lpgbt_bias_rssi_scan.py```: scan VTRX+ bias current vs RSSI

```lpgbt_config.py```: configure or unconfigure lpGBT

```lpgbt_efuse.py```: fuse registers on lpGBT

```lpgbt_eye.py```: downlink eye diagram using lpGBT

```lpgbt_eye_equalizer_scan.py```: scan equalizer settings using eye diagram

```lpgbt_eye_plot.py```: plot downlink eye diagram

```lpgbt_led_show.py```: GPIO led show

```lpgbt_optical_link_bert.py```: bit error ratio tests for optical links (uplink/downlink/loopback) between lpGBT and backend using PRBS

```lpgbt_optical_link_bert_fec.py```: bit error ratio tests for optical links (uplink/downlink) between lpGBT and backend using fec error rate counting 

```lpgbt_init.py```: initialize lpGBT

```lpgbt_rssi_monitor.py```: monitor for VTRX+ RSSI value

```lpgbt_rw_register.py```: read/write to any register on lpGBT

```lpgbt_status.py```: check status of lpGBT

```lpgbt_vfat_config.py```: configure VFAT

```lpgbt_vfat_daq_test.py```: bit error ratio tests by reading DAQ data packets from VFATs

```lpgbt_vfat_elink_scan.py```: scan VFAT vs elink 

```lpgbt_vfat_phase_scan.py```: phase scan for VFAT elinks and set optimal phase setting

```lpgbt_vfat_reset.py```: reset VFAT

```lpgbt_vfat_sbit_mapping.py```: S-bit mapping for VFATs (only works with test firmware)

```lpgbt_vfat_sbit_test.py```: S-bit testing for VFATs (only works with test firmware)

```lpgbt_vfat_slow_control_test.py```: error tests by read/write on VFAT registers using slow control

```lpgbt_vfat_slow_control_timing_test.py```: timing tests for read/write on VFAT registers using slow control

```lpgbt_vtrx.py```: enable/disable TX channels or registers on VTRX+

```reg_interface.py```: interactive tool to communicate with lpGBT registers

## Retrieving VFAT Calibrbation Data

To execute the script get_cal_info_vfat.py:
1. Install the `cx_Oracle` `python` module:
   ```
   $ pip3 install cx_Oracle
   ```
   `cx_Oracle` is an API used to interface with Oracle databases.
2. Define the following environment variables in your `.bash_profile`:
```
export GEM_ONLINE_DB_CONN="CMS_GEM_APPUSER_R/GEM_Reader_2015@"
export GEM_ONLINE_DB_NAME="INT2R_LB_LOCAL"
```
and source:
```
source ~/.bash_profile
```
3. Add the script `cheesecake_integration_devel/tnsnames.ora` to `/etc`. This file specifies the connection information for the Oracle database.
4. Edit the last line of DBconnect with your lxplus username.
5. In a separate shell session, open the tunnel to CERN's network with:
```
$ ./DBconnect.sh .
```
and login using your CERN credentials. (To execute from any directory, place `DBconnectsh` in `/usr/local/bin`.)
6. Update the VFAT text file (example file provided at `cheesecake_integration_devel/ME0WP_vfatID.txt`) with your list of plugin cards you want to retrieve calibration data for.
7. Execute the script:
```
# python3 get_cal_info_vfat.py -s backend -l <me0_layer> -g <geb_type> -a <asiago_number> -i <input_text_file>.txt -w
```
For more information on usage, run `# python3 get_cal_info_vfat.py -h`.
