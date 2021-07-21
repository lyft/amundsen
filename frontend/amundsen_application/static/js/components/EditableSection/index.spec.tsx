// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { shallow } from 'enzyme';

import TagInput from 'components/Tags/TagInput';
import { ResourceType } from 'interfaces/Resources';
import EditableSection, { EditableSectionProps } from '.';

describe('EditableSection', () => {
  const setup = (propOverrides?: Partial<EditableSectionProps>, children?) => {
    const props = {
      title: 'defaultTitle',
      readOnly: false,
      ...propOverrides,
    };
    const wrapper = shallow<EditableSection>(
      // eslint-disable-next-line react/jsx-props-no-spreading
      <EditableSection {...props}>{children}</EditableSection>
    );
    return { wrapper, props };
  };

  describe('handleClick', () => {
    const clickEvent = {
      preventDefault: jest.fn(),
    };

    it('preventDefault on click', () => {
      const { wrapper, props } = setup();
      wrapper
        .find('.editable-section-label-wrapper')
        .simulate('click', clickEvent);
      expect(clickEvent.preventDefault).toHaveBeenCalled();
    });
  });

  describe('setEditMode', () => {
    const { wrapper, props } = setup();

    it('Enters edit mode after calling setEditMode(true)', () => {
      wrapper.instance().setEditMode(true);
      expect(wrapper.state().isEditing).toBe(true);
    });

    it('Exits edit mode after calling setEditMode(false)', () => {
      wrapper.instance().setEditMode(false);
      expect(wrapper.state().isEditing).toBe(false);
    });
  });

  describe('toggleEdit', () => {
    const { wrapper, props } = setup();
    const initialEditMode = wrapper.state().isEditing;

    it('Toggles the edit mode from the after each call', () => {
      // First call
      wrapper.instance().toggleEdit();
      expect(wrapper.state().isEditing).toBe(!initialEditMode);

      // Second call
      wrapper.instance().toggleEdit();
      expect(wrapper.state().isEditing).toBe(initialEditMode);
    });
  });

  describe('render', () => {
    const mockTitle = 'Mock';
    const convertTextSpy = jest
      .spyOn(EditableSection, 'convertText')
      .mockImplementation(() => mockTitle);
    const { wrapper, props } = setup(
      { title: 'custom title' },
      <TagInput resourceType={ResourceType.table} uriKey="key" />
    );

    it('renders the converted props.title as the section title', () => {
      convertTextSpy.mockClear();
      wrapper.instance().render();
      expect(convertTextSpy).toHaveBeenCalledWith(props.title);
      expect(wrapper.find('.section-title').text()).toBe(mockTitle);
    });

    it('renders children with additional props', () => {
      const childProps = wrapper.find(TagInput).props();
      expect(childProps).toMatchObject({
        isEditing: wrapper.state().isEditing,
        setEditMode: wrapper.instance().setEditMode,
      });
    });

    it('renders children as-is for non-react elements', () => {
      const child = 'non-react-child';
      const { wrapper } = setup(undefined, child);

      expect(wrapper.find('.editable-section-content').text()).toBe(child);
    });

    it('renders edit button correctly when readOnly=false', () => {
      expect(wrapper.find('.edit-button').props().onClick).toBe(
        wrapper.instance().toggleEdit
      );
    });

    describe('renders edit link correctly when readOnly=true', () => {
      let props;
      let wrapper;
      beforeAll(() => {
        const setupResult = setup(
          { readOnly: true, editUrl: 'test', editText: 'hello' },
          <div />
        );
        props = setupResult.props;
        wrapper = setupResult.wrapper;
      });

      it('link links to editUrl', () => {
        expect(wrapper.find('.edit-button').props().href).toBe(props.editUrl);
      });
    });

    it('does not render button if readOnly=true and there is no external editUrl', () => {
      const { wrapper } = setup({ readOnly: true }, <div />);
      expect(wrapper.find('.edit-button').exists()).toBeFalsy();
    });
  });
});
