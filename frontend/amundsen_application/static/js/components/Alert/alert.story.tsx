// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import React from 'react';
import { storiesOf } from '@storybook/react';

import StorySection from '../StorySection';
import Alert from '.';

const stories = storiesOf('Components/Alert', module);

stories.add('Alert', () => (
  <>
    <StorySection title="Alert">
      <Alert
        message="Alert text that can be short"
        onAction={() => {
          alert('action executed!');
        }}
      />
    </StorySection>
    <StorySection title="Alert with text link">
      <Alert
        message={
          <span>
            Alert text that has a <a href="https://lyft.com">link</a>
          </span>
        }
      />
    </StorySection>
    <StorySection title="Alert with Action as button">
      <Alert
        message="Alert text that can be short"
        actionText="Action Text"
        onAction={() => {
          alert('action executed!');
        }}
      />
    </StorySection>
    <StorySection title="Alert with Action as link">
      <Alert
        message="Alert text that can be short"
        actionText="Action Text"
        actionHref="http://www.lyft.com"
      />
    </StorySection>
    <StorySection title="Alert with Action as custom link">
      <Alert
        message="Alert text that can be short"
        actionLink={
          <a className="test-action-link" href="http://testSite.com">
            Custom Link
          </a>
        }
      />
    </StorySection>
    <StorySection title="Alert with long text">
      <Alert message="Lorem ipsum dolor sit amet consectetur adipisicing elit. Laboriosam perspiciatis non ipsa officia expedita magnam mollitia, excepturi iste eveniet qui nisi eum illum, quas voluptas, reprehenderit quam molestias cum quisquam!" />
    </StorySection>
    <StorySection title="Alert with long text and action">
      <Alert
        actionText="Action Text"
        onAction={() => {
          alert('action executed!');
        }}
        message="Lorem ipsum dolor sit amet consectetur adipisicing elit. Laboriosam perspiciatis non ipsa officia expedita magnam mollitia, excepturi iste eveniet qui nisi eum illum, quas voluptas, reprehenderit quam molestias cum quisquam!"
      />
    </StorySection>
  </>
));
