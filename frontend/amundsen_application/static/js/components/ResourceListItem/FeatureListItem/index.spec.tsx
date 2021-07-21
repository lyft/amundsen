// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { shallow } from 'enzyme';
import { Link } from 'react-router-dom';

import BadgeList from 'features/BadgeList';
import * as ConfigUtils from 'config/config-utils';

import { featureSummary } from 'fixtures/metadata/feature';

import FeatureListItem, {
  FeatureListItemProps,
} from 'components/ResourceListItem/FeatureListItem';
import { RightIcon } from 'components/SVGIcons';

const MOCK_DISPLAY_NAME = 'displayName';
const MOCK_ICON_CLASS = 'test-class';

jest.mock('config/config-utils', () => ({
  getSourceDisplayName: jest.fn(() => MOCK_DISPLAY_NAME),
  getSourceIconClass: jest.fn(() => MOCK_ICON_CLASS),
}));

describe('FeatureListItem', () => {
  const setup = (propOverrides?: Partial<FeatureListItemProps>) => {
    const props: FeatureListItemProps = {
      logging: { source: 'src', index: 0 },
      feature: featureSummary,
      ...propOverrides,
    };
    const wrapper = shallow<typeof FeatureListItem>(
      // eslint-disable-next-line react/jsx-props-no-spreading
      <FeatureListItem {...props} />
    );
    return { props, wrapper };
  };

  describe('render', () => {
    let props: FeatureListItemProps;
    let wrapper;

    beforeAll(() => {
      const setupResult = setup();
      props = setupResult.props;
      wrapper = setupResult.wrapper;
    });

    it('renders item as Link with correct redirection', () => {
      const actual = wrapper.find(Link).length;
      const expected = 1;

      expect(actual).toEqual(expected);
    });

    describe('renders resource-info section', () => {
      let resourceInfo;
      beforeAll(() => {
        resourceInfo = wrapper.find('.resource-info');
      });

      it('renders start correct icon', () => {
        const startIcon = resourceInfo.find('.resource-icon');

        expect(startIcon.exists()).toBe(true);
        expect(startIcon.props().className).toEqual(
          `icon resource-icon ${MOCK_ICON_CLASS}`
        );
        expect(ConfigUtils.getSourceIconClass).toHaveBeenCalledWith(
          'hive',
          props.feature.type
        );
      });

      it('renders feature group and name', () => {
        expect(resourceInfo.find('.resource-name').text()).toEqual(
          `${props.feature.feature_group}.${props.feature.name}`
        );
      });

      it('renders feature description', () => {
        expect(resourceInfo.children().at(1).children().at(1).text()).toEqual(
          props.feature.description
        );
      });
    });

    describe('renders resource-source section', () => {
      let resourceType;
      beforeAll(() => {
        resourceType = wrapper.find('.resource-source');
      });

      it('renders resource type', () => {
        expect(resourceType.text()).toEqual(MOCK_DISPLAY_NAME);
        expect(ConfigUtils.getSourceDisplayName).toHaveBeenCalledWith(
          'hive',
          props.feature.type
        );
      });
    });
    describe('renders resource-badges section', () => {
      let resourceBadges;
      beforeAll(() => {
        resourceBadges = wrapper.find('.resource-badges');
      });

      it('renders resource badges section', () => {
        expect(resourceBadges.exists()).toBe(true);
      });

      describe('if props.feature has badges', () => {
        it('renders BadgeList for badges', () => {
          expect(resourceBadges.find(BadgeList).props().badges).toEqual(
            props.feature.badges
          );
        });
      });
    });

    describe('renders resource-entity section', () => {
      let resourceEntity;
      beforeAll(() => {
        resourceEntity = wrapper.find('.resource-entity');
      });

      it('renders default text if it doesnt exist', () => {
        expect(resourceEntity.find('.resource-type').text()).toBe(
          'test_entity'
        );
      });

      it('renders correct end icon', () => {
        const actual = resourceEntity.find(RightIcon).length;
        const expected = 1;

        expect(actual).toEqual(expected);
      });
    });
  });
});
