// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { Dropdown, MenuItem } from 'react-bootstrap';

const defaultData = [
  { name: 'rowName', type: 'rowType', value: 1 },
  { name: 'rowName2', type: 'rowType2', value: 2 },
  { name: 'rowName3', type: 'rowType3', value: 3 },
];

const defaultColumns = [
  {
    title: 'Name',
    field: 'name',
  },
  {
    title: 'Type',
    field: 'type',
  },
  {
    title: 'Value',
    field: 'value',
  },
];

const initalConfig = {
  data: defaultData,
  columns: defaultColumns,
};

/**
 * Generates test data for the table data
 * @example
 * let testData = new TestDataBuilder()
 *                         .withUsageRow()
 *                         .build();
 */
function TestDataBuilder(config = {}) {
  this.Klass = TestDataBuilder;
  this.config = {
    ...initalConfig,
    ...config,
  };

  this.withWrongData = () => {
    const attr = {
      data: [
        { name: 'rowName', type: 'rowType', value: 1 },
        { name: 'rowName2', type: 'rowType2', value: 2 },
        { name: 'rowName3', type: 'rowType3', value: 3 },
      ],
      columns: [
        {
          title: 'Name',
          field: 'name',
        },
        {
          title: 'Type',
          field: 'type',
        },
        {
          title: 'Value',
          field: 'value',
        },
        {
          title: 'Bad Field',
          field: 'badfield',
        },
      ],
    };

    return new this.Klass(attr);
  };

  this.withUsageRow = () => {
    const attr = {
      data: [
        ...this.config.data,
        { name: 'usageRow', type: 'usageRowType', value: 4, usage: 44 },
      ],
      columns: [...this.config.columns, { title: 'Usage', field: 'usage' }],
    };

    return new this.Klass(attr);
  };

  this.withCollapsedRow = () => {
    const attr = {
      data: [
        { name: 'rowName', type: 'rowType', value: 1 },
        { name: 'rowName2', type: 'rowType2', value: 2 },
        { name: 'rowName3', type: 'rowType3', value: 3 },
      ],
      columns: [
        {
          title: 'Name',
          field: 'name',
        },
        {
          title: 'Type',
          field: 'type',
        },
      ],
    };

    return new this.Klass(attr);
  };

  this.withOneComponentColumn = () => {
    const attr = {
      data: [...this.config.data],
      columns: [
        {
          title: 'Name',
          field: 'name',
          component: (name) => <strong>{name}</strong>,
        },
        {
          title: 'Type',
          field: 'type',
        },
        {
          title: 'Value',
          field: 'value',
        },
      ],
    };

    return new this.Klass(attr);
  };

  this.withActionCell = () => {
    const attr = {
      data: [
        { name: 'rowName', type: 'rowType', value: 'Action Text' },
        { name: 'rowName2', type: 'rowType2', value: 'Action Text' },
        { name: 'rowName3', type: 'rowType3', value: 'Action Text' },
      ],
      columns: [
        {
          title: 'Name',
          field: 'name',
        },
        {
          title: 'Type',
          field: 'type',
        },
        {
          title: 'Value',
          field: 'value',
          component: (value, index) => (
            <Dropdown
              id={`detail-list-item-dropdown:${index}`}
              pullRight
              className="column-dropdown"
            >
              <Dropdown.Toggle noCaret>
                <span className="sr-only">More info</span>
                <img className="icon icon-more" alt="" />
              </Dropdown.Toggle>
              <Dropdown.Menu>
                <MenuItem onClick={() => console.log('index', index)}>
                  {value}
                </MenuItem>
              </Dropdown.Menu>
            </Dropdown>
          ),
        },
      ],
    };

    return new this.Klass(attr);
  };

  this.withMultipleComponentsColumn = () => {
    const attr = {
      data: [
        { name: 'rowName', type: 'rowType', value: [1] },
        { name: 'rowName2', type: 'rowType2', value: [2, 3] },
        { name: 'rowName3', type: 'rowType3', value: [4, 5, 6] },
      ],
      columns: [
        {
          title: 'Name',
          field: 'name',
        },
        {
          title: 'Type',
          field: 'type',
        },
        {
          title: 'Value',
          field: 'value',
          component: (values) =>
            values.map((val, i) => <strong key={`key:${val}`}>{val}</strong>),
        },
      ],
    };

    return new this.Klass(attr);
  };

  this.withAlignedColumns = () => {
    const attr = {
      data: [...this.config.data],
      columns: [
        {
          title: 'Name',
          field: 'name',
          horAlign: 'left',
        },
        {
          title: 'Type',
          field: 'type',
          horAlign: 'center',
        },
        {
          title: 'Value',
          field: 'value',
          horAlign: 'right',
        },
      ],
    };

    return new this.Klass(attr);
  };

  this.withFourColumns = () => {
    const attr = {
      data: [
        { name: 'rowName', type: 'rowType', value: 1, usage: 4 },
        { name: 'rowName2', type: 'rowType2', value: 2, usage: 12 },
        { name: 'rowName3', type: 'rowType3', value: 3, usage: 7 },
      ],
      columns: [
        {
          title: 'Name',
          field: 'name',
          horAlign: 'left',
        },
        {
          title: 'Type',
          field: 'type',
          horAlign: 'right',
        },
        {
          title: 'Value',
          field: 'value',
          horAlign: 'left',
        },
        {
          title: 'Usage',
          field: 'usage',
          horAlign: 'left',
        },
      ],
    };

    return new this.Klass(attr);
  };

  this.withFixedWidthColumns = () => {
    const attr = {
      data: [...this.config.data],
      columns: [
        {
          title: 'Name',
          field: 'name',
          width: 50,
          horAlign: 'left',
        },
        {
          title: 'Type',
          field: 'type',
          width: 200,
          horAlign: 'center',
        },
        {
          title: 'Value',
          field: 'value',
          horAlign: 'right',
        },
      ],
    };

    return new this.Klass(attr);
  };

  this.withEmptyData = () => {
    const attr = {
      data: [],
      columns: [{ title: 'Name', field: 'name' }],
    };

    return new this.Klass(attr);
  };

  this.withMoreDataThanColumns = () => {
    const attr = {
      data: [
        ...this.config.data,
        {
          name: 'extraName',
          type: 'extraRowType',
          value: 4,
          usage: 44,
          extraValue: 3,
        },
      ],
      columns: [...this.config.columns],
    };

    return new this.Klass(attr);
  };

  this.build = () => this.config;
}

export default TestDataBuilder;
