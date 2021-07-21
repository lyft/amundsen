// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';

import { getBadgeConfig } from 'config/config-utils';
import { BadgeStyle, BadgeStyleConfig } from 'config/config-types';

import { convertText, CaseType } from 'utils/textUtils';
import { logClick } from 'utils/analytics';

import { Badge } from 'interfaces/Badges';

import './styles.scss';

const COLUMN_BADGE_CATEGORY = 'column';

export interface BadgeListProps {
  badges: Badge[];
  onBadgeClick: (badgeText: string) => void;
}

export interface ActionableBadgeProps {
  style: BadgeStyle;
  displayName: string;
  action: any;
}

const StaticBadge: React.FC<BadgeStyleConfig> = ({
  style,
  displayName,
}: BadgeStyleConfig) => (
  <span className={`static-badge flag label label-${style}`}>
    <div className={`badge-overlay-${style}`}>{displayName}</div>
  </span>
);

const ActionableBadge: React.FC<ActionableBadgeProps> = ({
  style,
  displayName,
  action,
}: ActionableBadgeProps) => (
  <span className="actionable-badge" onClick={action}>
    <StaticBadge style={style} displayName={displayName} />
  </span>
);

export default class BadgeList extends React.Component<BadgeListProps> {
  handleClick = (index: number, badgeText: string, e) => {
    const { onBadgeClick } = this.props;

    logClick(e, {
      target_type: 'badge',
      label: badgeText,
    });
    onBadgeClick(convertText(badgeText, CaseType.LOWER_CASE));
  };

  render() {
    const { badges } = this.props;
    const alphabetizedBadges = badges.sort((a, b) => {
      const aName = (a.badge_name ? a.badge_name : a.tag_name) || '';
      const bName = (b.badge_name ? b.badge_name : b.tag_name) || '';
      return aName.localeCompare(bName);
    });

    return (
      <span className="badge-list">
        {alphabetizedBadges.map((badge, index) => {
          let badgeConfig;
          // search badges with just name
          if (badge.tag_name) {
            badgeConfig = getBadgeConfig(badge.tag_name);
          }
          // metadata badges with name and category
          else if (badge.badge_name) {
            badgeConfig = getBadgeConfig(badge.badge_name);
            if (badge.category === COLUMN_BADGE_CATEGORY) {
              return (
                <StaticBadge
                  style={badgeConfig.style}
                  displayName={badgeConfig.displayName}
                  key={`badge-${index}`}
                />
              );
            }
          }
          if (badge.category !== COLUMN_BADGE_CATEGORY) {
            return (
              <ActionableBadge
                displayName={badgeConfig.displayName}
                style={badgeConfig.style}
                action={(e: React.SyntheticEvent) =>
                  this.handleClick(index, badgeConfig.displayName, e)
                }
                key={`badge-${index}`}
              />
            );
          }
        })}
      </span>
    );
  }
}
