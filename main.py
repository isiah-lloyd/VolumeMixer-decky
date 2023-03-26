import logging
import os
from typing import TypedDict
from enum import Enum

logging.basicConfig(filename="/tmp/VolumeMixer-decky.log",
                    format='[VolumeMixer] %(asctime)s %(levelname)s %(message)s',
                    filemode='w+',
                    force=True)
logger=logging.getLogger()
logger.setLevel(logging.DEBUG) # can be changed to logging.DEBUG for debugging issues
def get_plugin_dir():
    from pathlib import Path
    return Path(__file__).parent.resolve()

def add_plugin_to_path():
    import sys

    plugin_dir = get_plugin_dir()
    directories = [["./"], ["pulsectl"], ["defaults", "pulsectl"], ["dbussy"], ["defaults", "dbussy"], ["defaults", "lib"], ["lib"]]
    for dir in directories:
        sys.path.append(str(plugin_dir.joinpath(*dir)))

def setup_environ_vars():
    os.environ['XDG_RUNTIME_DIR'] = '/run/user/1000'
    os.environ['HOME'] = '/home/deck'
add_plugin_to_path()
setup_environ_vars()
import pulsectl
import ravel
bus = ravel.system_bus()
PULSE_CLIENT_NAME = 'volumemixerdecky'
class PlayerCmds(Enum):
    TOGGLEPLAY = 1
    NEXT = 2
    PREVIOUS =3
class Plugin:
    found_bt_devices = []
    async def get_sink_inputs(self):
        sink_inputs = []
        active_bt_devices = []
        with pulsectl.Pulse(PULSE_CLIENT_NAME) as pulse:
           for sink in pulse.sink_input_list():
                volume = pulse.volume_get_all_chans(sink)
                if 'application.process.binary' in sink.proplist and sink.proplist['application.process.binary'] == 'steamwebhelper':
                    sink_inputs.append({'name': 'Steam', 'index': sink.index, 'volume': volume})
                elif 'application.name' in sink.proplist:
                    sink_inputs.append({'name': sink.proplist['application.name'], 'index': sink.index, 'volume': volume})
                elif 'device.api' in sink.proplist and sink.proplist['device.api'] == 'bluez5':
                    # Can include codec using: 'codec': sink.proplist['api.bluez5.codec'].
                    active_bt_devices.append(sink.proplist['api.bluez5.address'])
                    if sink.proplist['api.bluez5.address'] not in self.found_bt_devices:
                        self.found_bt_devices.append(sink.proplist['api.bluez5.address'])
                    try:
                        device = BluetoothDevice(sink.proplist['api.bluez5.address'])
                        sink_inputs.append({'name': sink.proplist['media.name'], 'index': sink.index, 'volume': volume, 'device': device.asdict()})
                    except Exception as e:
                        logger.info(f"Bluetooth device {sink.proplist['api.bluez5.address']} disconnected")
                        logger.error(e)
        for address in self.found_bt_devices:
            if address not in active_bt_devices:
                try:
                    device = BluetoothDevice(address)
                    sink_inputs.append({'name': device.name, 'device': device.asdict()})
                except Exception as e:
                    logger.info(f"Bluetooth device disconnected")
                    logger.error(e)
        return sink_inputs

    async def set_input_volume(self, index, volume):
        with pulsectl.Pulse(PULSE_CLIENT_NAME) as pulse:
            sink = pulse.sink_input_info(index)
            pulse.volume_set_all_chans(sink, volume)
            return True
    async def send_player_cmd(self, address: str, command: str):
        device = BluetoothDevice(address)
        device.send_player_cmd(PlayerCmds[command])

    async def _main(self):
        logger.info(f"Loaded VolumeMixer")

    async def _unload(self):
        logger.info("Unloading VolumeMixer")
        pass

class BluetoothDevice:
    class TrackDict(TypedDict):
        Title: str
        Duration: int
        Album: str
        Artist: str
    BLUEZ_BUS_NAME = 'org.bluez'
    address: str
    name: str
    icon: str
    battery_pct: int
    track: TrackDict
    src_app: str
    player_status: str
    __device_obj = None
    __media_obj = None
    def __init__(self, address: str) -> None:
        self.address = address
        self.__device_obj = bus[self.BLUEZ_BUS_NAME][self.get_device_path()]
        if self.get_device_connected() == False:
            raise Exception('Device not connected')
        self.__media_obj = bus[self.BLUEZ_BUS_NAME][self.get_media_path()].get_interface('org.bluez.MediaPlayer1')
        self.name = self.get_device_name()
        self.icon = self.get_device_icon()
        self.update()
    def update(self):
        self.battery_pct = self.get_battery_pct()
        # MediaTrack and src app are very inconsistent, commenting out for now
        # Seems like Track info is sent on the first track that's played but after skipping to next song, new track info is immediately sent and then overwritten
        # by more minimal track info (just duration). Not sure if this is an iPhone bug or BlueZ but KDE's bt media controller is also prone to this.
        # A workaround could be to subscribe to a property change signal and cache each full track update
        # Fix in BlueZ 5.64, Steam OS uses 5.63
        # Ref: https://github.com/bluez/bluez/issues/291, https://github.com/bluez/bluez/commit/2e4627c3c92ed823cb976b0a48d5463c2b187fec
        # self.track = self.get_media_track()
        # self.src_app = self.get_src_app()
        self.player_status = self.get_player_status()
    def get_device_path(self) -> str:
        objs = bus[self.BLUEZ_BUS_NAME]['/'].get_interface('org.freedesktop.DBus.ObjectManager').GetManagedObjects()
        for path, obj in objs[0].items():
            addr =  obj.get('org.bluez.Device1', {}).get('Address')
            if addr and addr[1] == self.address:
                return path
    def get_media_path(self) -> str:
        return self.__device_obj.get_interface('org.bluez.MediaControl1').Player
    def get_device_name(self) -> str:
        return self.__device_obj.get_interface('org.bluez.Device1').Name
    def get_device_icon(self) -> str:
        return self.__device_obj.get_interface('org.bluez.Device1').Icon
    def get_device_connected(self) -> bool:
        return self.__device_obj.get_interface('org.bluez.Device1').Connected
    def get_battery_pct(self) -> int | None:
        try:
            return self.__device_obj.get_interface('org.bluez.Battery1').Percentage
        except:
            logger.info(f"Battery status not supported for {self.address}")
            return None
    def get_media_track(self) -> TrackDict:
        return self.__media_obj.Track
    def get_src_app(self) -> str:
        return self.__media_obj.Name
    def get_player_status(self) -> str:
        return self.__media_obj.Status
    def send_player_cmd(self, cmd: PlayerCmds):
        logger.info(f"Sending command {cmd}")
        match cmd:
            case PlayerCmds.TOGGLEPLAY:
                if self.player_status == 'playing':
                    self.__media_obj.Pause()
                else:
                    self.__media_obj.Play()
            case PlayerCmds.NEXT:
                self.__media_obj.Next()
            case PlayerCmds.PREVIOUS:
                self.__media_obj.Previous()
    def asdict(self) -> dict:
        # return {'address': self.address, 'icon': self.icon, 'batteryPct': self.battery_pct, 'track': self.track, 'src_app': self.src_app, 'playerStatus': self.player_status}
        return {'address': self.address, 'icon': self.icon, 'batteryPct': self.battery_pct, 'playerStatus': self.player_status}

