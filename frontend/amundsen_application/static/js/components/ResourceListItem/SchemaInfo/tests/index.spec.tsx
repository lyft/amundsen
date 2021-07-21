// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { shallow } from 'enzyme';
import { OverlayTrigger, Popover } from 'react-bootstrap';

import SchemaInfo, {
  SchemaInfoProps,
} from 'components/ResourceListItem/SchemaInfo';

describe('SchemaInfo', () => {
  const setup = (propOverrides?: Partial<SchemaInfoProps>) => {
    const props: SchemaInfoProps = {
      schema: 'tableSchema',
      table: 'tableName',
      desc: 'schemaDescription',
      placement: 'bottom',
      ...propOverrides,
    };
    // eslint-disable-next-line react/jsx-props-no-spreading
    const wrapper = shallow(<SchemaInfo {...props} />);
    return {
      props,
      wrapper,
    };
  };

  describe('render', () => {
    let props: SchemaInfoProps;
    let wrapper;

    beforeAll(() => {
      const setupResult = setup();
      props = setupResult.props;
      wrapper = setupResult.wrapper;
    });

    it('renders OverlayTrigger with correct placement', () => {
      expect(wrapper.find(OverlayTrigger).props().placement).toEqual(
        props.placement
      );
    });

    it('renders OverlayTrigger with correct popover', () => {
      const expectedPopover = (
        <Popover id="popover-trigger-hover-focus">
          <strong>{props.schema}:</strong> {props.desc}
        </Popover>
      );
      expect(wrapper.find(OverlayTrigger).props().overlay).toEqual(
        expectedPopover
      );
    });

    it('renders OverlayTrigger with correct schema name', () => {
      expect(wrapper.find(OverlayTrigger).find('.underline').text()).toEqual(
        props.schema
      );
    });

    it('renders correct table name', () => {
      expect(wrapper.children().at(1).text()).toEqual('.');
      expect(wrapper.children().at(2).text()).toEqual(props.table);
    });
  });
});
