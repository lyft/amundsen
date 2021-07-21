// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';

import { BadgeStyle } from 'config/config-types';
import { convertText, CaseType } from 'utils/textUtils';

import './styles.scss';

export interface FlagProps {
  caseType?: CaseType | null;
  text: string;
  labelStyle?: BadgeStyle;
}

const Flag: React.FC<FlagProps> = ({
  caseType = null,
  text = '',
  labelStyle = BadgeStyle.DEFAULT,
}: FlagProps) => (
  // TODO: After upgrading to Bootstrap 4, this component should leverage badges
  // https://getbootstrap.com/docs/4.1/components/badge/
  <span className={`flag label label-${labelStyle}`}>
    <div className={`badge-overlay-${labelStyle}`}>
      {convertText(text, caseType)}
    </div>
  </span>
);
export default Flag;
