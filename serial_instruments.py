import os, sys, time, serial
import numpy as np
from struct import unpack
import copy

class serialInstrument:

    prevCommand = ''
    debug = False

    def __init__(self, device, debug=False):
        self.device = device
        self.debug = debug
        try:
            self.inst = serial.Serial(device, 19200, timeout=0.01)
        except serial.serialutil.SerialException as e:
            if str(e).find('No such file or directory') != -1:
                print("ERROR: Path to serial device does not exist ("
                      + device + ")")
                sys.exit()
            elif str(e).find("Permission denied:"):
                print "Getting permission to change permissions of " + device
                os.system("gksudo chmod 777 " + device)
                try:
                    self.inst = serial.Serial(device, 19200, timeout=0.01)
                    print "Changed permissions and opened device"
                except:
                    print "Error opening device!"
                    sys.exit()
            else:
                print e
                print("Can't open path to device, have you ran: \n"
                      + "sudo chmod 777 " + device)
                sys.exit()

        tmp = self.read()
        while tmp != False:
            print "Flushing serial queue"
            print tmp
            tmp = self.read()

    def write(self, command):
        self.inst.write(command + "\n");
        if self.debug:
            print command
        if command != self.prevCommand:
            self.prevCommand = command

    def read(self):
        out = ""
        tmp = self.inst.readlines(9999)
        if self.debug:
            print tmp
        if tmp == []:
            return False
        else:
            out = ''
            for temp in tmp:
                out += temp
            while out.find('\n') == -1:
                tmp = self.inst.readlines(9999)
                for temp in tmp:
                    out += temp
            return out.rstrip('\n')


    def ask(self, command):
        self.write(command + "\n")
        tmp = self.read()
        while tmp == False:
            tmp = self.read()
        return tmp

    def getName(self):
        return self.ask("*IDN?")

    def sendReset(self):
        print "Resetting machine"
        self.inst.write("*RST")


class tek2024:

    x_incr = False
    x_num = False
    numAvg = 0
    selectedChannel = 1
    debug = False

    available_tdivs = [50,
                       25,
                       10,
                       5,
                       2.5,
                       1,
                       0.5,
                       0.25,
                       0.1,
                       0.05,
                       0.025,
                       0.01,
                       0.005,
                       0.0025,
                       0.001,
                       0.0005,
                       0.00025,
                       0.0001,
                       0.00005,
                       0.000025,
                       0.00001,
                       0.000005,
                       0.0000025,
                       0.000001,
                       0.0000005,
                       0.00000025,
                       0.0000001,
                       0.00000005,
                       0.000000025,
                       0.00000001,
                       0.000000005,
                       0.0000000025]

    available_averageSettings = [128, 64, 16, 4]

    def __init__(self, device, debug=False):
        self.inst = serialInstrument(device, debug)
        self.name = self.inst.getName()
        self.debug = debug
        if self.name == False:
            print "Shit! The machine on " + device + " isn't responding"
            sys.exit()
        else:
            print "Connected to: " + self.name.rstrip('\n')


    def status(self):
        return self.inst.ask("STB?")


    def error(self, message):
        print
        print "==========================================="
        print message
        print "==========================================="
        print

    def wait(self):
        self.write("*OPC?")
        tmp = self.read()
        while tmp != "1" and tmp != False:
            print "Waiting..." + str(tmp)
            tmp = self.read()


    def checkComplete(self):
        tmp = self.inst.ask("*OPC?")
        while tmp != "1":
            tmp = self.inst.read()


    def write(self, command):
        # Send an arbitrary command directly to the scope
        self.inst.write(command)


    def read(self):
        return self.inst.read()


    def ask(self, command):
        return self.inst.ask(command)


    def reset(self):
        # Reset the instrument
        self.inst.sendReset()


    def issueCommand(self, command, feedback, wait=True):
#         print feedback
        self.inst.write(command)
        if wait == True:
            self.checkComplete()
        # print "Success."


    def set_tScale(self, s):
        self.issueCommand("HORIZONTAL:DELAY:SCALE " + str(s), "Setting timebase to " + str(s) + " s/div")


    #===========================================================================
    # Sets or disables averaging (applies to all channels). Valid number of
    # averages are either 4,16,64 or 128. A value of 0 or False disables
    # averaging
    #
    # Arguments:
    #    averages [False | int - {4,16,64,128}]
    #===========================================================================
    def set_averaging(self, averages):
        if averages in self.available_averageSettings:
            if self.debug:
                print "Setting averaging to " + str(averages) + " samples"
            self.write("ACQuire:MODe AVERage")
            self.write("ACQuire:NUMAVg " + str(averages))
            self.numAvg = averages
        elif averages == 0 or averages == False:
            if self.debug:
                print "Disabling averaging"
            self.write("ACQuire:MODe SAMPLE")
            self.write("ACQuire:NUMAVg " + str(0))
            self.numAvg = 0
        else:
            print("Number of avearages must be in "
                  + str(self.available_averageSettings))
            sys.exit()


    def set_autoRange(self, mode):
        """
            Enables or disables autoranging for the device

            Arguments:
            mode = False | 'vertial' | 'horizontal' | 'both'
            the autoRanging mode with False being Disabled
        """
        if mode == False:
            self.issueCommand("AUTORange:STATE OFF", "Disabling auto ranging")
        elif mode.find("or") != -1:
            self.issueCommand("AUTORANGE:SETTINGS HORizontal", "Setting auto range mode to horizontal")
            self.issueCommand("AUTORange:STATE ON", "Enabling auto ranging")
        elif mode.find("er") != -1:
            self.issueCommand("AUTORANGE:SETTINGS VERTICAL", "Setting auto range mode to vertical")
            self.issueCommand("AUTORange:STATE ON", "Enabling auto ranging")
        elif mode.find("th") != -1:
            self.issueCommand("AUTORANGE:SETTINGS BOTH", "Setting auto range mode to both")
            self.issueCommand("AUTORange:STATE ON", "Enabling auto ranging")
        self.wait()


    def acquisition(self, enable):
        """
        Sets acquision parameter. Toggling this controls whether the scope acquires
        a waveform

        Arguments:
        enable [bool] Toggles waveform acquision
        """
        if enable:
            self.issueCommand("ACQuire:STATE ON", "Starting waveform acquisition")
        else:
            self.issueCommand("ACQuire:STATE OFF", "Stopping waveform acquisition")


    def get_numAcquisitions(self):
        """
        Indicates the number of acquisitions that have taken place since
        starting oscilloscope acquisition. The maximum number of acquisitions
        that can be counted is 231-1. This value is reset to zero when you
        change most Acquisition, Horizontal, Vertical, or Trigger arguments
        that affect the waveform
        """
        num = self.ask("ACQuire:NUMACq?")
        while num == False:
            num = self.read()
        try:
            num = num.split(' ')[1]
            return int(num)
        except IndexError:
            print "Uh oh, result was: " + str(num)
            return self.get_numAcquisitions()


    def waitForAcquisitions(self, num=False):
        """
        Waits in a loop until the scope has captured the required number of
        acquisitions
        """
        until = 0
#         print "Number of averages " + str(self.numAvg)
        if num == False and self.numAvg == False:
            # self.error("No number of acquisitions specified to wait")
            print "Waiting for a single aquisition to finish"
            until = 1
        elif num != False:
            until = num
            print "Waiting until " + str(until) + " acquisitions have been made"
        else:
            until = self.numAvg
            print "Waiting until " + str(until) + " acquisitions have been made"
        last = 0
        done = self.get_numAcquisitions()
        while done < until:
            if done != last:
                print "Waiting for " + str(until - done) + " acquisitions"
                last = done
            done = self.get_numAcquisitions()
            time.sleep(0.1)


    def set_hScale(self,
                   tdiv=False,
                   frequency=False,
                   cycles=False):
        """
        Set the horizontal scale according to the given parametrs.
        Parameters:
           tdiv [float] A time division in seconds (1/10 of the width of the display)
           frequency [float] Select a timebase that will capture '# cycles' of this
                             frequency
           cycles [float] Minimum number of frequency cycles to set timebase for
           used in conjunction with 'frequency' parameter
       """
        if tdiv != False:
            set_div = False
            for a_tdiv in self.available_tdivs:
                if set_div == False and float(tdiv) <= a_tdiv:
                     set_div = a_tdiv
        elif frequency != False:

            if cycles != False:
                set_div = self.find_minTdiv(frequency, cycles)
            else:
                set_div = self.find_minTdiv(frequency)

        if set_div != False:
            self.issueCommand("HORizontal:SCAle " + str(set_div),
                              "Setting horizontal scale to "
                              + str(set_div) + " s/div")
            if frequency != False and cycles != False:
                print "Window width = " + str(set_div * 10.0) + " seconds"
        else:
            print
            print "=========================================================="
            print "      WARNING: Appropriate time division not found"
            print "           Horizontal scale remains unchanged"
            print "=========================================================="
            print
        return set_div * 10.0


    def get_timeToCapture(self, frequency, cycles, averaging=1):

        if averaging == 0:
            averaging = 1

        tdiv = self.find_minTdiv(frequency, cycles)
        windowlength = float(tdiv) * 10.0
        wavelength = 1.0 / frequency

        # time if the first cycle triggers instantly and for every average
        time_min = windowlength * averaging

        # time when triggering is delayed by a full wavelength and at each
        # acquire for an average

        time_max = (windowlength * averaging) + (wavelength * averaging)
        return (time_min, time_max)


    def get_transferTime(self, mode):
        if mode == 'ASCII':
            return 8.43393707275
        elif mode == 'RPBinary':
            return 4.0
        else:
            print "Error getting transfer time"


    def find_minTdiv(self, frequency, min_cycles=2):
        # list of available time divisions on the scope
        tmp = copy.copy(self.available_tdivs)
        tmp.reverse()
        wavelength = 1.0 / float(frequency)
        min_div = (wavelength * min_cycles) / 10.0
        for tdiv in tmp:
            if min_div <= tdiv:
                return tdiv
        print
        print '==================================================='
        print('WARN: Cant fit ' + str(min_cycles) + ' cycles of '
              + str(frequency) + 'Hz into scope!')
        print('Will use ' + str(tmp[len(tmp) - 1]) + ' s/div instead,'
              + ' giving ' + str((tmp[len(tmp) - 1] * 10.0) / wavelength)
              + ' cycles')
        print '==================================================='
        print
        return tmp[len(tmp) - 1]


class channel(tek2024):

    channel = False  # Channel num
    y_offset = False
    y_mult = False
    y_zero = False
    curve_raw = False

    available_vdivs = [50.0,
                       20.0,
                       10.0,
                       5.0,
                       2.0,
                       1.0,
                       0.5,
                       0.2,
                       0.1,
                       0.05,
                       0.02]

    def __init__(self, inst, channel):
        self.inst = inst
        self.channel = channel

    def ask_properly(self, command):
        self.write(command)
        tmp = self.read()
        print tmp
        while tmp == False:
            tmp = self.read()
            print tmp
        return tmp

    def set_vScale(self, s, debug=False):
        tmp = copy.copy(self.available_vdivs)
        if debug:
            print 'asked to set vdiv to ' + str(s)
        setVdiv = False
        for vdiv in tmp:
            if s <= vdiv:
                setVdiv = vdiv
        if debug:
            print 'best match is ' + str(setVdiv)
        if setVdiv == False:
            print()
            print('===================================================')
            print('WARN: ' + str(s) + ' V/div is outside of scope range ')
            print('Will use ' + str(tmp[len(tmp) - 1]) + ' V/div instead,')
            print('===================================================')
            print()

        self.issueCommand("CH" + str(self.channel)
                          + ":SCAle " + str(setVdiv),
                          "Setting channel "
                          + str(self.channel)
                          + " scale to "
                          + str(setVdiv) + " V/div")
        self.y_mult = setVdiv

    def did_clip(self, debug=False):
        # Two points in a row must be above or below the threshold values
        # print self.curve_raw
        for i in range(len(self.curve_raw) - 2):
            sum = self.curve_raw[i] + self.curve_raw[i + 1]
            # print sum
            if sum < 10 or sum > 500:
                return True
        return False

    def get_yScale(self):
        tmp = self.ask('CH' + str(self.channel) + ':SCAle?')
        tmp = tmp.split(' ')
        return float(tmp[1])

    #==========================================================================
    # Tries to set the vertical scale appropriatly and returns data
    #==========================================================================
    def get_waveform_autoRange(self, debug=False, wait=True):
        xs, ys = self.get_waveform(False, wait=wait)
        # Check if this waveform contained clipped data
        if self.did_clip():
            clipped = True
            while clipped:
                # Increase V/div until no clipped data
                set_vdiv = self.get_yScale()
                if debug:
                    print 'set_vdiv = ' + str(set_vdiv)
                if self.available_vdivs.index(set_vdiv) > 0:
                    if debug:
                        print('Setting Y-scale on channel '
                              + str(self.channel) + ' to '
                              + str(self.available_vdivs[self.available_vdivs.index(set_vdiv) - 1])
                              + ' V/div')
                    self.set_vScale(self.available_vdivs[self.available_vdivs.index(set_vdiv) - 1])
                    self.waitForAcquisitions(self.numAvg)
                    xs, ys = self.get_waveform(debug=False)
                    clipped = self.did_clip()
                else:
                    print()
                    print('===================================================')
                    print('WARN: Scope Y-scale maxed out! THIS IS BAD!!!!!!!!!')
                    print('===================================================')
                    print()
                    clipped = False
        else:
            # Detect if decreasing V/div it will cause clipping
            tmp_max = 0
            tmp_min = 0
            for y in ys:
                if y > tmp_max:
                    tmp_max = y
                elif y < tmp_min:
                    tmp_min = y
            datarange = tmp_max - tmp_min

            set_range = self.get_yScale()
            set_window = set_range * 8.0

            # find the best (minimum no-clip) range
            best_window = 0
            tmp_range = copy.copy(self.available_vdivs)
            available_windows = map(lambda x: x * 8.0, tmp_range)

            for available_window in available_windows:
                if datarange <= (available_window * 0.90):
                    best_window = available_window

            if debug:
                print 'bestWindow = ' + str(best_window)

            # if it's not the range were already using, set it
            if best_window != set_window:
                if debug:
                    print 'Setting new range' + str(best_window / 8.0)
                self.set_vScale(best_window / 8.0)
                avgTmp = self.numAvg
                self.set_averaging(False)
                time.sleep(1)
                self.set_averaging(avgTmp)
                time.sleep(1)
                return self.get_waveform_autoRange()
        return [xs, ys]

    def set_measurementChannel(self):
        self.issueCommand("MEASUrement:IMMed:SOUrce " + str(self.channel), "Setting immediate measurement source channel to CH" + str(self.channel))

    def get_measurement(self):
        self.inst.write("MEASUrement:IMMed:VALue")
        self.inst.read()

    #===========================================================================
    # Sets waveform parameters for the waveform specified by the channel parameter
    # Arguments:
    #    channel [int - 1-4] - specifies which channel to configure
    #    encoding (optional: 'ASCII') [str - {'ASCII' , 'Binary'}] - how the waveform is to be transferred (ascii is easiest but slowest)
    #    start (optional: 0) [int - 0-2499] - data point to begin transfer from
    #    stop (optional: 2500) [int - 1-2500] - data point to stop transferring at
    #    width (optional: 2) [int] - how many bytes per datapoint to transfer
    #===========================================================================
    def set_waveformParams(self,
                           encoding='RPBinary',
                           start=0,
                           stop=2500,
                           width=1):
        self.issueCommand("DATA:SOUrce CH" + str(self.channel), "Setting data source to channel " + str(self.channel), False)
        if encoding == 'ASCII':
            self.issueCommand("DATA:ENCdg ASCIi", "Setting data encoding to ASCII", False)
            self.encoding = 'ASCII'
        else:
            self.issueCommand("DATA:ENCdg RPBinary", "Setting data encoding to RPBinary", False)
            self.encoding = 'RPBinary'
        # self.issueCommand("DATA:ENCdg RIBinary","Setting data encoding to RIBinary") #I dont know how to convert this data stream from binary into int
        self.issueCommand("DATA:STARt " + str(start), "Setting start data point to " + str(start), False)
        self.issueCommand("DATA:STOP " + str(stop), "Setting stop data point to " + str(stop), False)
        self.issueCommand("DATA:WIDTH " + str(width), "Setting of bytes to transfer per waveform point to " + str(width), False)
        self.checkComplete()


    def get_transferTime(self):
        return self.inst.get_transferTime(self.encoding)


    #===========================================================================
    # Waits until all pending operations have finished and the correct number
    # of aquisitions have occurred (if averaging) and downloads the waveform.
    # This method will download waveform setup information and construct the
    # x and y data fields
    #===========================================================================
    def get_waveform(self, debug=False, wait=True):

        if wait:
            self.waitForAcquisitions()

        self.issueCommand("DATA:SOUrce CH" + str(self.channel), "Setting data source to channel " + str(self.channel))
        if debug:
            print "Requesting waveform setup information"

        self.write("WFMPre?")

        tmp = self.read()
        while tmp == False:
            tmp = self.read()
        out = tmp

        y_offset = False
        y_mult = False
        x_incr = False
        y_zero = False
        x_num = False

        out = out.split(';')
        for line in out:
            tmp = line.split(' ')
            if tmp[0] == ':WFMPRE:BYT_NR':
                if debug:
                    print 'Bytes per point: ' + tmp[1]
            elif tmp[0] == 'BIT_NR':
                if debug:
                    print 'Bits per point: ' + tmp[1]
            elif tmp[0] == 'ENCDG':
                if tmp[1] == 'ASC':
                    if debug:
                        print 'Data encoding: ASCII'
                    encoding = 'ascii'
                elif tmp[1] == 'BIN':
                    if debug:
                        print 'Data encoding: Binary'
                    encoding = 'binary'
            elif tmp[0] == 'N,':
                if debug:
                    print 'Volume of data: ' + tmp[1] + ' points'
                x_num = int(tmp[1])
            elif tmp[0] == 'XINCR':
                if debug:
                    print 'Time between points: ' + tmp[1]
                x_incr = float(tmp[1])
            elif tmp[0] == 'XUNIT':
                if debug:
                    if tmp[1] == '"s"':
                        print 'X axis unit: Seconds'
                    elif tmp[1] == '"Hz"':
                        print 'X axis unit: Hertz'
            elif tmp[0] == 'XZERO':
                if debug:
                    print 'Trigger occurred at ' + tmp[1] + ' V from 1st data point'
            elif tmp[0] == 'YMULT':
                if debug:
                    print 'Y axis muitiplyer: ' + tmp[1]
                y_mult = float(tmp[1])
            elif tmp[0] == 'YZERO':
                if debug:
                    print 'Y axis zero: ' + tmp[1]
                y_zero = float(tmp[1])
            elif tmp[0] == 'YOFF':
                try:
                    y_offset = float(tmp[1])
                    if debug:
                        print 'Y axis waveform offset: ' + tmp[1]
                except ValueError:
                    y_offset = 0.00
                    if debug:
                        print 'Y axis waveform offset ignored'

        if y_offset == False:
            print
            print "======================================================"
            print "WARNING: Y-offset parameter was not returned by scope"
            print "======================================================"
            print
        if y_mult == False:
            print
            print "======================================================"
            print "WARNING: Y-multiplyer parameter was not returned by scope"
            print "======================================================"
            print
        if x_incr == False:
            print
            print "======================================================"
            print "WARNING: X-increment parameter was not returned by scope"
            print "======================================================"
            print
        if y_zero == False:
            y_zero = 0

        print "Requsting waveform"
        self.write("CURVE?")
        out = ''
        tmp = self.read()
        while tmp == False:
            tmp = self.read()

        if encoding == 'binary':
            tmp = tmp.split(':CURVE #42500')[1]
            data = np.array(unpack('>%sB' % (len(tmp)), tmp))
        elif encoding == 'ascii':
            out = tmp.split(":CURVE ")[1]
            data = out.split(',')
        else:
            print "Error: Waveform encoding was not understood, exiting!"
            sys.exit()

        self.curve_raw = data
        data_y = map(lambda x: ((int(x) - y_offset) * y_mult) + y_zero, data)
        data_x = map(lambda x: x * x_incr , range(len(data_y)))
        if x_num != False and x_num != len(data_y):
            print
            print "======================================================"
            print "WARNING: Data payload was stated as " + str(self.x_num) + " points"
            print "but " + str(len(data_x)) + " points were returned"
            print "======================================================"
            print

        self.y_offset = y_offset
        self.y_mult = y_mult
        self.x_incr = x_incr
        self.y_zero = y_zero

        if self.did_clip() == True:
            print
            print "======================================================="
            print "WARNING: Data payload possibly contained clipped points"
            print "======================================================="
            print

        return [data_x, data_y]



