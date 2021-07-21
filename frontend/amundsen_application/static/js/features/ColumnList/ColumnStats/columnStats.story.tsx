// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import React from 'react';
import { storiesOf } from '@storybook/react';

import StorySection from 'components/StorySection';
import ColumnStats from '.';

import TestDataBuilder from './testDataBuilder';

const dataBuilder = new TestDataBuilder();

const { stats: fourStats } = dataBuilder.withFourStats().build();
const { stats: threeStats } = dataBuilder.withThreeStats().build();
const { stats: eightStats } = dataBuilder.withEightStats().build();

const stories = storiesOf('Components/ColumnStats', module);

stories.add('Column Stats', () => (
  <>
    <StorySection title="with four stats">
      <ColumnStats stats={fourStats} />
    </StorySection>
    <StorySection title="with three stats">
      <ColumnStats stats={threeStats} />
    </StorySection>
    <StorySection title="with eight stats">
      <ColumnStats stats={eightStats} />
    </StorySection>
  </>
));
