// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import React from 'react';
import { withKnobs, object } from '@storybook/addon-knobs';

import StorySection from '../StorySection';
import Table from '.';
import TestDataBuilder from './testDataBuilder';

const dataBuilder = new TestDataBuilder();
const { columns, data } = dataBuilder.build();
const {
  columns: alignedColumns,
  data: alignedData,
} = dataBuilder.withAlignedColumns().build();
const {
  columns: differentWidthColumns,
} = dataBuilder.withFixedWidthColumns().build();
const {
  columns: fourColumns,
  data: fourColData,
} = dataBuilder.withFourColumns().build();
const {
  columns: customColumns,
  data: customColumnsData,
} = dataBuilder.withOneComponentColumn().build();
const {
  columns: multipleCustomColumns,
  data: multipleCustomComlumnsData,
} = dataBuilder.withMultipleComponentsColumn().build();
const {
  columns: columnsWithAction,
  data: dataWithAction,
} = dataBuilder.withActionCell().build();
const {
  columns: columnsWithCollapsedRow,
  data: dataWithCollapsedRow,
} = dataBuilder.withCollapsedRow().build();
const expandRowComponent = (rowValue, index) => (
  <strong>
    {index}:{rowValue.value}
  </strong>
);

export const TableStates = () => (
  <>
    <StorySection title="Basic Table">
      <Table
        columns={object('basic table columns', columns)}
        data={object('basic table data', data)}
      />
    </StorySection>
    <StorySection title="Empty Table">
      <Table
        columns={object('empty table columns', columns)}
        data={object('empty table data', [])}
      />
    </StorySection>
    <StorySection title="Loading Table">
      <Table
        columns={[]}
        data={[]}
        options={object('options', { isLoading: true })}
      />
    </StorySection>
  </>
);

export const StyledTable = () => (
  <>
    <StorySection title="with different column alignment">
      <Table
        columns={object('aligned columns', alignedColumns)}
        data={object('aligned columns data', alignedData)}
      />
    </StorySection>
    <StorySection title="with 50px row height">
      <Table
        columns={columns}
        data={data}
        options={object('row height options', { rowHeight: 50 })}
      />
    </StorySection>
    <StorySection title="with different column widths">
      <Table
        columns={object(
          'different column widths columns',
          differentWidthColumns
        )}
        data={data}
        options={{ rowHeight: 50 }}
      />
    </StorySection>
    <StorySection title="with four columns">
      <Table
        columns={fourColumns}
        data={fourColData}
        options={{ rowHeight: 50 }}
      />
    </StorySection>
  </>
);

export const CustomizedTable = () => (
  <>
    <StorySection title="with custom column components">
      <Table
        columns={object('custom component columns', customColumns)}
        data={object('custom component data', customColumnsData)}
        options={{ rowHeight: 40 }}
      />
    </StorySection>
    <StorySection title="with multiple custom column components">
      <Table
        columns={object('multiple component columns', multipleCustomColumns)}
        data={object('multiple component data', multipleCustomComlumnsData)}
        options={{ rowHeight: 40 }}
      />
    </StorySection>
    <StorySection title="with Bootstrap dropdown as component">
      <Table
        columns={object('action columns', columnsWithAction)}
        data={object('action data', dataWithAction)}
        options={{ rowHeight: 40 }}
      />
    </StorySection>
    <StorySection title="with Custom Empty Message">
      <Table
        columns={columns}
        data={[]}
        options={object('empty message options', {
          emptyMessage: 'Custom Empty Message Here!',
        })}
      />
    </StorySection>
  </>
);

export const CollapsibleTable = () => (
  <>
    <StorySection title="with Collapsed Rows">
      <Table
        columns={object('collapsed rows columns', columnsWithCollapsedRow)}
        data={object('collapsed rows data', dataWithCollapsedRow)}
        options={object('collapsed rows options', {
          rowHeight: 40,
          expandRow: expandRowComponent,
        })}
      />
    </StorySection>
    <StorySection
      title="with onExpand handler"
      text="You can open the console to see the handler being called"
    >
      <Table
        columns={columnsWithCollapsedRow}
        data={dataWithCollapsedRow}
        options={object('onExpand options', {
          rowHeight: 40,
          expandRow: expandRowComponent,
          onExpand: (rowValues, index) => {
            console.log('Expanded row values:', rowValues);
            console.log('Expanded row index:', index);
          },
        })}
      />
    </StorySection>
    <StorySection
      title="with onCollapse handler"
      text="You can open the console to see the handler being called"
    >
      <Table
        columns={columnsWithCollapsedRow}
        data={dataWithCollapsedRow}
        options={object('onCollapse options', {
          rowHeight: 40,
          expandRow: expandRowComponent,
          onCollapse: (rowValues, index) => {
            console.log('Collapsed row values:', rowValues);
            console.log('Collapsed row index:', index);
          },
        })}
      />
    </StorySection>
  </>
);

export default {
  title: 'Components/Table',
  component: Table,
  decorators: [withKnobs],
};
