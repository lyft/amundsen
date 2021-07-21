// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { Link } from 'react-router-dom';
import { Modal } from 'react-bootstrap';

import AppConfig from 'config/config';
import AvatarLabel, { AvatarLabelProps } from 'components/AvatarLabel';
import LoadingSpinner from 'components/LoadingSpinner';
import { ResourceType, UpdateMethod, UpdateOwnerPayload } from 'interfaces';
import { logClick } from 'utils/analytics';

import { EditableSectionChildProps } from 'components/EditableSection';

import * as Constants from './constants';

import './styles.scss';

export interface DispatchFromProps {
  onUpdateList: (
    updateArray: UpdateOwnerPayload[],
    onSuccess?: () => any,
    onFailure?: () => any
  ) => void;
}

export interface ComponentProps {
  errorText?: string | null;
  resourceType: ResourceType;
}

interface OwnerAvatarLabelProps extends AvatarLabelProps {
  link?: string;
  isExternal?: boolean;
}

export interface StateFromProps {
  isLoading: boolean;
  itemProps: OwnerItemProps;
}

export type OwnerEditorProps = ComponentProps &
  DispatchFromProps &
  StateFromProps &
  EditableSectionChildProps;

export type OwnerItemProps = { [id: string]: OwnerAvatarLabelProps };

interface OwnerEditorState {
  errorText: string | null;
  itemProps: OwnerItemProps;
  tempItemProps: { [id: string]: AvatarLabelProps };
}

export class OwnerEditor extends React.Component<
  OwnerEditorProps,
  OwnerEditorState
> {
  private inputRef: React.RefObject<HTMLInputElement>;

  public static defaultProps: Partial<OwnerEditorProps> = {
    errorText: null,
    isLoading: false,
    itemProps: {},
    onUpdateList: () => undefined,
  };

  constructor(props) {
    super(props);

    this.state = {
      errorText: props.errorText,
      itemProps: props.itemProps,
      tempItemProps: props.itemProps,
    };

    this.inputRef = React.createRef();
  }

  componentDidUpdate(prevProps) {
    const { itemProps } = this.props;

    // TODO - itemProps is a new object and this check needs to be fixed
    if (prevProps.itemProps !== itemProps) {
      this.setState({
        itemProps,
        tempItemProps: itemProps,
      });
    }
  }

  handleShow = () => {
    const { setEditMode } = this.props;

    if (setEditMode) {
      setEditMode(true);
    }
  };

  cancelEdit = () => {
    const { setEditMode } = this.props;
    const { itemProps } = this.state;

    this.setState({ tempItemProps: itemProps });
    if (setEditMode) {
      setEditMode(false);
    }
  };

  saveEdit = () => {
    const { itemProps, tempItemProps } = this.state;
    const { setEditMode, onUpdateList } = this.props;

    const updateArray: UpdateOwnerPayload[] = [];

    Object.keys(itemProps).forEach((key) => {
      if (!tempItemProps.hasOwnProperty(key)) {
        updateArray.push({ method: UpdateMethod.DELETE, id: key });
      }
    });
    Object.keys(tempItemProps).forEach((key) => {
      if (!itemProps.hasOwnProperty(key)) {
        updateArray.push({ method: UpdateMethod.PUT, id: key });
      }
    });

    const onSuccessCallback = () => {
      if (setEditMode) {
        setEditMode(false);
      }
    };
    const onFailureCallback = () => {
      this.setState({
        errorText: Constants.DEFAULT_ERROR_TEXT,
      });
      if (setEditMode) {
        setEditMode(false);
      }
    };

    onUpdateList(updateArray, onSuccessCallback, onFailureCallback);
  };

  recordAddItem = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (this.inputRef.current) {
      const { value } = this.inputRef.current;

      if (value) {
        this.inputRef.current.value = '';

        const newTempItemProps = {
          ...this.state.tempItemProps,
          [value]: { label: value },
        };
        this.setState({ tempItemProps: newTempItemProps });
      }
    }
  };

  recordDeleteItem = (deletedKey: string) => {
    const { tempItemProps } = this.state;

    const newTempItemProps = Object.keys(tempItemProps)
      .filter((key) => key !== deletedKey)
      .reduce((obj, key) => {
        obj[key] = tempItemProps[key];
        return obj;
      }, {});
    this.setState({ tempItemProps: newTempItemProps });
  };

  renderModalBody = () => {
    const { isEditing, isLoading } = this.props;

    if (!isEditing) {
      return null;
    }

    if (isLoading) {
      return (
        <Modal.Body>
          <LoadingSpinner />
        </Modal.Body>
      );
    }

    return (
      <Modal.Body>
        <form className="component-form" onSubmit={this.recordAddItem}>
          {/* eslint-disable jsx-a11y/no-autofocus */}
          <input
            id="add-item-input"
            autoFocus
            placeholder={`Please enter ${
              AppConfig.userIdLabel || Constants.USERID_LABEL
            }`}
            ref={this.inputRef}
          />
          {/* eslint-enable jsx-a11y/no-autofocus */}
          <button className="btn btn-default add-button" type="submit">
            {Constants.ADD_ITEM}
          </button>
        </form>
        <ul className="component-list">
          {Object.keys(this.state.tempItemProps).map((key) => (
            <li key={`modal-list-item:${key}`}>
              {React.createElement(AvatarLabel, this.state.tempItemProps[key])}
              <button
                className="btn btn-flat-icon delete-button"
                /* tslint:disable - TODO: Investigate jsx-no-lambda rule */
                onClick={() => this.recordDeleteItem(key)}
                /* tslint:enable */
                type="button"
              >
                <span className="sr-only">{Constants.DELETE_ITEM}</span>
                <img className="icon icon-delete" alt="" />
              </button>
            </li>
          ))}
        </ul>
      </Modal.Body>
    );
  };

  render() {
    const { isEditing, readOnly, resourceType } = this.props;
    const { errorText, itemProps } = this.state;
    const hasItems = Object.keys(itemProps).length > 0;

    if (errorText) {
      return (
        <div className="owner-editor-component">
          <label className="status-message">{errorText}</label>
        </div>
      );
    }

    const ownerList = hasItems ? (
      <ul className="component-list">
        {Object.keys(itemProps).map((key) => {
          const owner = itemProps[key];
          const avatarLabel = React.createElement(AvatarLabel, owner);

          let listItem;
          if (owner.link === undefined) {
            listItem = avatarLabel;
          } else if (owner.isExternal) {
            listItem = (
              <a
                href={owner.link}
                target="_blank"
                id={`${resourceType}-owners:${key}`}
                onClick={logClick}
                rel="noopener noreferrer"
              >
                {avatarLabel}
              </a>
            );
          } else {
            listItem = (
              <Link
                to={owner.link}
                id={`${resourceType}-owners:${key}`}
                onClick={logClick}
              >
                {avatarLabel}
              </Link>
            );
          }
          return <li key={`list-item:${key}`}>{listItem}</li>;
        })}
      </ul>
    ) : null;

    return (
      <div className="owner-editor-component">
        {ownerList}
        {readOnly && !hasItems && (
          <AvatarLabel
            avatarClass="gray-avatar"
            labelClass="text-placeholder"
            label={Constants.NO_OWNER_TEXT}
          />
        )}
        {!readOnly && !hasItems && (
          <button
            type="button"
            className="btn btn-flat-icon add-item-button"
            onClick={this.handleShow}
          >
            <img className="icon icon-plus-circle" alt="" />
            <span>{Constants.ADD_OWNER}</span>
          </button>
        )}
        {!readOnly && (
          <Modal
            className="owner-editor-modal"
            show={isEditing}
            onHide={this.cancelEdit}
          >
            <Modal.Header className="text-center" closeButton={false}>
              <Modal.Title>{Constants.OWNED_BY}</Modal.Title>
            </Modal.Header>
            {this.renderModalBody()}
            <Modal.Footer>
              <button
                type="button"
                className="btn btn-default"
                onClick={this.cancelEdit}
              >
                {Constants.CANCEL_TEXT}
              </button>
              <button
                type="button"
                className="btn btn-primary"
                onClick={this.saveEdit}
              >
                {Constants.SAVE_TEXT}
              </button>
            </Modal.Footer>
          </Modal>
        )}
      </div>
    );
  }
}

export default OwnerEditor;
