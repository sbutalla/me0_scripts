## General

Script for configuring LpGBTs on ME0 Optohybrid using either RPi+Cheesecake (preferred option) or USB dongle

lpGBT naming :

master (ASIAGO schematics) == boss (in software)

slave (ASIAGO schematics) == sub (in software)

## Installation

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

## Configuration

Configure the master/boss lpgbt with Cheesecake:

```python lpgbt_config.py -s chc -l boss```

and likewise configure the slave/sub lpgbt with Cheesecake:

```python lpgbt_config.py -s chc -l sub```

Configure thr master/boss lpgbt with Backend:

```python lpgbt_config.py -s backend -l boss -o <OH_LINK> -g <GBT_LINK>```

Configure thr slave/sub lpgbt with Backend:

```python lpgbt_config.py -s backend -l sub -o <OH_LINK> -g <GBT_LINK>```

## CHecking lpGBT Status

Check the status of the master/boss lpgbt with Cheesecake:

```python lpgbt_status.py -s chc -l boss```

Check the status of the slave/sub lpgbt with Cheesecake:

```python lpgbt_status.py -s chc -l sub```

## Fusing

Fuse the master/boss lpgbt with Cheesecake from text file produced by lpgbt_config.py:

```python lpgbt_efuse.py -s chc -l boss -f input_file -i config_boss.txt```

and likewise fuse the slave/sub lpgbt with Cheesecake from text file produced by lpgbt_config.py:

```python lpgbt_efuse.py -s chc -l sub -f input_file -i config_sub.txt```


## Eye Opening Monitor

Take an eye scan with Cheesecake:

```python lpgbt_eye.py -s chc -l boss```

Create an image:

```python lpgbt_eye_plot.py```

## BERT

Take a bert scan with Cheesecake, for example for DLFRAME (other data sources also possible, check script):

```python lpgbt_bert.py -s chc -l boss -b DLFRAME```
