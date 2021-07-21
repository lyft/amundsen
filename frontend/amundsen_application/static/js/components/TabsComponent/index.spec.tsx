// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';

import { shallow } from 'enzyme';

import { Tab, Tabs } from 'react-bootstrap';
import TabsComponent, { TabsProps } from '.';

describe('Tabs', () => {
  let props: TabsProps;
  let tabContent: JSX.Element;
  let subject;

  beforeEach(() => {
    tabContent = <div>I am content</div>;
    props = {
      activeKey: 'activeTab',
      defaultTab: 'defaultTab',
      onSelect: jest.fn(),
      tabs: [
        {
          content: tabContent,
          key: 'defaultTab',
          title: 'Tabby Tab',
        },
        {
          content: tabContent,
          key: 'defaultTab2',
          title: 'Tabby Tab2',
        },
      ],
    };
    subject = shallow(<TabsComponent {...props} />);
  });

  describe('render', () => {
    it('renders Tabs with correct props', () => {
      expect(subject.find(Tabs).props()).toMatchObject({
        id: 'tab',
        className: 'tabs-component',
        defaultActiveKey: props.defaultTab,
        activeKey: props.activeKey,
        onSelect: props.onSelect,
      });
    });

    it('renders Tab for each props.tabs', () => {
      expect(subject.find(Tab)).toHaveLength(2);
    });

    it('passes correct props to Tab', () => {
      expect(subject.find(Tab).at(0).props()).toMatchObject({
        eventKey: props.tabs[0].key,
        title: props.tabs[0].title,
      });
    });

    it('passes correct content to Tab', () => {
      expect(subject.find(Tab).at(0).props().children).toEqual(tabContent);
    });
  });
});
