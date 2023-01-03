import logging
import subprocess
import platform
import os

logging.basicConfig(filename="/tmp/VolumeMixer-decky.log",
                    format='[VolumeMixer] %(asctime)s %(levelname)s %(message)s',
                    filemode='w+',
                    force=True)
logger=logging.getLogger()
logger.setLevel(logging.INFO) # can be changed to logging.DEBUG for debugging issues
def get_plugin_dir():
    from pathlib import Path
    return Path(__file__).parent.resolve()

def add_plugin_to_path():
    import sys

    plugin_dir = get_plugin_dir()
    directories = [["./"], ["pulsectl"], ["defaults", "pulsectl"]]
    for dir in directories:
        sys.path.append(str(plugin_dir.joinpath(*dir)))
def setup_environ_vars():
    os.environ['XDG_RUNTIME_DIR'] = '/run/user/1000'
    os.environ['HOME'] = '/home/deck'
add_plugin_to_path()
setup_environ_vars()
import pulsectl

PULSE_CLIENT_NAME = 'volumemixerdecky'
class Plugin:
    async def get_sink_inputs(self):
        sink_inputs = []
        with pulsectl.Pulse(PULSE_CLIENT_NAME) as pulse:
           for sink in pulse.sink_input_list():
                volume = pulse.volume_get_all_chans(sink)
                if 'application.process.binary' in sink.proplist and sink.proplist['application.process.binary'] == 'steamwebhelper':
                    sink_inputs.append({'name': 'Steam', 'index': sink.index, 'volume': volume})
                elif 'application.name' in sink.proplist:
                    sink_inputs.append({'name': sink.proplist['application.name'], 'index': sink.index, 'volume': volume})
                elif 'api.bluez5.codec' in sink.proplist:
                    # Can include codec using: 'codec': sink.proplist['api.bluez5.codec'].
                    sink_inputs.append({'name': sink.proplist['media.name'], 'index': sink.index, 'volume': volume})
        return sink_inputs

    async def set_input_volume(self, index, volume):
        with pulsectl.Pulse(PULSE_CLIENT_NAME) as pulse:
            sink = pulse.sink_input_info(index);
            logger.info(f"Setting volume for {sink.proplist['media.name']} to {volume}")
            pulse.volume_set_all_chans(sink, volume)
            return True

    async def _main(self):
        logger.info(f"Loaded VolumeMixer")

    async def _unload(self):
        logger.info("Unloading VolumeMixer")
        pass
