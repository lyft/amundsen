// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';

import { shallow } from 'enzyme';

import EntityCard, { EntityCardProps } from '.';
import EntityCardSection from './EntityCardSection';

describe('EntityCard', () => {
  let props: EntityCardProps;
  let subject;

  beforeEach(() => {
    props = {
      sections: [
        {
          title: 'Title',
          infoText: 'Here is some info',
          contentRenderer: jest.fn(),
          isEditable: true,
        },
        {
          title: 'Title2',
          infoText: 'Here is some other info',
          contentRenderer: jest.fn(),
          isEditable: false,
        },
      ],
    };
    subject = shallow(<EntityCard {...props} />);
  });

  describe('render', () => {
    it('renders EntityCardSections', () => {
      expect(subject.find(EntityCardSection).length).toEqual(2);
    });

    it('passes correct props to EntityCardSection', () => {
      expect(subject.find(EntityCardSection).at(0).props()).toMatchObject({
        title: props.sections[0].title,
        infoText: props.sections[0].infoText,
        contentRenderer: props.sections[0].contentRenderer,
        isEditable: props.sections[0].isEditable,
      });
    });
  });
});
