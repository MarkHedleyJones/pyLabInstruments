import os, sys

class usbtmc:

    def __init__(self, device):
        self.device = device
        try:
            self.FILE = os.open(device, os.O_RDWR)
        except OSError as e:
            if str(e).find('No such file or directory') != -1:
                print("ERROR: Path to USB device does not exist ("
                      + device + ")")
                sys.exit()
            elif str(e).find("Permission denied:"):
                print "Getting permission to change permissions of " + device
                os.system("gksudo chmod 777 " + device)
                try:
                    self.FILE = os.open(device, os.O_RDWR)
                    print "Changed permissions and opened device"
                except:
                    print "Error opening device!"
                    sys.exit()
            else:
                print("Can't open path to device, have you ran: \n"
                      + "sudo chmod 777 " + device)
                sys.exit()

    def write(self, command):
        os.write(self.FILE, command);

    def read(self, length=4000):
        return os.read(self.FILE, length)

    def getName(self):
        self.write("*IDN?")
        return self.read(300)

    def sendReset(self):
        self.write("*RST")


class agilent33220A:

    _frequency = 0
    amplitude = 0

    def __init__(self, device):
        self.meas = usbtmc(device)
        self.name = self.meas.getName()
        self.voltage(0.1)
        print "Connected to: " + self.name.rstrip('\n')

    def write(self, command):
        """ Send an arbitrary command directly to the scope
        """
        self.meas.write(command)

    def read(self, command):
        """ Read an arbitrary amount of data directly from the scope
        """
        return self.meas.read(command)

    def reset(self):
        """ Reset the instrument
        """
        self.meas.sendReset()

    def frequency(self, freq):
        """ Sets the output frequency to the given value
        """
        self.meas.write("FREQ %f" % freq)
        self._frequency = freq

    def mode(self, mode):
        """ Selects the output mode
        Possible values are:
            sine     -> Sine wave
            square   -> Square wave
            ramp     -> Triangle/saw-tooth wave
            triangle -> Alias of ramp
            pulse    -> Pulse output
            noise    -> White noise
            dc       -> DC voltage
            user     -> Arbitrary waveforms
        """
        if mode.find('sin') != -1:
            self.meas.write("FUNC SIN")
        elif mode.find('squ') != -1:
            self.meas.write("FUNC SQU")
        elif mode.find('ramp') != -1:
            self.meas.write("FUNC RAMP")
        elif mode.find('tri') != -1:
            self.meas.write("FUNC RAMP")
        elif mode.find('puls') != -1:
            self.meas.write("FUNC PULS")
        elif mode.find('nois') != -1:
            self.meas.write("FUNC NOIS")
        elif mode.find('dc') != -1:
            self.meas.write("FUNC DC")
        elif mode.find('user') != -1:
            self.meas.write("FUNC USER")
        else:
            print 'Invalid waveform mode specified'
            sys.exit()

    def voltage(self, amplitude=None):
        """ Sets the output voltage of the device.
        NOTE: The device expects to be driving into a 50 Ohm load so.
        If driving loads of higher impedance you will get more voltage.
        """
        if amplitude is not None:
            self.meas.write("VOLT %f" % amplitude)
            self.amplitude = amplitude
        return self.amplitude

    def offset(self, offset):
        """ Sets the amount of DC offset to apply to the output.
        """
        self.meas.write("VOLT:OFFS %f" % offset)

    def units(self, unit):
        """ Sets the unit to be used when setting the output voltage.
        """
        if unit.find('pp') != -1:
            self.meas.write("VOLT:UNIT VPP")
        elif unit.find('rms') != -1:
            self.meas.write("VOLT:UNIT VRMS")
        elif unit.find('db') != -1:
            self.meas.write("VOLT:UNIT DBM")

    def loadImpedance(self, impedance):
        """ Sets the load impedance the device expects to be driving.
        This allows the output to be accurately set.
        """
        if type(impedance):
            self.meas.write("OUTP:LOAD %s" % impedance)
        elif impedance.find('inf') != -1:
            self.meas.write("OUTP:LOAD INF")
        elif impedance.find('min') != -1:
            self.meas.write("OUTP:LOAD MIN")
        elif impedance.find('max') != -1:
            self.meas.write("OUTP:LOAD MAX")
        else:
            print 'ERROR: Invalid impedance parameter specified'
            sys.exit()

    def dutyCycle(self, duty):
        """ Sets the ratio of on time to off time for square waves.
        """
        if self._frequency > 10000000:
            if duty >= 40 and duty <= 60:
                self.meas.write("FUNC:SQU:DCYC %f" % duty)
            else:
                print "ERROR: Above 10MHz valid duty cycle ranges are between 40% and 60%"
                sys.exit()
        else:
            if duty >= 20 and duty <= 80:
                self.meas.write("FUNC:SQU:DCYC %f" % duty)
            else:
                if self._frequency == 0:
                    print "ERROR: Max duty cycle range is between 20% and 80%"
                    print "WARNING: You specified a duty cycle without specifying a frequency"
                else:
                    print "ERROR: Max duty cycle range is between 20% and 80%"
                sys.exit()

    def output(self, enable):
        """ Enables or disables the output.
        """
        if enable:
            self.meas.write("OUTP ON")
        else:
            self.meas.write("OUTP OFF")

