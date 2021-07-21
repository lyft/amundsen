// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import React from 'react';
import { storiesOf } from '@storybook/react';

import StorySection from 'components/StorySection';
import ExpandableUniqueValues from '.';

// import TestDataBuilder from './testDataBuilder';

// const dataBuilder = new TestDataBuilder();

// const { stats: fourStats } = dataBuilder.withFourStats().build();
// const { stats: threeStats } = dataBuilder.withThreeStats().build();
// const { stats: eightStats } = dataBuilder.withEightStats().build();

const defaultUniqueValues = [
  {
    value: '2020-11-28',
    count: 2418200,
  },
  {
    value: '2020-11-26',
    count: 2265000,
  },
  {
    value: '2020-12-01',
    count: 1983000,
  },
  {
    value: '2020-11-27',
    count: 1903500,
  },
  {
    value: '2020-11-30',
    count: 1520800,
  },
  {
    value: '2020-11-29',
    count: 1286900,
  },
  {
    value: '2020-11-25',
    count: 281100,
  },
];

const stories = storiesOf('Components/ExpandableUniqueValues', module);

stories.add('Expandable Unique Values', () => (
  <>
    <StorySection title="with seven value/count pairs">
      <ExpandableUniqueValues uniqueValues={defaultUniqueValues} />
    </StorySection>
  </>
));
