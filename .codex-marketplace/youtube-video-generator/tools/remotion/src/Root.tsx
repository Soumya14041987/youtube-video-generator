import React from 'react';
import {Composition} from 'remotion';
import {Episode, EpisodeProps} from './Episode';

// Shown only in Remotion Studio when no props file is given. Real episodes pass --props=<file>.
const demo: EpisodeProps = {
  fps: 30,
  width: 1280,
  height: 720,
  totalSeconds: 6,
  audio: '',
  badge: 'SERIES  |  EPISODE 01',
  follow: [],
  quiz: null,
  scenes: [
    {n: 1, start: 0, end: 6, title: 'Demo', lines: [], scene: {type: 'title', headline: ['YOUR TOPIC', 'HERE'], subtitle: 'Preview in Remotion Studio'}},
  ],
};

export const Root: React.FC = () => (
  <Composition
    id="Episode"
    component={Episode}
    durationInFrames={180}
    fps={30}
    width={1280}
    height={720}
    defaultProps={demo}
    calculateMetadata={({props}) => ({
      durationInFrames: Math.max(1, Math.round(props.totalSeconds * props.fps)),
      fps: props.fps,
      width: props.width,
      height: props.height,
    })}
  />
);
