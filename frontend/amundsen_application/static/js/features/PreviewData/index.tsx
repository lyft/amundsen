// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';

import { PreviewData } from 'interfaces/PreviewData';
import {
  NO_DATA_MESSAGE,
  PREVIEW_COLUMN_MAX_LEN,
  PREVIEW_COLUMN_MSG,
} from './constants';

import './styles.scss';

export interface PreviewDataProps {
  isLoading: boolean;
  previewData: PreviewData;
}

export const PreviewDataLoader = () => (
  <div className="preview-data-loader">
    <div className="shimmer-header-row is-shimmer-animated" />
    <div className="shimmer-row is-shimmer-animated" />
    <div className="shimmer-row is-shimmer-animated" />
    <div className="shimmer-row is-shimmer-animated" />
    <div className="shimmer-row is-shimmer-animated" />
    <div className="shimmer-row is-shimmer-animated" />
    <div className="shimmer-row is-shimmer-animated" />
    <div className="shimmer-row is-shimmer-animated" />
    <div className="shimmer-row is-shimmer-animated" />
  </div>
);

export const getSanitizedValue = (value) => {
  let sanitizedValue = '';
  if (value === 0 || typeof value === 'boolean') {
    sanitizedValue = value.toString();
  } else if (typeof value === 'object') {
    sanitizedValue = JSON.stringify(value);
  } else {
    sanitizedValue = value;
  }

  if (sanitizedValue.length > PREVIEW_COLUMN_MAX_LEN) {
    return PREVIEW_COLUMN_MSG;
  }
  return sanitizedValue;
};

export const PreviewDataTable: React.FC<PreviewDataProps> = ({
  isLoading,
  previewData,
}) => {
  if (isLoading) {
    return <PreviewDataLoader />;
  }
  if (
    !previewData.columns ||
    !previewData.data ||
    previewData.columns.length === 0 ||
    previewData.data.length === 0
  ) {
    return (
      <div className="preview-data">
        <div className="error-message">{NO_DATA_MESSAGE}</div>
      </div>
    );
  }

  return (
    <div className="preview-data">
      <div className="grid">
        {previewData.columns.map((col, colId) => {
          const fieldName = col.column_name;
          return (
            <div key={fieldName} id={fieldName} className="grid-column">
              <div className="grid-cell grid-header text-subtitle-w3">
                {fieldName.toUpperCase()}
              </div>
              {(previewData.data || []).map((row, rowId) => {
                const cellId = `${colId}:${rowId}`;
                const dataItemValue = getSanitizedValue(row[fieldName]);
                return (
                  <div key={cellId} className="grid-cell grid-data-cell">
                    {dataItemValue}
                  </div>
                );
              })}
            </div>
          );
        })}
      </div>
    </div>
  );
};
