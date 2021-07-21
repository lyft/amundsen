// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { OverlayTrigger, Popover } from 'react-bootstrap';

import { ColumnUniqueValues } from 'interfaces/index';
import UniqueValuesModal from './UniqueValuesModal';

import './styles.scss';

export const UNIQUE_VALUES_TITLE = 'Unique Values';
export const SEE_MORE_LINK_TEXT = 'See all';
export const POPOVER_TEXT = 'Click to see a full list of unique values';
export const NUMBER_OF_VALUES_SUMMARY = 5;

export interface ExpandableUniqueValuesProps {
  uniqueValues: ColumnUniqueValues[];
}

type UniqueValueSummaryProps = {
  uniqueValues: ColumnUniqueValues[];
};

const UniqueValueSummary: React.FC<UniqueValueSummaryProps> = ({
  uniqueValues,
}: UniqueValueSummaryProps) => {
  const summaryItems = uniqueValues.slice(0, NUMBER_OF_VALUES_SUMMARY);
  const [showModal, setShowModal] = React.useState(false);

  const handleSeeAll = () => {
    setShowModal(true);
  };
  const handleCloseModal = () => {
    setShowModal(false);
  };
  const popoverHoverFocus = (
    <Popover id="popover-trigger-hover-focus">{POPOVER_TEXT}</Popover>
  );

  return (
    <div className="unique-values-list">
      {summaryItems.map(({ value }, index) => {
        const trailingSymbol = index === summaryItems.length - 1 ? '...' : ', ';

        return (
          <span className="unique-value-item" key={value}>
            {value}
            {trailingSymbol}
          </span>
        );
      })}
      <OverlayTrigger
        trigger={['hover', 'focus']}
        placement="top"
        overlay={popoverHoverFocus}
      >
        <button
          className="unique-values-expand-link btn-link"
          type="button"
          onClick={handleSeeAll}
        >
          {SEE_MORE_LINK_TEXT}
        </button>
      </OverlayTrigger>
      <UniqueValuesModal
        shouldShow={showModal}
        uniqueValues={uniqueValues}
        onClose={handleCloseModal}
      />
    </div>
  );
};

const ExpandableUniqueValues: React.FC<ExpandableUniqueValuesProps> = ({
  uniqueValues,
}: ExpandableUniqueValuesProps) => {
  if (uniqueValues.length === 0) {
    return null;
  }
  return (
    <article className="unique-values">
      <div className="unique-values-wrapper">
        <span className="unique-values-title">{UNIQUE_VALUES_TITLE} </span>
        <UniqueValueSummary uniqueValues={uniqueValues} />
      </div>
    </article>
  );
};

export default ExpandableUniqueValues;
