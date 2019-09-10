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

configure the master lpgbt with:

```sudo python lpgbt_config.py master```

and likewise configure the slave lpgbt with

```sudo python lpgbt_config.py slave```

check the status of the lpgbt with

```sudo python status.py```

## Eye Opening Monitor

take an eye scan with

```sudo python lpgbt_eye.py```

create an image with

```sudo python lpgbt_eye_plot.py```

## BERT

take a bert scan with

```sudo python lpgbt_bert.py```
