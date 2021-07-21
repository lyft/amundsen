// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import React from 'react';
import { Welcome } from '@storybook/react/demo';

import StorySection from '../components/StorySection';

export default {
  title: 'Overview/Introduction',
  component: Welcome,
};

export const Introduction = () => (
  <>
    <StorySection
      title="Welcome to Amundsen's Component Library!"
      text={
        <h3 className="text-subtitle-w2">
          A development area for developing new{' '}
          <strong>presentational components</strong>
        </h3>
      }
    >
      <p>
        Do you ever miss having a “workshop” to develop new components before
        hooking them with the real data? Look no more, here is the place!
      </p>
      <p>In this environment you can:</p>
      <ul>
        <li>Quickly develop new components for using them on Amundsen</li>
        <li>See what components are available already</li>
        <li>Be consistent with the Amundsen styling</li>
        <li>Create manual tests for your components</li>
        <li>
          Avoid the whole syncing thing while developing your presentational
          components
        </li>
        <li>
          Clear the path to eventually move reusable components into the Data
          Product Language (DPL)
        </li>
        <li>Prototype something really quick to show around</li>
      </ul>
    </StorySection>
  </>
);
