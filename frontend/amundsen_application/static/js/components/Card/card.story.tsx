// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import React from 'react';

import StorySection from '../StorySection';
import Card from '.';

export default {
  title: 'Components/Cards',
};

export const Cards = () => (
  <>
    <StorySection title="Loading Card">
      <Card isLoading />
    </StorySection>
    <StorySection title="Basic Card">
      <Card
        title="Card Title"
        copy="Lorem, ipsum dolor sit amet consectetur adipisicing elit. Minima autem dolorum incidunt quaerat perspiciatis! Totam est, ab molestiae magnam quisquam eligendi enim eum, iste excepturi mollitia laboriosam cumque, vitae reiciendis."
      />
    </StorySection>
    <StorySection title="Full Card">
      <Card
        title="Card Title"
        subtitle="Card Subtitle"
        copy="Lorem, ipsum dolor sit amet consectetur adipisicing elit. Minima autem dolorum incidunt quaerat perspiciatis! Totam est, ab molestiae magnam quisquam eligendi enim eum, iste excepturi mollitia laboriosam cumque, vitae reiciendis."
      />
    </StorySection>
  </>
);

Cards.storyName = 'Cards';
