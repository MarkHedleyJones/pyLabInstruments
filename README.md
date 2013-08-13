pyInstruments
=============

A simple library for controlling USB and Serial based measurement instruments in Linux. It does not have a gui but provides a wrapper around instruments controlled via usb or serial interface.
It does not rely on the VISA library. No docmunetation exists as yet.

## Supported instruments

###usb_instruments:
* Agilent 3320A Arbitrary Waveform Generator

###serial_instruments:
* Tektronix TPS2024B Digital Storage Oscilloscope


## Usage

    import serial_instruments
    import usb_instruments
    
    scope = serial_instruments.tek2024('/dev/ttyS0')
    wavegen = usb_instruments.agilent33220A('/dev/usbtmc0')
    channel1 = serial_instruments.channel(scope,1)
    channel2 = serial_instruments.channel(scope,2)
    
    wavegen.mode('sine')  # Enable sinusodal output
    wavegen.frequency(1000)  # Set the frequency to 1kHz
    wavegen.voltage(2)  # Set the output amplitude to 2V
    wavegen.output(True)  # Enable the output
    
    scope.set_hScale(frequency=1000, cycles=8)  # Set the time scale to the mimimum that contains 8 waveforms
    scope.set_averaging(16)  # Set the scope to do 16X averaging
    channel1.set_vScale(1)  # Set the voltage scale to 
    channel2.set_vScale(1)
    
    data_voltage = channel1.get_waveform()  # Download the waveform from channel 1
    data_current = channel2.get_waveform()  # Download the waveform from channel 2
