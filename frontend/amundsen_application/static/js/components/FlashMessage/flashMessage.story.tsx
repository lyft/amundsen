// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import React from 'react';
import { storiesOf } from '@storybook/react';

import { ImageIconType } from 'interfaces/Enums';
import StorySection from '../StorySection';
import FlashMessage from '.';

const stories = storiesOf('Components/Flash Message', module);

stories.add('Flash Message', () => (
  <>
    <StorySection title="Flash Message">
      <FlashMessage
        message="Flash message text that can be short"
        onClose={() => {
          alert('message closed!');
        }}
      />
    </StorySection>
    <StorySection title="Flash Message with Icon">
      <FlashMessage
        message="Flash message text that can be short"
        iconClass={ImageIconType.ALERT}
        onClose={() => {
          alert('message closed!');
        }}
      />
    </StorySection>
  </>
));
