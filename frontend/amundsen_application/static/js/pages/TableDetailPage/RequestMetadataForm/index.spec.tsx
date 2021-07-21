// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { shallow } from 'enzyme';
import globalState from 'fixtures/globalState';
import {
  NotificationType,
  RequestMetadataType,
  SendingState,
} from 'interfaces';
import {
  RequestMetadataForm,
  mapDispatchToProps,
  mapStateToProps,
  RequestMetadataProps,
} from '.';
import {
  TITLE_TEXT,
  FROM_LABEL,
  TO_LABEL,
  REQUEST_TYPE,
  TABLE_DESCRIPTION,
  COLUMN_DESCRIPTIONS,
  COLUMN_REQUESTED_COMMENT_PREFIX,
  COMMENT_PLACEHOLDER_COLUMN,
  COMMENT_PLACEHOLDER_DEFAULT,
  ADDITIONAL_DETAILS,
  SEND_BUTTON,
  SEND_FAILURE_MESSAGE,
  SEND_INPROGRESS_MESSAGE,
  SEND_SUCCESS_MESSAGE,
} from './constants';

const globalAny: any = global;
const mockFormData = {
  recipients: 'test1@test.com,test2@test.com',
  sender: 'test@test.com',
  'table-description': 'on',
  'fields-requested': 'off',
  comment: 'test',
  get: jest.fn(),
};
mockFormData.get.mockImplementation((val) => mockFormData[val]);
function formDataMock() {
  this.append = jest.fn();

  return mockFormData;
}
globalAny.FormData = formDataMock;

describe('RequestMetadataForm', () => {
  const setup = (propOverrides?: Partial<RequestMetadataProps>) => {
    const props: RequestMetadataProps = {
      userEmail: 'test0@lyft.com',
      tableOwners: ['test1@lyft.com', 'test2@lyft.com'],
      tableMetadata: globalState.tableMetadata.tableData,
      submitNotification: jest.fn(),
      requestIsOpen: true,
      sendState: SendingState.IDLE,
      closeRequestDescriptionDialog: jest.fn(),
      ...propOverrides,
    };
    const wrapper = shallow<RequestMetadataForm>(
      // eslint-disable-next-line react/jsx-props-no-spreading
      <RequestMetadataForm {...props} />
    );
    return { props, wrapper };
  };

  describe('componentWillUnmount', () => {
    it('calls closeRequestDescriptionDialog', () => {
      const { props, wrapper } = setup();
      const closeRequestDescriptionDialogSpy = jest.spyOn(
        props,
        'closeRequestDescriptionDialog'
      );
      wrapper.instance().componentWillUnmount();
      expect(closeRequestDescriptionDialogSpy).toHaveBeenCalled();
    });
  });

  describe('closeDialog', () => {
    it('calls closeRequestDescriptionDialog', () => {
      const { props, wrapper } = setup();
      const closeRequestDescriptionDialogSpy = jest.spyOn(
        props,
        'closeRequestDescriptionDialog'
      );
      wrapper.instance().closeDialog();
      expect(closeRequestDescriptionDialogSpy).toHaveBeenCalled();
    });
  });

  describe('getFlashMessageString', () => {
    it('returns SEND_SUCCESS_MESSAGE if SendingState.COMPLETE', () => {
      const { wrapper } = setup({ sendState: SendingState.COMPLETE });
      expect(wrapper.instance().getFlashMessageString()).toEqual(
        SEND_SUCCESS_MESSAGE
      );
    });
    it('returns SEND_FAILURE_MESSAGE if SendingState.ERROR', () => {
      const { wrapper } = setup({ sendState: SendingState.ERROR });
      expect(wrapper.instance().getFlashMessageString()).toEqual(
        SEND_FAILURE_MESSAGE
      );
    });
    it('returns SEND_INPROGRESS_MESSAGE if SendingState.WAITING', () => {
      const { wrapper } = setup({ sendState: SendingState.WAITING });
      expect(wrapper.instance().getFlashMessageString()).toEqual(
        SEND_INPROGRESS_MESSAGE
      );
    });
    it('returns empty striong if sending state not handled', () => {
      const { wrapper } = setup({ sendState: SendingState.IDLE });
      expect(wrapper.instance().getFlashMessageString()).toEqual('');
    });
  });

  describe('renderFlashMessage', () => {
    let wrapper;
    let mockString;

    beforeAll(() => {
      wrapper = setup().wrapper;
      mockString = 'I am the message';
      jest
        .spyOn(wrapper.instance(), 'getFlashMessageString')
        .mockImplementation(() => mockString);
    });

    it('renders a FlashMessage with correct props', () => {
      const element = wrapper.instance().renderFlashMessage();

      expect(element.props.iconClass).toEqual('icon-mail');
      expect(element.props.message).toBe(mockString);
      expect(element.props.onClose).toEqual(wrapper.instance().closeDialog);
    });
  });

  describe('submitNotification', () => {
    it('calls submitNotification', () => {
      const { props, wrapper } = setup();
      const submitNotificationSpy = jest.spyOn(props, 'submitNotification');
      const { cluster, database, schema, name } = props.tableMetadata;

      wrapper.instance().submitNotification({ preventDefault: jest.fn() });

      expect(submitNotificationSpy).toHaveBeenCalledWith(
        mockFormData.recipients.split(','),
        mockFormData.sender,
        NotificationType.METADATA_REQUESTED,
        {
          comment: mockFormData.comment,
          resource_name: `${schema}.${name}`,
          resource_path: `/table_detail/${cluster}/${database}/${schema}/${name}`,
          description_requested: true,
          fields_requested: false,
        }
      );
    });
  });

  describe('render', () => {
    let wrapper;
    let element;

    describe('when this.props.requestIsOpen', () => {
      describe('no optional props', () => {
        beforeAll(() => {
          const setupResult = setup();
          wrapper = setupResult.wrapper;
        });

        it('renders header title', () => {
          element = wrapper.find('#request-metadata-title');
          expect(element.find('h3').text()).toEqual(TITLE_TEXT);
        });
        it('renders close button', () => {
          element = wrapper.find('#request-metadata-title');
          expect(element.find('button').exists()).toEqual(true);
        });

        it('renders from input with current user', () => {
          element = wrapper.find('#sender-form-group');
          expect(element.find('input').props().value).toEqual('test0@lyft.com');
        });

        it('renders from label', () => {
          element = wrapper.find('#sender-form-group');
          expect(element.find('label').text()).toEqual(FROM_LABEL);
        });
        it('renders from input with current user', () => {
          element = wrapper.find('#sender-form-group');
          expect(element.find('input').props().value).toEqual('test0@lyft.com');
        });

        it('renders to label', () => {
          element = wrapper.find('#recipients-form-group');
          expect(element.find('label').text()).toEqual(TO_LABEL);
        });
        it('renders to input with correct recipients', () => {
          element = wrapper.find('#recipients-form-group');
          expect(element.find('input').props().defaultValue).toEqual(
            'test1@lyft.com, test2@lyft.com'
          );
        });

        it('renders request type label', () => {
          element = wrapper.find('#request-type-form-group');
          expect(element.find('label').at(0).text()).toEqual(REQUEST_TYPE);
        });
        it('renders unchecked table description checkbox', () => {
          element = wrapper.find('#request-type-form-group');
          const label = element.find('label').at(1);
          expect(label.text()).toEqual(TABLE_DESCRIPTION);
          expect(label.find('input').props().defaultChecked).toBe(false);
        });
        it('renders unchecked column descriptions checkbox', () => {
          element = wrapper.find('#request-type-form-group');
          const label = element.find('label').at(2);
          expect(label.text()).toEqual(COLUMN_DESCRIPTIONS);
          expect(label.find('input').props().defaultChecked).toBe(false);
        });

        it('renders additional details label', () => {
          element = wrapper.find('#additional-comments-form-group');
          expect(element.find('label').text()).toEqual(ADDITIONAL_DETAILS);
        });
        it('renders default textarea', () => {
          element = wrapper.find('#additional-comments-form-group');
          const textArea = element.find('textarea');
          expect(textArea.text()).toEqual('');
          expect(textArea.props().required).toBe(false);
          expect(textArea.props().placeholder).toBe(
            COMMENT_PLACEHOLDER_DEFAULT
          );
        });

        it('renders submit button with correct text and icon', () => {
          element = wrapper.find('#submit-request-button');
          expect(element.text()).toEqual(SEND_BUTTON);
          expect(element.find('img').props().className).toEqual(
            'icon icon-send'
          );
        });
      });

      describe('table description requested', () => {
        beforeAll(() => {
          const setupResult = setup({
            requestMetadataType: RequestMetadataType.TABLE_DESCRIPTION,
          });
          wrapper = setupResult.wrapper;
        });
        it('renders checked table description checkbox', () => {
          element = wrapper.find('#request-type-form-group');
          const label = element.find('label').at(1);

          expect(label.find('input').props().defaultChecked).toBe(true);
        });
      });

      describe('column description requested', () => {
        beforeAll(() => {
          const setupResult = setup({
            requestMetadataType: RequestMetadataType.COLUMN_DESCRIPTION,
            columnName: 'Test',
          });
          wrapper = setupResult.wrapper;
        });

        it('renders checked column description checkbox', () => {
          element = wrapper.find('#request-type-form-group');
          const label = element.find('label').at(2);

          expect(label.find('input').props().defaultChecked).toBe(true);
        });

        it('renders textarea for column request', () => {
          element = wrapper.find('#additional-comments-form-group');
          const textArea = element.find('textarea');

          expect(textArea.props().defaultValue).toEqual(
            `${COLUMN_REQUESTED_COMMENT_PREFIX}Test`
          );
          expect(textArea.props().required).toBe(true);
          expect(textArea.props().placeholder).toBe(COMMENT_PLACEHOLDER_COLUMN);
        });
      });
    });

    describe('when !this.props.requestIsOpen', () => {
      beforeAll(() => {
        const setupResult = setup({ requestIsOpen: false });
        wrapper = setupResult.wrapper;
      });

      it('renders nothing', () => {
        expect(wrapper).toEqual({});
      });
    });

    describe('when sendState is not SendingState.IDLE', () => {
      let wrapper;
      let renderFlashMessageMock;

      beforeAll(() => {
        wrapper = setup({
          sendState: SendingState.WAITING,
          requestIsOpen: false,
        }).wrapper;
        renderFlashMessageMock = jest.spyOn(
          wrapper.instance(),
          'renderFlashMessage'
        );
      });

      it('renders results of renderFlashMessage() within component', () => {
        wrapper.instance().render();
        expect(wrapper.props().className).toEqual('request-component');
        expect(renderFlashMessageMock).toHaveBeenCalledTimes(1);
      });
    });
  });

  describe('mapStateToProps', () => {
    let result;
    beforeAll(() => {
      result = mapStateToProps(globalState);
    });

    it('sets userEmail on the props', () => {
      expect(result.userEmail).toEqual(globalState.user.loggedInUser.email);
    });
    it('sets ownerObj on the props', () => {
      expect(result.tableOwners).toEqual(
        Object.keys(globalState.tableMetadata.tableOwners.owners)
      );
    });
    it('sets requestIsOpen on the props', () => {
      expect(result.requestIsOpen).toEqual(
        globalState.notification.requestIsOpen
      );
    });
    it('sets sendState on the props', () => {
      expect(result.sendState).toEqual(globalState.notification.sendState);
    });
    it('sets columnName on the props if it exists in globalState', () => {
      const newState = { ...globalState };
      newState.notification.columnName = 'test_name';
      result = mapStateToProps(newState);
      expect(result.columnName).toEqual(newState.notification.columnName);
    });
    it('sets requestMetadataType on the props if it exists in globalState', () => {
      const newState = { ...globalState };
      newState.notification.requestMetadataType =
        RequestMetadataType.TABLE_DESCRIPTION;
      result = mapStateToProps(newState);
      expect(result.requestMetadataType).toEqual(
        newState.notification.requestMetadataType
      );
    });
  });

  describe('mapDispatchToProps', () => {
    let dispatch;
    let result;
    beforeAll(() => {
      dispatch = jest.fn(() => Promise.resolve());
      result = mapDispatchToProps(dispatch);
    });

    it('sets submitNotification on the props', () => {
      expect(result.submitNotification).toBeInstanceOf(Function);
    });

    it('sets closeRequestDescriptionDialog on the props', () => {
      expect(result.closeRequestDescriptionDialog).toBeInstanceOf(Function);
    });
  });
});
