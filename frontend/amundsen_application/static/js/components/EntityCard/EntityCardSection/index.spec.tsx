// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';

import { shallow } from 'enzyme';

import InfoButton from 'components/InfoButton';
import EntityCardSection, { EntityCardSectionProps } from '.';

describe('EntityCardSection', () => {
  let props: EntityCardSectionProps;
  let subject;

  beforeEach(() => {
    props = {
      title: 'Title',
      contentRenderer: jest.fn(() => <div>HI!</div>),
      isEditable: true,
    };
    // eslint-disable-next-line react/jsx-props-no-spreading
    subject = shallow(<EntityCardSection {...props} />);
  });

  describe('render', () => {
    it('renders the title', () => {
      expect(subject.find('.caption').text()).toEqual('TITLE');
    });

    it('renders InfoButton w/ correct props if props.infoText', () => {
      props.infoText = 'Here is some info';
      subject.setProps(props);
      expect(subject.find(InfoButton).props()).toMatchObject({
        infoText: props.infoText,
        placement: 'top',
      });
    });

    it('renders button to toggle edit mode if props.isEditable', () => {
      expect(subject.find('button').props().onClick).toEqual(
        subject.instance().toggleEditMode
      );
    });

    it('renders with correct class if state.readOnly', () => {
      subject.setState({ readOnly: true });
      expect(subject.find('button').props().className).toEqual(
        'btn icon edit-button'
      );
    });

    it('renders with correct class if !state.readOnly', () => {
      subject.setState({ readOnly: false });
      expect(subject.find('button').props().className).toEqual(
        'btn active-edit-button'
      );
    });

    it('renders with expected content', () => {
      expect(subject.find('#section-content').props().children).toEqual(
        <div>HI!</div>
      );
    });
  });

  describe('toggleEditMode', () => {
    const mockBlur = jest.fn();
    beforeEach(() => {
      subject.instance().editButton = { current: { blur: mockBlur } };
    });

    it('negates state.readOnly if props.isEditable', () => {
      subject.setState({ readOnly: true });
      subject.instance().toggleEditMode();
      expect(subject.instance().state.readOnly).toEqual(false);
    });

    it('does not update state.readyOnly if !props.isEditable', () => {
      props.isEditable = false;
      subject.setProps(props);
      subject.setState({ readOnly: true });
      subject.instance().toggleEditMode();
      expect(subject.instance().state.readOnly).toEqual(true);
    });

    it('calls blur on editButton', () => {
      subject.instance().toggleEditMode();
      expect(mockBlur).toHaveBeenCalled();
    });
  });
});
