# Rigol DG1000Z arbitrary waveform generator Python library (unofficial)

![A Rigol DG1000Z setup](/doc/DG1000Z.jpg)

A simple Python library and utility to control Rigol DG1000Z arbitrary waveform generator. This library implements the [functiongenerator](https://github.com/tspspi/pylabdevs/src/labdevices/functiongenerator.py) class from
the [labdevices](https://github.com/tspspi/pylabdevs) package which exposes the public interface.

## Installing 

There is a PyPi package that can be installed using

```
pip install pydg1000z
```

## Simple example to generate waveforms:

```python
import time
from pydg1000z import *
from labdevices.scpi import SCPIDeviceEthernet

with PYDG1000Z(address="10.0.0.124") as awg:

  awg.set_channel_enabled(0, True)
  awg.set_channel_enabled(1, True)

  awg.set_channel_frequency(0, 600000)
  awg.set_channel_waveform(channel=0, waveform=FunctionGeneratorWaveform.SINE)
  awg.set_channel_waveform(channel=1, waveform=FunctionGeneratorWaveform.SINE)

  awg.set_channel_amplitude(0, 5.0)
  awg.set_coupling(True)

  awg.set_channel_frequency(0, 1000)
  time.sleep(10)

  awg.set_channel_frequency(0, 10000)

  print("Press Key to switch off")
  input()

  awg.set_channel_enabled(0, False)
  awg.set_channel_enabled(1, False)
```

## Supported waveforms

* FunctionGeneratorWaveform.SINE :
* FunctionGeneratorWaveform.SQUARE :
* FunctionGeneratorWaveform.RAMP :
* FunctionGeneratorWaveform.TRGL :
* FunctionGeneratorWaveform.DC :
* FunctionGeneratorWaveform.WHITENOISE : 

`
For more detailed information about waveforms see ***:SOURce:FUNCtion:SHAPe*** [DG1000Z Progamming Guide (Feb 2014)](/doc/DG1000Z_ProgrammingGuide_EN.pdf) section 3.17
`

## Supported methods

* ```identify()```
* Connection management (when not using ```with``` context management):
   * ```connect()```
   * ```disconnect()```
* ```set_channel_enable(channel, enabled)```
* ```is_channel_enabled(channel)```
* ```set_channel_waveform(channel, waveform[, arbitrary])```
* ```get_channel_waveform(channel)```
* ```set_channel_frequency(channel, freq_Hz)```
* ```get_channel_frequency(channel)```
* ```set_channel_phase(channel, phase_deg:float)```
* ```get_channel_phase(channel)```
* ```set_channel_amplitude(channel, amp_Vpp:float)```
* ```get_channel_amplitude(channel)```
* ```set_channel_offset(channel, )```
* ```get_channel_offset(channel)```
* ```set_coupling(on)```
* ```get_coupling()```


