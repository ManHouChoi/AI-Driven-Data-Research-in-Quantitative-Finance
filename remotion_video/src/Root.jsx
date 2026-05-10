import React from 'react';
import {Composition} from 'remotion';
import {QuantNlpRiskVideo} from './QuantNlpRiskVideo.jsx';
import {STGATNetworkSpin} from './STGATNetworkSpin.jsx';
import '@fontsource/instrument-serif/400.css';
import '@fontsource/instrument-serif/400-italic.css';
import 'katex/dist/katex.min.css';
import './style.css';

export const FPS = 24;
export const WIDTH = 1280;
export const HEIGHT = 720;
export const DURATION_IN_FRAMES = 183 * FPS;
export const STGAT_SPIN_DURATION_IN_FRAMES = 16 * FPS;

export const RemotionRoot = () => {
  return (
    <>
      <Composition
        component={QuantNlpRiskVideo}
        durationInFrames={DURATION_IN_FRAMES}
        fps={FPS}
        height={HEIGHT}
        id="QuantNlpRiskVideo"
        width={WIDTH}
      />
      <Composition
        component={STGATNetworkSpin}
        durationInFrames={STGAT_SPIN_DURATION_IN_FRAMES}
        fps={FPS}
        height={1080}
        id="STGATNetworkSpin"
        width={1920}
      />
    </>
  );
};
