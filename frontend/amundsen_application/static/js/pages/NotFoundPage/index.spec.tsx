// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import * as DocumentTitle from 'react-document-title';

import { shallow } from 'enzyme';

import Breadcrumb from 'components/Breadcrumb';
import NotFoundPage from '.';

describe('NotFoundPage', () => {
  let subject;
  beforeEach(() => {
    subject = shallow(<NotFoundPage />);
  });

  it('renders DocumentTitle w/ correct title', () => {
    expect(subject.find(DocumentTitle).props().title).toEqual(
      '404 Page Not Found - Amundsen'
    );
  });

  it('renders Breadcrumb to homepage', () => {
    expect(subject.find(Breadcrumb).props()).toMatchObject({
      path: '/',
      text: 'Home',
    });
  });

  it('renders header correct text', () => {
    expect(subject.find('h1').text()).toEqual('404 Page Not Found');
  });

  it('renders image icon', () => {
    expect(subject.find('img').props()).toMatchObject({
      className: 'icon icon-alert',
    });
  });
});
