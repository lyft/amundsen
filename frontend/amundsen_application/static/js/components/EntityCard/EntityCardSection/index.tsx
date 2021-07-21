// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import InfoButton from 'components/InfoButton';

import { IconSizes } from 'interfaces';

import './styles.scss';

export interface EntityCardSectionProps {
  title: string;
  infoText?: string;
  contentRenderer: (readOnly?: boolean) => JSX.Element;
  isEditable: boolean;
}

interface EntityCardSectionState {
  readOnly: boolean;
}

class EntityCardSection extends React.Component<
  EntityCardSectionProps,
  EntityCardSectionState
> {
  private editButton: React.RefObject<HTMLButtonElement>;

  constructor(props) {
    super(props);
    this.state = {
      readOnly: true,
    };

    this.editButton = React.createRef();
    this.toggleEditMode = this.toggleEditMode.bind(this);
  }

  toggleEditMode() {
    if (this.props.isEditable) {
      this.setState({ readOnly: !this.state.readOnly });
    }
    this.editButton.current?.blur();
  }

  render() {
    const activeButtonClass = this.state.readOnly
      ? 'icon edit-button'
      : 'active-edit-button';
    return (
      <div className="entity-card-section">
        <div className="content-header">
          <div id="section-title" className="caption">
            {this.props.title.toUpperCase()}
            {this.props.infoText && (
              <InfoButton
                infoText={this.props.infoText}
                placement="top"
                size={IconSizes.SMALL}
              />
            )}
            {this.props.isEditable && (
              <button
                className={`btn ${activeButtonClass}`}
                onClick={this.toggleEditMode}
                ref={this.editButton}
              />
            )}
          </div>
        </div>
        <div id="section-content" className="content">
          {this.props.contentRenderer(this.state.readOnly)}
        </div>
      </div>
    );
  }
}

export default EntityCardSection;
