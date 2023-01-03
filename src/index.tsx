import {
  definePlugin,
  PanelSection,
  PanelSectionRow,
  ServerAPI,
  SliderField,
  staticClasses,
} from "decky-frontend-lib";
import { useEffect, useState, VFC } from "react";
import { CgLoadbarSound } from "react-icons/cg";
interface sinkInput { name: string, index: number, volume: number, codec?: string };
const Content: VFC<{ serverAPI: ServerAPI }> = ({ serverAPI }) => {
  const [sinkInputs, setSinkInputs] = useState<sinkInput[]>([]);
  const fetchSinkInputs = async () => {
    const data = await serverAPI.callPluginMethod<{}, sinkInput[]>("get_sink_inputs", {});
    if (data.success) {
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
  useEffect(() => {
    fetchSinkInputs()
    const interval = setInterval(() => {
      fetchSinkInputs()
    }, 5000)
    return () => clearInterval(interval);
  }, [])
  return (
    <PanelSection>
      {sinkInputs.map(sinkInput =>
        <PanelSectionRow>
          <SliderField min={0} max={1} step={0.05} value={sinkInput.volume} label={sinkInput.name}
            description={sinkInput.codec} onChange={(volume) => setInputVolume(sinkInput.index, volume)} />
        </PanelSectionRow>
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
