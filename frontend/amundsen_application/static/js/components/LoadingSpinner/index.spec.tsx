// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';

import { shallow } from 'enzyme';

import LoadingSpinner from '.';

describe('LoadingSpinner', () => {
  let subject;

  beforeEach(() => {
    subject = shallow(<LoadingSpinner />);
  });

  describe('render', () => {
    it('renders img with props', () => {
      expect(subject.find('img').props()).toMatchObject({
        alt: 'loading...',
        className: 'loading-spinner',
        src: '/static/images/loading_spinner.gif',
      });
    });
  });
});
