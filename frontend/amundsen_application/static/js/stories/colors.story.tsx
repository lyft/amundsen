// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import React from 'react';
import { storiesOf } from '@storybook/react';

import StorySection from '../components/StorySection';

const stories = storiesOf('Attributes/Colors', module);

const COLOR_BLOCK_SIZE = '80px';

type ColorBlockProps = {
  color: string;
  title: string;
};

const ColorBlock: React.FC<ColorBlockProps> = ({
  color,
  title,
}: ColorBlockProps) => (
  <div style={{ margin: '20px' }}>
    <h3 className="text-subtitle-w2">{title}</h3>
    <div
      style={{
        width: COLOR_BLOCK_SIZE,
        height: COLOR_BLOCK_SIZE,
        backgroundColor: `${color}`,
        borderRadius: '3px',
      }}
    />
  </div>
);

stories.add('Colors', () => (
  <>
    <StorySection title="Brand Colors">
      <div style={{ display: 'flex' }}>
        <ColorBlock title="$brand-color-1" color="#DCDCFF" />
        <ColorBlock title="$brand-color-2" color="#BABAFF" />
        <ColorBlock title="$brand-color-3" color="#8481FF" />
        <ColorBlock title="$brand-color-4" color="#8481FF" />
        <ColorBlock title="$brand-color-5" color="#523BE4" />
      </div>
    </StorySection>
    <StorySection title="Text Colors">
      <div style={{ display: 'flex' }}>
        <ColorBlock title="$text-primary" color="#292936" />
        <ColorBlock title="$text-secondary" color="#292936" />
        <ColorBlock title="$text-tertiary" color="#9191A8" />
        <ColorBlock title="$text-placeholder" color="#9191A8" />
        <ColorBlock title="$text-inverse" color="#FFFFFF" />
      </div>
    </StorySection>
  </>
));
