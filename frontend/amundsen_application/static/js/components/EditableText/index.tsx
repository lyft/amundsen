// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as autosize from 'autosize';
import * as React from 'react';
import * as ReactMarkdown from 'react-markdown';

import { EditableSectionChildProps } from 'components/EditableSection';
import {
  CANCEL_BUTTON_TEXT,
  REFRESH_BUTTON_TEXT,
  REFRESH_MESSAGE,
  UPDATE_BUTTON_TEXT,
} from './constants';

import './styles.scss';

export interface StateFromProps {
  refreshValue?: string;
}

export interface DispatchFromProps {
  getLatestValue?: (onSuccess?: () => any, onFailure?: () => any) => void;
  onSubmitValue?: (
    newValue: string,
    onSuccess?: () => any,
    onFailure?: () => any
  ) => void;
}

export interface ComponentProps {
  editable?: boolean;
  maxLength?: number;
  value?: string;
}

export type EditableTextProps = ComponentProps &
  DispatchFromProps &
  StateFromProps &
  EditableSectionChildProps;

interface EditableTextState {
  value?: string;
  isDisabled: boolean;
}

class EditableText extends React.Component<
  EditableTextProps,
  EditableTextState
> {
  readonly textAreaRef;

  public static defaultProps: EditableTextProps = {
    editable: true,
    maxLength: 250,
    value: '',
  };

  constructor(props) {
    super(props);
    this.textAreaRef = React.createRef();

    this.state = {
      isDisabled: false,
      value: props.value,
    };
  }

  componentDidUpdate(prevProps) {
    if (!this.props.isEditing) return;
    if (!prevProps.isEditing) {
      const textArea = this.textAreaRef.current;
      if (textArea) {
        autosize(textArea);
        textArea.focus();
      }

      if (this.props.getLatestValue) {
        this.props.getLatestValue();
      }
    } else if (
      this.props.refreshValue !== this.state.value &&
      !this.state.isDisabled
    ) {
      // disable the component if a refresh is needed
      this.setState({ isDisabled: true });
    }
  }

  exitEditMode = () => {
    this.props.setEditMode?.(false);
  };

  enterEditMode = () => {
    this.props.setEditMode?.(true);
  };

  refreshText = () => {
    this.setState({ value: this.props.refreshValue, isDisabled: false });
    const textArea = this.textAreaRef.current;
    if (textArea) {
      textArea.value = this.props.refreshValue;
      autosize.update(textArea);
    }
  };

  updateText = () => {
    const newValue = this.textAreaRef.current.value;
    const onSuccessCallback = () => {
      this.props.setEditMode?.(false);
      this.setState({ value: newValue });
    };
    const onFailureCallback = () => {
      this.exitEditMode();
    };

    this.props.onSubmitValue?.(newValue, onSuccessCallback, onFailureCallback);
  };

  render() {
    const { isEditing, editable, maxLength } = this.props;
    const { value = '', isDisabled } = this.state;

    if (!isEditing) {
      return (
        <div className="editable-text">
          <div className="markdown-wrapper">
            <ReactMarkdown allowDangerousHtml={false}>{value}</ReactMarkdown>
          </div>
          {editable && !value && (
            <a
              className="edit-link"
              href="JavaScript:void(0)"
              onClick={this.enterEditMode}
            >
              Add Description
            </a>
          )}
        </div>
      );
    }

    return (
      <div className="editable-text">
        <textarea
          className="editable-textarea"
          rows={2}
          maxLength={maxLength}
          ref={this.textAreaRef}
          defaultValue={value}
          disabled={isDisabled}
        />
        <div className="editable-textarea-controls">
          {isDisabled && (
            <>
              <h2 className="label label-danger refresh-message">
                {REFRESH_MESSAGE}
              </h2>
              <button
                className="btn btn-primary refresh-button"
                onClick={this.refreshText}
                type="button"
              >
                <img className="icon icon-refresh" alt="" />
                {REFRESH_BUTTON_TEXT}
              </button>
            </>
          )}
          {!isDisabled && (
            <button
              className="btn btn-primary update-button"
              onClick={this.updateText}
              type="button"
            >
              {UPDATE_BUTTON_TEXT}
            </button>
          )}
          <button
            className="btn btn-default cancel-button"
            onClick={this.exitEditMode}
            type="button"
          >
            {CANCEL_BUTTON_TEXT}
          </button>
        </div>
      </div>
    );
  }
}

export default EditableText;
