// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';

import { mount } from 'enzyme';

import ResourceStatusMarker, { StatusMarkerProps } from '.';

const setup = (propsOverrides?: Partial<StatusMarkerProps>) => {
  const props = {
    stateText: '',
    succeeded: false,
    ...propsOverrides,
  };
  const wrapper = mount<typeof ResourceStatusMarker>(
    // eslint-disable-next-line react/jsx-props-no-spreading
    <ResourceStatusMarker {...props} />
  );
  return { props, wrapper };
};

describe('RunStateContainer', () => {
  describe('Succeded', () => {
    it('renders SuccessState when lastRunState successful', () => {
      const { wrapper } = setup({
        stateText: 'Succeeded',
        succeeded: true,
      });

      const expected = 1;
      const actual = wrapper.find('.success').length;

      expect(actual).toEqual(expected);
    });
  });
  describe('Failed', () => {
    const { wrapper } = setup({
      stateText: 'Failed',
    });
    it('renders MissedState when lastRunState failed', () => {
      const expected = 1;
      const actual = wrapper.find('.failure').length;

      expect(actual).toEqual(expected);
    });
    it('renders failure icon', () => {
      const expected = 1;
      const actual = wrapper.find('.failure-icon').length;

      expect(expected).toEqual(actual);
    });
  });
});
