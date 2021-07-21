// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { OverlayTrigger, Popover } from 'react-bootstrap';

import './styles.scss';

export interface SchemaInfoProps {
  schema: string;
  table: string;
  desc: string;
  placement?: string;
}

const SchemaInfo: React.FC<SchemaInfoProps> = ({
  schema,
  table,
  desc,
  placement,
}: SchemaInfoProps) => {
  const popoverHoverFocus = (
    <Popover id="popover-trigger-hover-focus">
      <strong>{schema}:</strong> {desc}
    </Popover>
  );

  return (
    <>
      <OverlayTrigger
        trigger={['hover', 'focus']}
        placement={placement}
        overlay={popoverHoverFocus}
      >
        <span className="underline">{schema}</span>
      </OverlayTrigger>
      .{table}
    </>
  );
};

SchemaInfo.defaultProps = {
  placement: 'bottom',
};

export default SchemaInfo;
