import {
  definePlugin,
  DialogButton,
  Focusable,
  PanelSection,
  PanelSectionRow,
  ServerAPI,
  SliderField,
  staticClasses,
} from "decky-frontend-lib";
import { useEffect, useState, VFC } from "react";
import { CgLoadbarSound } from "react-icons/cg";
import { MdPlayArrow, MdPause, MdSkipNext, MdSkipPrevious, MdOutlineSmartphone, MdComputer } from 'react-icons/md'
type PlayerStatus = 'playing' | 'stopped' | 'paused'
interface sinkInput { name: string, index: number, volume: number, codec?: string, device?: { address: string, icon: string, batteryPct: number, playerStatus: PlayerStatus } };
const Content: VFC<{ serverAPI: ServerAPI }> = ({ serverAPI }) => {
  const [sinkInputs, setSinkInputs] = useState<sinkInput[]>([]);
  const fetchSinkInputs = async () => {
    const data = await serverAPI.callPluginMethod<{}, sinkInput[]>("get_sink_inputs", {});
    if (data.success) {
      data.result.sort((a, b) => {
        /* Sort sink inputs:
        // Show bluetooth devices first
        // then sort by application name
        */
        if (a.name === 'Steam') {
          return 1
        }
        if (a.device) {
          return -1;
        }
        else if (b.device) {
          return 1;
        }
        if (a.name > b.name) {
          return -1;
        }
        else {
          return 1;
        }
      })
      setSinkInputs(data.result);
    }
    else {
      console.error('[VolumeMixer] Error while calling get_sink_inputs');
    }
  }
  const setInputVolume = async (index: number, volume: number) => {
    const data = await serverAPI.callPluginMethod<{ index: number, volume: number }, boolean>("set_input_volume", { index, volume })
    if (data.success) {
      fetchSinkInputs();
    }
  }
  const sendPlayerCommand = async (address: string, command: 'TOGGLEPLAY' | 'NEXT' | 'PREVIOUS') => {
    await serverAPI.callPluginMethod("send_player_cmd", { address, command })
    if (command === 'TOGGLEPLAY') {
      const index = sinkInputs.findIndex((obj) => obj.device?.address === address);
      const playerStatus = sinkInputs[index].device?.playerStatus;
      if (playerStatus === 'playing') {
        sinkInputs[index].device!.playerStatus = 'paused';
      }
      else {
        sinkInputs[index].device!.playerStatus = 'playing';
      }
      setSinkInputs(sinkInputs)
    }
    fetchSinkInputs();
  }
  const getIconLabel = (icon: string, label: string) => {
    if (icon === 'phone') {
      return (
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'baseline' }}>
          <MdOutlineSmartphone />
          <p style={{ margin: 0 }}>{label}</p>
        </div>
      )
    }
    else if (icon === 'computer') {
      return (
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'baseline' }}>
          <MdComputer />
          <p style={{ margin: 0 }}>{label}</p>
        </div>
      )
    }
    else {
      return label
    }
  }
  useEffect(() => {
    fetchSinkInputs();
    const interval = setInterval(() => {
      fetchSinkInputs()
    }, 5000)
    return () => clearInterval(interval);
  }, [])
  return (
    <PanelSection>
      {sinkInputs.map(sinkInput => {
        let label: string | JSX.Element = sinkInput.device?.batteryPct ? `${sinkInput.name} • Battery: ${sinkInput.device.batteryPct}%` : sinkInput.name;
        if (sinkInput.device?.icon) {
          label = getIconLabel(sinkInput.device.icon, label);
        }
        return (
          <PanelSectionRow>
            <SliderField bottomSeparator="none" min={0} max={1} step={0.05} value={sinkInput.volume} label={label}
              disabled={!sinkInput.index} description={sinkInput.codec} onChange={(volume) => setInputVolume(sinkInput.index, volume)} />
            {sinkInput.device &&
              <Focusable style={{ display: 'flex', alignItems: 'center', gap: '1rem' }} flow-children="horizontal">
                <DialogButton style={{ width: '33%', minWidth: 0 }} onClick={() => sendPlayerCommand(sinkInput.device!.address, 'PREVIOUS')}><MdSkipPrevious /></DialogButton>
                <DialogButton style={{ width: '33%', minWidth: 0 }} onClick={() => sendPlayerCommand(sinkInput.device!.address, 'TOGGLEPLAY')} >{sinkInput.device.playerStatus === 'playing' ? <MdPause /> : <MdPlayArrow />}</DialogButton>
                <DialogButton style={{ width: '33%', minWidth: 0 }} onClick={() => sendPlayerCommand(sinkInput.device!.address, 'NEXT')} ><MdSkipNext /></DialogButton>
              </Focusable>
            }
          </PanelSectionRow>
        )
      }
      )}
    </PanelSection>
  );
};

export default definePlugin((serverApi: ServerAPI) => {
  return {
    title: <div className={staticClasses.Title}>Volume Mixer</div>,
    content: <Content serverAPI={serverApi} />,
    icon: <CgLoadbarSound />,
  };
});
