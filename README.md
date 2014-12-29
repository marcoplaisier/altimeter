Project Altimeter
------
------

Measuring temperature and air pressure with a single chip


Hardware Setup
------

The MS5607 is a cool chip that can measure both temperature and air pressure. It can measure air pressures between 10
mbar and 1200 mbar and temperatures between -40°C and +80°C. However, measuring is a little bit more complicated than 
getting a value from the chip. 
This chip is connected through SPI to a Raspberry Pi. Schematics will follow. It is powered through the standard GPIO
pins. 

Software Installation
------

Install with 

    pip install pyaltimeter
    
Run with 

    python pyaltimeter
    

Measuring Temperature
------

As said, measuring temperatures is a little more complicated than getting a simple value from the chip. Every device is 
calibrated in the factory and the calibration data is stored on the chip. The temperature value and calibration data 
are used together to calculate the measured temperature.

Measuring Air Pressure
------

Raw Data
------
