// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';

import { shallow } from 'enzyme';

import { ResourceType } from 'interfaces';
import DashboardListItem from './DashboardListItem';
import FeatureListItem from './FeatureListItem';
import TableListItem from './TableListItem';
import UserListItem from './UserListItem';
import ResourceListItem, { ListItemProps } from '.';

describe('ResourceListItem', () => {
  let props: ListItemProps;
  let subject;

  beforeEach(() => {
    props = {
      logging: { source: 'src', index: 0 },
      item: { type: ResourceType.table },
    };
    // eslint-disable-next-line react/jsx-props-no-spreading
    subject = shallow(<ResourceListItem {...props} />);
  });

  describe('render', () => {
    it('renders TableListItem with correct props', () => {
      expect(subject.find(TableListItem).props()).toMatchObject({
        logging: props.logging,
        table: props.item,
      });
    });

    it('renders UserListItem with correct props', () => {
      props.item.type = ResourceType.user;
      subject.setProps(props);
      expect(subject.find(UserListItem).props()).toMatchObject({
        logging: props.logging,
        user: props.item,
      });
    });

    it('renders DashboardListItem with correct props', () => {
      props.item.type = ResourceType.dashboard;
      subject.setProps(props);
      expect(subject.find(DashboardListItem).props()).toMatchObject({
        logging: props.logging,
        dashboard: props.item,
      });
    });

    it('renders FeatureListItem with correct props', () => {
      props.item.type = ResourceType.feature;
      subject.setProps(props);
      expect(subject.find(FeatureListItem).props()).toMatchObject({
        logging: props.logging,
        feature: props.item,
      });
    });

    it('renders nothing if invalid props.item.type', () => {
      // @ts-ignore
      props.item.type = 'not a valid type';
      subject.setProps(props);
      expect(subject.props().children).toBeFalsy();
    });
  });
});
