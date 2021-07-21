// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { shallow } from 'enzyme';
import AvatarLabel from 'components/AvatarLabel';
import { tableMetadata } from '../../../fixtures/metadata/table';
import LineageLink from './index';

describe('LineageLink', () => {
  let wrapper;
  let props;
  beforeAll(() => {
    props = {
      tableData: tableMetadata,
    };
    wrapper = shallow<typeof LineageLink>(<LineageLink {...props} />);
  });

  it('should render a link', () => {
    expect(wrapper.find('a').exists).toBeTruthy();
  });

  it('should render an avatarLabel', () => {
    expect(wrapper.find(AvatarLabel).exists).toBeTruthy();
  });
});
