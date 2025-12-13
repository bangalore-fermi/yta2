import { Composition } from 'remotion';
import { My3DScene } from './Scene';

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="My3DVideo"
        component={My3DScene}
        durationInFrames={150}
        fps={30}
        width={1080}
        height={1920}
      />
    </>
  );
};
