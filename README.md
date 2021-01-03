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

configure the master/boss lpgbt with Cheesecake:

```python lpgbt_config.py -s chc -l boss```

and likewise configure the slave/sub lpgbt with Cheesecake:

```python lpgbt_config.py -s chc -l sub```

check the status of the lpgbt with Cheesecake:

```python status.py -s chc```

## Eye Opening Monitor

take an eye scan with Cheesecake:

```python lpgbt_eye.py -s chc -l boss```

create an image:

```python lpgbt_eye_plot.py```

## BERT

take a bert scan with Cheesecake, for example for DLFRAME (other data sources also possible, check script):

```python lpgbt_bert.py -s chc -l boss -b DLFRAME```
