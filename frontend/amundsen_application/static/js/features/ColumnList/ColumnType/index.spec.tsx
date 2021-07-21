// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { mount } from 'enzyme';
import { Modal } from 'react-bootstrap';

import * as Analytics from 'utils/analytics';
import ColumnType, { ColumnTypeProps } from '.';

const logClickSpy = jest.spyOn(Analytics, 'logClick');
logClickSpy.mockImplementation(() => null);

const setup = (propOverrides?: Partial<ColumnTypeProps>) => {
  const props = {
    columnName: 'test',
    database: 'presto',
    type:
      'row(test_id varchar,test2 row(test2_id varchar,started_at timestamp,ended_at timestamp))',
    ...propOverrides,
  };
  // eslint-disable-next-line react/jsx-props-no-spreading
  const wrapper = mount<ColumnType>(<ColumnType {...props} />);
  return {
    wrapper,
    props,
  };
};
const { wrapper, props } = setup();

describe('ColumnType', () => {
  describe('lifecycle', () => {
    describe('when clicking on column-type-btn', () => {
      it('should call showModal on the instance', () => {
        const clickSpy = jest.spyOn(wrapper.instance(), 'showModal');
        wrapper.instance().forceUpdate();
        wrapper.find('.column-type-btn').simulate('click');

        expect(clickSpy).toHaveBeenCalled();
      });

      it('should log the interaction', () => {
        logClickSpy.mockClear();
        wrapper.find('.column-type-btn').simulate('click');

        expect(logClickSpy).toHaveBeenCalled();
      });
    });
  });

  describe('render', () => {
    it('renders the column type string for simple types', () => {
      const { wrapper, props } = setup({ type: 'varchar(32)' });
      expect(wrapper.find('.column-type').text()).toBe(props.type);
    });

    describe('for nested types', () => {
      it('renders the truncated column type string', () => {
        const actual = wrapper.find('.column-type-btn').text();
        const expected = 'row(...)';

        expect(actual).toBe(expected);
      });

      describe('renders a modal', () => {
        it('exists', () => {
          const actual = wrapper.find(Modal).exists();
          const expected = true;

          expect(actual).toBe(expected);
        });

        it('renders props.type in modal body', () => {
          const actual = wrapper.find('.sub-title').text();
          const expected = props.columnName;

          expect(actual).toBe(expected);
        });

        it('renders props.type in modal body', () => {
          const actual = wrapper.find('.modal-body').text();
          const expected = props.type;

          expect(actual).toBe(expected);
        });
      });
    });
  });
});
