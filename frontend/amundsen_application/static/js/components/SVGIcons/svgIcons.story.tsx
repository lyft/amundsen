// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import React from 'react';
import { withKnobs, object } from '@storybook/addon-knobs';

import StorySection from '../StorySection';
import {
  AlertIcon,
  DownIcon,
  UpIcon,
  RightIcon,
  LeftIcon,
  InformationIcon,
} from '.';

export const SVGIcons = () => (
  <>
    <StorySection title="Alert">
      <AlertIcon stroke={object('Alert stroke', 'currentColor')} />
    </StorySection>
    <StorySection title="Down">
      <DownIcon fill={object('DownIcon fill', '#9191A8')} />
    </StorySection>
    <StorySection title="Up">
      <UpIcon fill={object('UpIcon fill', '#9191A8')} />
    </StorySection>
    <StorySection title="Right">
      <RightIcon fill={object('RightIcon fill', '#9191A8')} />
    </StorySection>
    <StorySection title="Left">
      <LeftIcon fill={object('LeftIcon fill', '#9191A8')} />
    </StorySection>
    <StorySection title="Information">
      <InformationIcon fill={object('InformationIcon fill', '#9191A8')} />
    </StorySection>
  </>
);
SVGIcons.storyName = 'SVG Icons';

export default {
  title: 'Attributes/Iconography',
  component: AlertIcon,
  decorators: [withKnobs],
};
