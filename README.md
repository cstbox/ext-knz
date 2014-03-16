# CSTBox extension for Kipp and Zonen ModBus products support

This repository contains the code for the extension adding the support
for Kipp and Zonen ModBus based products in the [CSTBox framework](http://cstbox.cstb.fr). 

Kipp and Zonen products are industrial modules for solar monitoring. More details can be found
on their [Web site](http://www.kippzonen.com/).

The support comes in two forms :

  * product drivers generating CSTBox events from registers map readings
  * products definition files (aka metadata) driving the associated Web configuration editor
    pages

## Currently supported products

  * **SMP11 pyranometer**
      * measures incoming global solar radiation with a 180° field of view

## Runtime dependencies

This extension requires the CSTBox core and ModBus support extension to be already installed.
