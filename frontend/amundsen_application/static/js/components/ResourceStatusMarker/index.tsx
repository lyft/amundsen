// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';

import './styles.scss';

export interface StatusMarkerProps {
  stateText: string;
  succeeded: boolean;
}

export interface StateProps {
  stateText: string;
}

const FailureState: React.FC<StateProps> = ({ stateText }: StateProps) => (
  <div className="failure">
    <div className="failure-icon">
      <div className="exclamation-top" />
      <div className="exclamation-bottom" />
    </div>
    <span className="status-text">{stateText}</span>
  </div>
);

const SuccessState: React.FC<StateProps> = ({ stateText }: StateProps) => (
  <div className="success">
    <div className="success-icon">
      <span className="icon icon-check" />
    </div>
    <span className="status-text">{stateText}</span>
  </div>
);

const ResourceStatusMarker: React.FC<StatusMarkerProps> = ({
  stateText,
  succeeded,
}: StatusMarkerProps) => {
  const state = stateText.charAt(0).toUpperCase() + stateText.slice(1);
  if (succeeded) {
    return <SuccessState stateText={state} />;
  }
  return <FailureState stateText={state} />;
};

export default ResourceStatusMarker;
