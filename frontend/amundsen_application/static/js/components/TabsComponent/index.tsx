// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { Tab, Tabs } from 'react-bootstrap';

import './styles.scss';

export interface TabsProps {
  tabs: TabInfo[];
  activeKey?: string;
  defaultTab?: string;
  onSelect?: (key: string) => void;
}

export interface TabInfo {
  content?: JSX.Element;
  key: string;
  title: string | JSX.Element;
}

const TabsComponent: React.FC<TabsProps> = ({
  tabs,
  activeKey,
  defaultTab,
  onSelect,
}: TabsProps) => (
  <Tabs
    id="tab"
    className="tabs-component"
    defaultActiveKey={defaultTab}
    activeKey={activeKey}
    onSelect={onSelect}
  >
    {tabs.map((tab) => (
      <Tab title={tab.title} eventKey={tab.key} key={tab.key}>
        {tab.content}
      </Tab>
    ))}
  </Tabs>
);

export default TabsComponent;
