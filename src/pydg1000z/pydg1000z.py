from labdevices.exceptions import CommunicationError_ProtocolViolation
from labdevices.exceptions import CommunicationError_Timeout
from labdevices.exceptions import CommunicationError_NotConnected

from labdevices.functiongenerator import FunctionGenerator, FunctionGeneratorWaveform, FunctionGeneratorModulation
from labdevices.scpi import SCPIDeviceEthernet
import atexit
import re

from time import sleep

import socket

import logging
import datetime
from enum import Enum, IntEnum

class PYDG1000Z(FunctionGenerator):
    def __init__(
        self,

        address=None,
        port=5555,
    ):
        self._scpi = SCPIDeviceEthernet(address, port, None)
        self._usedConnect = False
        self._usedContext = False
        self._channel_waveform ={}
        self._channel_waveform[FunctionGeneratorWaveform.SINE] = "SIN"
        self._channel_waveform[FunctionGeneratorWaveform.SQUARE] = "SQU"
        self._channel_waveform[FunctionGeneratorWaveform.RAMP] = "RAMP"
        self._channel_waveform[FunctionGeneratorWaveform.TRGL] = "TRI"
        self._channel_waveform[FunctionGeneratorWaveform.DC] = "DC"
        self._channel_waveform[FunctionGeneratorWaveform.WHITENOISE] = "NOIS"
        

        super().__init__(
            nchannels = 2,
            freqrange = ( 1.0e-6, 60.001e6 ),
            amplituderange = ( 1.0e-3, 5 ),
            offsetrange = ( -5, 5 ),
            
            arbitraryWaveforms = False,
            hasFrequencyCounter = False,
            
            arbitraryWaveformLength = ( 0, 0 ),
            arbitraryWaveformMinMax = ( 0, 0 ),
            arbitraryNormalizeInDriver = False,
            
            supportedWaveforms = [
                FunctionGeneratorWaveform.SINE, 
                FunctionGeneratorWaveform.SQUARE, 
                FunctionGeneratorWaveform.TRGL,
                FunctionGeneratorWaveform.RAMP,
                FunctionGeneratorWaveform.DC,
                FunctionGeneratorWaveform.WHITENOISE
            ],
            supportedTriggerModes = [],
            supportedModulations = [],
            commandRetries = 3
        )

        atexit.register(self.__close)

    # Connection handling

    def _connect(self, address = None, port = None):
        if self._scpi.connect(address, port):
            # Ask for identity and verify ...
            idnString = self._idn()
            if not idnString.startswith("Rigol Technologies,DG10"):
                self._disconnect()
                raise ValueError(f"Unsupported device, identifies as {idnString}")

            idnParts = idnString.split(",")
            self._id = {
                'manufacturer' : idnParts[0],
                'product'      : idnParts[1],
                'serial'       : idnParts[2],
                'version'      : idnParts[3]
            }
        return True

    def _disconnect(self):
        self._scpi.disconnect()

    def _isConnected(self):
        return self._scpi.isConnected()

    # Context management

    def __enter__(self):
        if self._usedConnect:
            raise ValueError("Cannot use context management (with) on a connected port")

        # Run our internal connect method ...
        self._connect()

        self._usesContext = True
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.__close()
        self._usesContext = False
    def __close(self):
        atexit.unregister(self.__close)
        if self._scpi.isConnected():
            self._off()
            self._disconnect()

    # Commands

    def _idn(self):
        return self._scpi.scpiQuery("*IDN?")

    def _identify(self):
        resp = self._idn()
        if resp is None:
            return None

        idnParts = resp.split(",")

        return {
            'manufacturer' : idnParts[0],
            'product'      : idnParts[1],
            'serial'       : idnParts[2],
            'version'      : idnParts[3]
        }

    def _off(self):
        pass

    def _set_channel_enabled(self, channel, enabled):
        if (channel < 0) or (channel > 1):
            raise ValueError("Invalid channel number for DG1000Z")
        if enabled:
            self._scpi.scpiCommand(f":OUTP{channel+1}:LOAD 50")
            self._scpi.scpiCommand(f":OUTP{channel+1} ON")
        else:
            self._scpi.scpiCommand(f":CHAN{channel+1}:DISP INF")
            self._scpi.scpiCommand(f":OUTP{channel+1} OFF")

    def _is_channel_enabled(self, channel):
        if (channel < 0) or (channel > self.nchannels):
            raise ValueError("Invalid channel number for DG1000Z")

        resp = self._scpi.scpiQuery(f":CHAN{channel+1}:DISP?")
        try:
            resp = int(resp)
            if resp == 1:
                return True
            elif resp == 0:
                return False
        except:
            pass

        raise CommunicationError_ProtocolViolation("Failed to query enabled status of channel")
            
    def _set_channel_waveform(self, channel, waveform, arbitrary = None):
        if not (waveform in self._channel_waveform.keys()):
            raise ValueError("Invalid waveform specified")

        self._scpi.scpiCommand(f":SOUR{channel+1}:FUNC: {self._channel_waveform[waveform]}")
        self._scpi.scpiCommand(f":APPL:{self._channel_waveform[waveform]}")
        
    def _get_channel_waveform(self, channel):
        resp = self._scpi.scpiQuery(f":SOUR{channel+1}:FUNC?")
        return resp

    def _set_channel_frequency(self, channel, freq_Hz):
        self._scpi.scpiCommand(f":SOUR{channel+1}:FREQ {freq_Hz}")

    def _get_channel_frequency(self, channel):
        resp = self._scpi.scpiQuery(f":SOUR{channel+1}:FREQ?")
        return resp
    
    def _set_channel_phase(self, channel, phase_deg:float):
        """ Input is in degrees """
        self._scpi.scpiCommand(f":SOUR{channel+1}:PHAS {phase_deg}")

    def _get_channel_phase(self, channel):
        resp = self._scpi.scpiQuery(f":SOUR{channel+1}:PHAS?")
        return resp
    
    def _set_channel_amplitude(self, channel, amp_Vpp: float):
        """ Input is in volts, max is 10Vpp"""
        print(f"Setting amp to {amp_Vpp}")
        self._scpi.scpiCommand(f":SOUR{channel+1}:VOLT:AMPL {amp_Vpp}")

    def _get_channel_amplitude(self, channel):
        resp = self._scpi.scpiQuery(f":SOUR{channel+1}:VOLT:AMPL?")
        return resp
    
    def _set_channel_offset(self, channel, offset_V: float):
        """ Input is in volts"""
        self._scpi.scpiCommand(f":SOUR{channel+1}:VOLT:OFFS {offset_V}")
        
    def _get_channel_offset(self, channel):
        resp = self._scpi.scpiQuery(f":SOUR{channel+1}:VOLT:OFFS?")
        return resp
    
    def set_coupling(self, on=True):
        """ Input is in volts"""
        if on:
            self._scpi.scpiCommand(f":COUP ON")
        else:
            self._scpi.scpiCommand(f":COUP OFF")
        
    def get_coupling(self):
        resp = self._scpi.scpiQuery(f":COUP?")
        return resp

    def set_model(self):
        """ Input is in volts"""
        self._scpi.scpiCommand(f":PROJ:STAT MODEL,DG1062Z")
        readData = ""        
        while True:
            dataBlock = self._socket.recv(4096*10)
            dataBlockStr = dataBlock.decode("utf-8")
            readData = readData + dataBlockStr
            if dataBlockStr[-1] == '\n':
                break
            
    
    def set_serial_number(self, number):
        """ Input is in volts"""
        self._scpi.scpiCommand(f":PROJ:STAT SN,{number}")
        readData = ""        
        while True:
            dataBlock = self._socket.recv(4096*10)
            dataBlockStr = dataBlock.decode("utf-8")
            readData = readData + dataBlockStr
            if dataBlockStr[-1] == '\n':
                break
            
        