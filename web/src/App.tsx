import { useApp } from './state';
import { TouristShell } from './components/Shell';
import { CallScreen } from './screens/CallScreen';
import { WaveScreen } from './screens/WaveScreen';
import { TripsScreen } from './screens/TripsScreen';
import { ControlScreen } from './screens/ControlScreen';
import { ModelScreen } from './screens/ModelScreen';

export function App() {
  const { route } = useApp();
  if (route.path === 'control') return <ControlScreen />;
  if (route.path === 'model') return <ModelScreen />;
  const key = `${route.path}?${route.params.toString()}`;
  return (
    <TouristShell>
      {route.path === 'wave' ? <WaveScreen key={key} /> : route.path === 'trips' ? <TripsScreen /> : <CallScreen key={key} />}
    </TouristShell>
  );
}
