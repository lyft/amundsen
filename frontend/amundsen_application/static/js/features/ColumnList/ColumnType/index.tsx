// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { Modal, OverlayTrigger, Popover } from 'react-bootstrap';

import './styles.scss';

import { logClick } from 'utils/analytics';
import {
  getTruncatedText,
  parseNestedType,
  NestedType,
  ParsedType,
} from './parser';

const CTA_TEXT = 'Click to see nested fields';
const MODAL_TITLE = 'Nested Type';
const TEXT_INDENT = 8;

export interface ColumnTypeProps {
  columnName: string;
  database: string;
  type: string;
}

export interface ColumnTypeState {
  showModal: boolean;
}

export class ColumnType extends React.Component<
  ColumnTypeProps,
  ColumnTypeState
> {
  nestedType: NestedType | null;

  constructor(props) {
    super(props);

    this.state = {
      showModal: false,
    };
    const { database, type } = this.props;
    this.nestedType = parseNestedType(type, database);
  }

  hideModal = (e) => {
    this.stopPropagation(e);
    this.setState({ showModal: false });
  };

  showModal = (e) => {
    logClick(e);
    this.stopPropagation(e);
    this.setState({ showModal: true });
  };

  stopPropagation = (e) => {
    if (e) {
      e.stopPropagation();
    }
  };

  createLineItem = (text: string, textIndent: number) => (
    <div key={`lineitem:${text}`} style={{ textIndent: `${textIndent}px` }}>
      {text}
    </div>
  );

  renderParsedChildren = (children: ParsedType[], level: number) => {
    const textIndent = level * TEXT_INDENT;
    return children.map((item) => {
      if (typeof item === 'string') {
        return this.createLineItem(item, textIndent);
      }
      return this.renderNestedType(item, level);
    });
  };

  renderNestedType = (nestedType: NestedType, level: number = 0) => {
    const { head, tail, children } = nestedType;
    const textIndent = level * TEXT_INDENT;
    return (
      <div key={`nesteditem:${head}${tail}`}>
        {this.createLineItem(head, textIndent)}
        {this.renderParsedChildren(children, level + 1)}
        {this.createLineItem(tail, textIndent)}
      </div>
    );
  };

  render = () => {
    const { columnName, type } = this.props;

    if (this.nestedType === null) {
      return <p className="column-type">{type}</p>;
    }

    const popoverHover = (
      <Popover
        className="column-type-popover"
        id={`column-type-popover:${columnName}`}
      >
        {CTA_TEXT}
      </Popover>
    );
    return (
      <div onClick={this.stopPropagation}>
        <OverlayTrigger
          trigger={['hover', 'focus']}
          placement="top"
          overlay={popoverHover}
          rootClose
        >
          <button
            data-type="column-type"
            type="button"
            className="column-type-btn"
            onClick={this.showModal}
          >
            {getTruncatedText(this.nestedType)}
          </button>
        </OverlayTrigger>
        <Modal
          className="column-type-modal"
          show={this.state.showModal}
          onHide={this.hideModal}
        >
          <Modal.Header closeButton>
            <Modal.Title>
              <h5 className="main-title">{MODAL_TITLE}</h5>
              <div className="sub-title">{columnName}</div>
            </Modal.Title>
          </Modal.Header>
          <Modal.Body>
            <div className="column-type-modal-content">
              {this.renderNestedType(this.nestedType)}
            </div>
          </Modal.Body>
        </Modal>
      </div>
    );
  };
}

export default ColumnType;
