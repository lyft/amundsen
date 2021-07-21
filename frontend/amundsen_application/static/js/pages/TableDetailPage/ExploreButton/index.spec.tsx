// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { shallow } from 'enzyme';

import * as ConfigUtils from 'config/config-utils';
import { TableMetadata } from 'interfaces/TableMetadata';

import { logClick } from 'utils/analytics';
import ExploreButton from '.';

let mockExploreEnabled = true;
let mockExploreUrl = 'https://test-website.com';

jest.mock('config/config-utils', () => ({
  exploreEnabled: () => mockExploreEnabled,
  generateExploreUrl: () => mockExploreUrl,
}));

const generateExploreUrlSpy = jest.spyOn(ConfigUtils, 'generateExploreUrl');

describe('ExploreButton', () => {
  const setup = (tableDataOverrides?: Partial<TableMetadata>) => {
    const props = {
      tableData: {
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
      },
    };
    // eslint-disable-next-line react/jsx-props-no-spreading
    const wrapper = shallow<ExploreButton>(<ExploreButton {...props} />);
    return {
      props,
      wrapper,
    };
  };

  describe('generateUrl', () => {});

  describe('render', () => {
    beforeEach(() => {
      mockExploreEnabled = true;
      mockExploreUrl = 'https://test-website.com';
    });

    it('calls url generator with the partition value and key, if partitioned', () => {
      const { props, wrapper } = setup();
      wrapper.instance().render();
      expect(generateExploreUrlSpy).toHaveBeenCalledWith(props.tableData);
    });

    it('returns null if explore is not enabled', () => {
      mockExploreEnabled = false;
      const { wrapper } = setup();

      expect(wrapper.instance().render()).toBeNull();
    });

    it('returns null if the generated url is empty', () => {
      const { wrapper } = setup();
      mockExploreUrl = '';

      expect(wrapper.instance().render()).toBeNull();
    });

    it('renders a link to the explore URL', () => {
      const { wrapper } = setup();

      expect(wrapper.find('a').props()).toMatchObject({
        href: mockExploreUrl,
        target: '_blank',
        id: 'explore-sql',
        onClick: logClick,
      });
    });
  });
});
