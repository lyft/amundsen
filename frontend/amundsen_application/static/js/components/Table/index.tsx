// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';

import ShimmeringResourceLoader from '../ShimmeringResourceLoader';
import { UpIcon, DownIcon } from '../SVGIcons';

import './styles.scss';

// export type SortDirection = 'asc' | 'desc';
// export type SortCriteria = { key: string; direction: SortDirection };

export enum TextAlignmentValues {
  left = 'left',
  right = 'right',
  center = 'center',
}
export interface TableColumn {
  title: string;
  field: string;
  horAlign?: TextAlignmentValues;
  component?: (value: any, index: number) => React.ReactNode;
  width?: number;
  // sortable?: bool (false)
}
type Some = string | number | boolean | symbol | bigint | object;
type ValidData = Record<string, Some | null>; // Removes the undefined values

interface RowData {
  [key: string]: Some | null;
}

export interface TableOptions {
  tableClassName?: string;
  isLoading?: boolean;
  numLoadingBlocks?: number;
  rowHeight?: number;
  expandRow?: (rowValue: any, index: number) => React.ReactNode;
  onExpand?: (rowValues: any, index: number) => void;
  onCollapse?: (rowValues: any, index: number) => void;
  emptyMessage?: string;
}

export interface TableProps {
  data: RowData[];
  columns: TableColumn[];
  options?: TableOptions;
}

type RowStyles = {
  height: string;
};

type EmptyRowProps = {
  colspan: number;
  rowStyles: RowStyles;
  emptyMessage?: string;
};

const DEFAULT_EMPTY_MESSAGE = 'No Results';
const EXPAND_ROW_TEXT = 'Expand Row';
const INVALID_DATA_ERROR_MESSAGE =
  'Invalid data! Your data does not contain the fields specified on the columns property.';
const DEFAULT_LOADING_ITEMS = 3;
const DEFAULT_ROW_HEIGHT = 30;
const EXPANDING_CELL_WIDTH = '70px';
const DEFAULT_TEXT_ALIGNMENT = TextAlignmentValues.left;
const DEFAULT_CELL_WIDTH = 'auto';
const ALIGNEMENT_TO_CLASS_MAP = {
  left: 'is-left-aligned',
  right: 'is-right-aligned',
  center: 'is-center-aligned',
};

const getCellAlignmentClass = (alignment: TextAlignmentValues) =>
  ALIGNEMENT_TO_CLASS_MAP[alignment];

const fieldIsDefined = (field, row) => row[field] !== undefined;

const checkIfValidData = (
  data: unknown[],
  fields: string[]
): data is ValidData[] => {
  let isValid = true;

  for (let i = 0; i < fields.length; i++) {
    if (!data.some(fieldIsDefined.bind(null, fields[i]))) {
      isValid = false;
      break;
    }
  }
  return isValid;
};

const EmptyRow: React.FC<EmptyRowProps> = ({
  colspan,
  rowStyles,
  emptyMessage = DEFAULT_EMPTY_MESSAGE,
}: EmptyRowProps) => (
  <tr className="ams-table-row is-empty" style={rowStyles}>
    <td className="ams-empty-message-cell" colSpan={colspan}>
      {emptyMessage}
    </td>
  </tr>
);

const ShimmeringHeader: React.FC = () => (
  <tr>
    <th className="ams-table-heading-loading-cell">
      <div className="ams-table-shimmer-block" />
    </th>
  </tr>
);

type ShimmeringBodyProps = {
  numLoadingBlocks: number;
};

const ShimmeringBody: React.FC<ShimmeringBodyProps> = ({
  numLoadingBlocks,
}: ShimmeringBodyProps) => (
  <tr className="ams-table-row">
    <td className="ams-table-body-loading-cell">
      <ShimmeringResourceLoader numItems={numLoadingBlocks} />
    </td>
  </tr>
);

type ExpandingCellProps = {
  index: number;
  expandedRows: RowIndex[];
  rowValues: any;
  onClick: (index) => void;
  onExpand?: (rowValues: any, index: number) => void;
  onCollapse?: (rowValues: any, index: number) => void;
};
const ExpandingCell: React.FC<ExpandingCellProps> = ({
  index,
  onClick,
  onExpand,
  onCollapse,
  rowValues,
  expandedRows,
}: ExpandingCellProps) => {
  const isExpanded = expandedRows.includes(index);
  const cellStyling = { width: EXPANDING_CELL_WIDTH };

  return (
    <td
      className="ams-table-cell ams-table-expanding-cell"
      key={`expandingIndex:${index}`}
      style={cellStyling}
    >
      <button
        type="button"
        className="ams-table-expanding-button"
        onClick={() => {
          const newExpandedRows = isExpanded
            ? expandedRows.filter((i) => i !== index)
            : [...expandedRows, index];

          onClick(newExpandedRows);

          if (!isExpanded && onExpand) {
            onExpand(rowValues, index);
          }
          if (isExpanded && onCollapse) {
            onCollapse(rowValues, index);
          }
        }}
      >
        <span className="sr-only">{EXPAND_ROW_TEXT}</span>
        {isExpanded ? <UpIcon /> : <DownIcon />}
      </button>
    </td>
  );
};

type RowIndex = number;

const Table: React.FC<TableProps> = ({
  data,
  columns,
  options = {},
}: TableProps) => {
  const {
    tableClassName = '',
    isLoading = false,
    numLoadingBlocks = DEFAULT_LOADING_ITEMS,
    rowHeight = DEFAULT_ROW_HEIGHT,
    expandRow = null,
    emptyMessage,
    onExpand,
    onCollapse,
  } = options;
  const fields = columns.map(({ field }) => field);
  const rowStyles = { height: `${rowHeight}px` };
  const [expandedRows, setExpandedRows] = React.useState<RowIndex[]>([]);

  let body: React.ReactNode = (
    <EmptyRow
      colspan={fields.length}
      rowStyles={rowStyles}
      emptyMessage={emptyMessage}
    />
  );

  if (data.length) {
    if (!checkIfValidData(data, fields)) {
      throw new Error(INVALID_DATA_ERROR_MESSAGE);
    }

    body = data.map((item, index) => (
      <React.Fragment key={`index:${index}`}>
        <tr
          className={`ams-table-row ${
            expandRow && expandedRows.includes(index)
              ? 'has-child-expanded'
              : ''
          }`}
          key={`index:${index}`}
          style={rowStyles}
        >
          <>
            {expandRow ? (
              <ExpandingCell
                index={index}
                expandedRows={expandedRows}
                onExpand={onExpand}
                onCollapse={onCollapse}
                rowValues={item}
                onClick={setExpandedRows}
              />
            ) : null}
            {Object.entries(item)
              .filter(([key]) => fields.includes(key))
              .map(([key, value], rowIndex) => {
                const columnInfo = columns.find(({ field }) => field === key);
                const horAlign: TextAlignmentValues = columnInfo
                  ? columnInfo.horAlign || DEFAULT_TEXT_ALIGNMENT
                  : DEFAULT_TEXT_ALIGNMENT;
                const width =
                  columnInfo && columnInfo.width
                    ? `${columnInfo.width}px`
                    : DEFAULT_CELL_WIDTH;
                const cellStyle = {
                  width,
                };
                // TODO: Improve the typing of this
                let cellContent: React.ReactNode | typeof value = value;
                if (columnInfo && columnInfo.component) {
                  cellContent = columnInfo.component(value, rowIndex);
                }

                return (
                  <td
                    className={`ams-table-cell ${getCellAlignmentClass(
                      horAlign
                    )}`}
                    key={`index:${rowIndex}`}
                    style={cellStyle}
                  >
                    {cellContent}
                  </td>
                );
              })}
          </>
        </tr>
        {expandRow ? (
          <tr
            className={`ams-table-expanded-row ${
              expandedRows.includes(index) ? 'is-expanded' : ''
            }`}
            key={`expandedIndex:${index}`}
          >
            <td className="ams-table-cell">
              {/* Placeholder for the collapse/expand cell */}
            </td>
            <td className="ams-table-cell" colSpan={fields.length + 1}>
              {expandRow(item, index)}
            </td>
          </tr>
        ) : null}
      </React.Fragment>
    ));
  }

  let header: React.ReactNode = (
    <tr>
      {expandRow && (
        <th key="emptyTableHeading" className="ams-table-heading-cell" />
      )}
      {columns.map(
        ({ title, horAlign = DEFAULT_TEXT_ALIGNMENT, width = null }, index) => {
          const cellStyle = {
            width: width ? `${width}px` : DEFAULT_CELL_WIDTH,
          };

          return (
            <th
              className={`ams-table-heading-cell ${getCellAlignmentClass(
                horAlign
              )}`}
              key={`index:${index}`}
              style={cellStyle}
            >
              {title}
            </th>
          );
        }
      )}
    </tr>
  );

  if (isLoading) {
    header = <ShimmeringHeader />;
    body = <ShimmeringBody numLoadingBlocks={numLoadingBlocks} />;
  }

  return (
    <table className={`ams-table ${tableClassName || ''}`}>
      <thead className="ams-table-header">{header}</thead>
      <tbody className="ams-table-body">{body}</tbody>
    </table>
  );
};

export default Table;
