// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import * as Avatar from 'react-avatar';
import { OverlayTrigger, Popover } from 'react-bootstrap';
import { Link } from 'react-router-dom';

import { TableReader } from 'interfaces';
import AppConfig from 'config/config';
import { logClick } from 'utils/analytics';

import './styles.scss';

export interface FrequentUsersProps {
  readers: TableReader[];
}

export function renderReader(
  reader: TableReader,
  index: number,
  readers: TableReader[]
) {
  const { user } = reader;
  let link = user.profile_url;
  let target = '_blank';
  if (AppConfig.indexUsers.enabled) {
    link = `/user/${user.user_id}?source=frequent_users`;
    target = '';
  }

  return (
    <OverlayTrigger
      key={user.display_name}
      trigger={['hover', 'focus']}
      placement="top"
      overlay={
        <Popover id="popover-trigger-hover-focus">{user.display_name}</Popover>
      }
    >
      <Link
        className="avatar-overlap"
        onClick={logClick}
        data-type="frequent-users"
        to={link}
        target={target}
      >
        <Avatar
          name={user.display_name}
          round
          size={25}
          style={{ zIndex: readers.length - index, position: 'relative' }}
        />
      </Link>
    </OverlayTrigger>
  );
}

const FrequentUsers: React.FC<FrequentUsersProps> = ({
  readers,
}: FrequentUsersProps) => {
  if (readers.length === 0) {
    return <label className="body-3">No frequent users exist</label>;
  }

  return <div className="frequent-users">{readers.map(renderReader)}</div>;
};

export default FrequentUsers;
