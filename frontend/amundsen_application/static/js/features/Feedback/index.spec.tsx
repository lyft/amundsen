// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';

import { shallow } from 'enzyme';

import BugReportFeedbackForm from './FeedbackForm/BugReportFeedbackForm';
import RatingFeedbackForm from './FeedbackForm/RatingFeedbackForm';
import RequestFeedbackForm from './FeedbackForm/RequestFeedbackForm';
import Feedback, { FeedbackProps, FeedbackType } from '.';
import { BUG_REPORT_TEXT, RATING_TEXT, REQUEST_TEXT } from './constants';

describe('Feedback', () => {
  const setStateSpy = jest.spyOn(Feedback.prototype, 'setState');

  const setup = (propOverrides?: Partial<FeedbackProps>) => {
    const props: FeedbackProps = {
      ...propOverrides,
    };
    const wrapper = shallow<Feedback>(<Feedback {...props} />);
    return { props, wrapper };
  };

  describe('constructor', () => {
    let wrapper;

    beforeAll(() => {
      const setupResult = setup();
      wrapper = setupResult.wrapper;
    });

    it('sets state.isOpen to false', () => {
      expect(wrapper.state().isOpen).toEqual(false);
    });

    it('sets state.content from defaultProps', () => {
      expect(wrapper.state().content).toEqual(Feedback.defaultProps.content);
    });

    it('sets state.feedbackType to FeedbackType.Rating', () => {
      expect(wrapper.state().feedbackType).toEqual(FeedbackType.Rating);
    });
  });

  describe('toggle', () => {
    it('calls setState with negation of state.isOpen', () => {
      setStateSpy.mockClear();
      const { wrapper } = setup();
      const previsOpenState = wrapper.state().isOpen;

      wrapper.instance().toggle();

      expect(setStateSpy).toHaveBeenCalledWith({ isOpen: !previsOpenState });
    });
  });

  describe('changeType', () => {
    let wrapper;

    beforeAll(() => {
      const setupResult = setup();
      wrapper = setupResult.wrapper;
      setStateSpy.mockClear();
    });

    it('returns method that calls setState with correct values if type === FeedbackType.Bug', () => {
      wrapper.instance().changeType(FeedbackType.Bug)();
      expect(setStateSpy).toHaveBeenCalledWith({
        content: <BugReportFeedbackForm />,
        feedbackType: FeedbackType.Bug,
      });
    });

    it('returns method that calls setState with correct values if type === FeedbackType.Rating', () => {
      wrapper.instance().changeType(FeedbackType.Rating)();
      expect(setStateSpy).toHaveBeenCalledWith({
        content: <RatingFeedbackForm />,
        feedbackType: FeedbackType.Rating,
      });
    });

    it('returns method that calls setState with correct values if type === FeedbackType.Request', () => {
      wrapper.instance().changeType(FeedbackType.Request)();
      expect(setStateSpy).toHaveBeenCalledWith({
        content: <RequestFeedbackForm />,
        feedbackType: FeedbackType.Request,
      });
    });
  });

  describe('render', () => {
    describe('if state.isOpen', () => {
      let feedbackIcon;
      let feedbackComponent;
      let props;
      let wrapper;
      let changeTypeSpy;
      let changeTypeMockResult;

      beforeAll(() => {
        const setupResult = setup({ title: 'I am a title' });
        props = setupResult.props;
        wrapper = setupResult.wrapper;
        wrapper.instance().toggle();

        changeTypeMockResult = jest.fn(() => {});
        changeTypeSpy = jest
          .spyOn(wrapper.instance(), 'changeType')
          .mockImplementation(() => changeTypeMockResult);
        wrapper.update();
        feedbackIcon = wrapper.children().at(0);
        feedbackComponent = wrapper.children().at(1);
      });

      it('renders help button with correct props', () => {
        expect(feedbackIcon.exists()).toBe(true);
        expect(feedbackIcon.props().className).toEqual(
          'btn btn-flat-icon feedback-icon is-open'
        );
      });

      it('renders wrapper with correct className', () => {
        expect(feedbackComponent.props().className).toEqual(
          'feedback-component'
        );
      });

      describe('correct feedback-header', () => {
        let button;
        let title;
        beforeAll(() => {
          const header = feedbackComponent.children().at(0);
          title = header.children().at(0);
          button = header.children().at(1);
        });
        it('renders correct title', () => {
          expect(title.text()).toEqual(props.title);
        });

        it('renders close button with correct props', () => {
          expect(button.props()).toMatchObject({
            type: 'button',
            className: 'btn btn-close',
            onClick: wrapper.instance().toggle,
          });
        });
      });

      describe('correct feedback button group', () => {
        let buttonGroupParent;
        let buttonGroup;
        beforeAll(() => {
          buttonGroupParent = feedbackComponent.children().at(1);
          buttonGroup = buttonGroupParent.children().at(0);
        });
        it('renders button group parent with correct className', () => {
          expect(buttonGroupParent.props().className).toEqual('text-center');
        });

        it('renders button group with correct props', () => {
          expect(buttonGroup.props()).toMatchObject({
            className: 'btn-group',
            role: 'group',
          });
        });

        describe('renders correct rating button', () => {
          let button;
          beforeAll(() => {
            wrapper.setState({ feedbackType: FeedbackType.Rating });
            button = wrapper
              .children()
              .at(1)
              .children()
              .at(1)
              .children()
              .at(0)
              .find('button')
              .at(0);
          });
          it('has correct props if active', () => {
            expect(button.props()).toMatchObject({
              type: 'button',
              className: 'btn btn-default active',
              onClick: changeTypeMockResult,
            });
          });

          it('has correct text', () => {
            expect(button.text()).toEqual(RATING_TEXT);
          });

          it('has correct props if not active', () => {
            wrapper.setState({ feedbackType: FeedbackType.Bug });
            button = wrapper
              .children()
              .at(1)
              .children()
              .at(1)
              .children()
              .at(0)
              .find('button')
              .at(0);
            expect(button.props()).toMatchObject({
              type: 'button',
              className: 'btn btn-default',
              onClick: changeTypeMockResult,
            });
          });
        });

        describe('renders correct bug report button', () => {
          let button;
          beforeAll(() => {
            wrapper.setState({ feedbackType: FeedbackType.Bug });
            button = wrapper
              .children()
              .at(1)
              .children()
              .at(1)
              .children()
              .at(0)
              .find('button')
              .at(1);
          });
          it('has correct props if active', () => {
            expect(button.props()).toMatchObject({
              type: 'button',
              className: 'btn btn-default active',
              onClick: changeTypeMockResult,
            });
          });

          it('has correct text', () => {
            expect(button.text()).toEqual(BUG_REPORT_TEXT);
          });

          it('has correct props if not active', () => {
            wrapper.setState({ feedbackType: FeedbackType.Request });
            button = wrapper
              .children()
              .at(1)
              .children()
              .at(1)
              .children()
              .at(0)
              .find('button')
              .at(1);
            expect(button.props()).toMatchObject({
              type: 'button',
              className: 'btn btn-default',
              onClick: changeTypeMockResult,
            });
          });
        });

        describe('renders correct request button', () => {
          let button;
          beforeAll(() => {
            wrapper.setState({ feedbackType: FeedbackType.Request });
            button = wrapper
              .children()
              .at(1)
              .children()
              .at(1)
              .children()
              .at(0)
              .find('button')
              .at(2);
          });
          it('has correct props if active', () => {
            expect(button.props()).toMatchObject({
              type: 'button',
              className: 'btn btn-default active',
              onClick: changeTypeMockResult,
            });
          });

          it('has correct text', () => {
            expect(button.text()).toEqual(REQUEST_TEXT);
          });

          it('has correct props if not active', () => {
            wrapper.setState({ feedbackType: FeedbackType.Rating });
            button = wrapper
              .children()
              .at(1)
              .children()
              .at(1)
              .children()
              .at(0)
              .find('button')
              .at(2);
            expect(button.props()).toMatchObject({
              type: 'button',
              className: 'btn btn-default',
              onClick: changeTypeMockResult,
            });
          });
        });
      });

      /* Note: Using .debug() as a temporary workaround -- do not propagate this pattern.
         Issue: The content are connected components. Enzyme will throw an error if we access that connected component without a Redux store connected.
         Workaround: Use .debug() to check that the string representation of the rendered content is what we expect.
         Future Solution: Connect a mock store OR refactor FeedbackForm to be the connected component on the first place, submitting the form data
                          of its child form and refreshing it.
      */
      it('renders state.content', () => {
        expect(wrapper.children().at(1).children().at(2).debug()).toEqual(
          '<Connect(RatingFeedbackForm) />'
        );
      });

      afterAll(() => {
        changeTypeSpy.mockRestore();
      });
    });

    describe('if !state.isOpen', () => {
      let wrapper;

      beforeAll(() => {
        const setupResult = setup();
        wrapper = setupResult.wrapper;
      });

      it('renders help button with correct props', () => {
        const feedbackIcon = wrapper.children().at(0);
        expect(feedbackIcon.exists()).toBe(true);
        expect(feedbackIcon.props().className).toEqual(
          'btn btn-flat-icon feedback-icon'
        );
      });

      it('does not render expanded form', () => {
        expect(wrapper.children().at(1).exists()).toBe(false);
      });
    });
  });
});
