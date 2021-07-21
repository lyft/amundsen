// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { shallow } from 'enzyme';

import { ResourceReport } from 'interfaces/TableMetadata';
import TableReportsDropdown from '.';

describe('TableReportsDropdown component', () => {
  const reports: ResourceReport[] = [
    {
      name: 'test_1',
      url: 'http://test_1',
    },
    {
      name: 'test_2',
      url: 'http://test_2',
    },
  ];
  const tableReportsDropdown = shallow(
    <TableReportsDropdown resourceReports={reports} />
  );

  it('renders a resource reports dropdown', () => {
    const container = tableReportsDropdown.find('DropdownMenu');
    expect(container.exists()).toBe(true);
  });

  it('do not render resource reports', () => {
    const container = shallow(
      <TableReportsDropdown resourceReports={[]} />
    ).find('DropdownMenu');
    expect(container.exists()).toBe(false);
  });
  it('check if resource reports params are passed correctly ', () => {
    const container = tableReportsDropdown.find('DropdownMenu');
    reports.forEach((report, index) => {
      const objectContent = container.childAt(index).props().children;
      const expectedContent = JSON.stringify(
        <a target="_blank" rel="noreferrer" href={reports[index].url}>
          {reports[index].name}
        </a>
      );
      expect(JSON.stringify(objectContent)).toEqual(expectedContent);
    });
  });
});
