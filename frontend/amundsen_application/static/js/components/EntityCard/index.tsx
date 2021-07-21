// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import EntityCardSection, { EntityCardSectionProps } from './EntityCardSection';

// TODO: Use css-modules instead of 'import'
import './styles.scss';

export interface EntityCardProps {
  sections: EntityCardSectionProps[];
}

const EntityCard: React.FC<EntityCardProps> = ({
  sections,
}: EntityCardProps) => {
  const cardItems = sections.map((entry, index) => (
    <EntityCardSection
      key={`section:${index}`}
      title={entry.title}
      infoText={entry.infoText}
      contentRenderer={entry.contentRenderer}
      isEditable={entry.isEditable}
    />
  ));

  return <div className="entity-card">{cardItems}</div>;
};

EntityCard.defaultProps = {
  sections: [],
};

export default EntityCard;
