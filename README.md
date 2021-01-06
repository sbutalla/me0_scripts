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

```python3 lpgbt_config.py -s chc -l boss```

and likewise configure the slave/sub lpgbt with Cheesecake:

```python3 lpgbt_config.py -s chc -l sub```

Check the status of the lpgbt with Cheesecake:

```python3 status.py -s chc```

## Fusing

Fuse the master/boss lpgbt with Cheesecake from text file produced by lpgbt_config.py:

```python3 lpgbt_efuse.py -s chc -l boss -f input_file -i config_boss.txt```

and likewise fuse the slave/sub lpgbt with Cheesecake from text file produced by lpgbt_config.py:

```python3 lpgbt_efuse.py -s chc -l sub -f input_file -i config_sub.txt```


## Eye Opening Monitor

Take an eye scan with Cheesecake:

```python3 lpgbt_eye.py -s chc -l boss```

Create an image:

```python3 lpgbt_eye_plot.py```

## BERT

Take a bert scan with Cheesecake, for example for DLFRAME (other data sources also possible, check script):

```python3 lpgbt_bert.py -s chc -l boss -b DLFRAME```
