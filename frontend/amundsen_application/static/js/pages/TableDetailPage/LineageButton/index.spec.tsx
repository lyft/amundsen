// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { MemoryRouter } from 'react-router-dom';
import { mount } from 'enzyme';

import * as NavigationUtils from 'utils/navigationUtils';
import { TableMetadata } from 'interfaces/TableMetadata';

import LineageButton from '.';

let mockTableLineageEnabled = true;

jest.mock('config/config-utils', () => ({
  isTableLineagePageEnabled: () => mockTableLineageEnabled,
}));

describe('LineageButton', () => {
  const setup = (tableDataOverrides?: Partial<TableMetadata>) => {
    const mockMetadata = {
      badges: [],
      cluster: 'cluster',
      columns: [],
      dashboards: [],
      database: 'database',
      is_editable: false,
      is_view: false,
      key: '',
      schema: 'schema',
      name: 'table_name',
      last_updated_timestamp: 12321312321,
      description: '',
      table_writer: {
        application_url: '',
        description: '',
        id: '',
        name: '',
      },
      partition: {
        is_partitioned: true,
        key: 'partition_key',
        value: 'partition_value',
      },
      table_readers: [],
      source: {
        source: '',
        source_type: '',
      },
      resource_reports: [],
      watermarks: [],
      programmatic_descriptions: {},
      ...tableDataOverrides,
    };

    const wrapper = mount(
      <MemoryRouter>
        <LineageButton tableData={mockMetadata} />
      </MemoryRouter>
    );
    return {
      props: { tableData: mockMetadata },
      wrapper,
    };
  };

  describe('render', () => {
    beforeEach(() => {
      mockTableLineageEnabled = true;
    });

    it('null component if lineage is not enabled', () => {
      mockTableLineageEnabled = false;
      const { wrapper } = setup();
      expect(wrapper.find('Link').exists()).toBe(false);
    });

    it('renders correctly', () => {
      const builderSpy = jest.spyOn(NavigationUtils, 'buildLineageURL');
      const { props, wrapper } = setup();
      expect(builderSpy).toHaveBeenCalledWith(props.tableData);
      expect(wrapper.find('Link').exists()).toBe(true);
    });
  });
});
