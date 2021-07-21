// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import React from 'react';
import { withKnobs, object } from '@storybook/addon-knobs';

import { IconSizes } from 'interfaces';
import StorySection from '../StorySection';
import InfoButton from '.';

export const InfoButtonStory = () => (
  <>
    <StorySection title="Info Button">
      <InfoButton
        infoText={object('InfoButton infoText', 'Some info text to share')}
        title={object('InfoButton title', 'Popover Title')}
      />
    </StorySection>
    <StorySection title="Info Button to left">
      <InfoButton
        infoText={object(
          'InfoButton infoText to left title',
          'Some info text to share'
        )}
        title={object('InfoButton to left title', 'Popover Title')}
        placement={object('InfoButton placement to left', 'left')}
      />
    </StorySection>
    <StorySection title="Info Button small size">
      <InfoButton
        infoText={object(
          'InfoButton infoText small size title',
          'Some info text to share'
        )}
        title={object('InfoButton small size title', 'Popover Title')}
        placement={object('InfoButton small size placement', 'left')}
        size={IconSizes.SMALL}
      />
    </StorySection>
  </>
);
InfoButtonStory.storyName = 'Info Button';

export default {
  title: 'Components/Buttons',
  component: InfoButton,
  decorators: [withKnobs],
};
