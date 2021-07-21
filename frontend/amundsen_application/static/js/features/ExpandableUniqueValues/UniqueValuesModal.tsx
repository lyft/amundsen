// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { Modal } from 'react-bootstrap';

import { formatNumber, isNumber } from 'utils/numberUtils';

import { ColumnUniqueValues } from 'interfaces/index';

const UNIQUE_VALUES_MODAL_TITLE = 'Unique Values';

type UniqueValueRowProps = ColumnUniqueValues;

const UniqueValueRow: React.FC<UniqueValueRowProps> = ({
  value,
  count,
}: UniqueValueRowProps) => (
  <div className="unique-value-row">
    <div className="unique-value-name body-3">{value}</div>
    <div className="unique-value-value">
      {isNumber(count) ? formatNumber(+count) : count}
    </div>
  </div>
);

export type UniqueValuesModalProps = {
  uniqueValues: ColumnUniqueValues[];
  onClose: () => void;
  shouldShow: boolean;
};

const UniqueValuesModal: React.FC<UniqueValuesModalProps> = ({
  uniqueValues,
  onClose,
  shouldShow,
}: UniqueValuesModalProps) => (
  <Modal
    className="unique-values-modal"
    onHide={onClose}
    show={shouldShow}
    scrollable="true"
  >
    <Modal.Header className="unique-values-modal-header" closeButton>
      <Modal.Title>{UNIQUE_VALUES_MODAL_TITLE}</Modal.Title>
    </Modal.Header>
    <Modal.Body>
      <div className="unique-values-table">
        {uniqueValues.map(({ value, count }) => (
          <UniqueValueRow key={value} value={value} count={count} />
        ))}
      </div>
    </Modal.Body>
  </Modal>
);

export default UniqueValuesModal;
