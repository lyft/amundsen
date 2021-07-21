// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { bindActionCreators } from 'redux';
import { RouteComponentProps } from 'react-router';
import { withRouter } from 'react-router-dom';
import { connect } from 'react-redux';

import { GlobalState } from 'ducks/rootReducer';
import {
  submitSearch,
  getInlineResultsDebounce,
  selectInlineResult,
} from 'ducks/search/reducer';
import {
  SubmitSearchRequest,
  InlineSearchRequest,
  InlineSearchSelect,
} from 'ducks/search/types';

import { ResourceType } from 'interfaces';

import InlineSearchResults from './InlineSearchResults';

import './styles.scss';

import * as Constants from './constants';

export interface StateFromProps {
  searchTerm: string;
}

export interface DispatchFromProps {
  clearSearch?: () => void;
  submitSearch: (searchTerm: string) => SubmitSearchRequest;
  onInputChange: (term: string) => InlineSearchRequest;
  onSelectInlineResult: (
    resourceType: ResourceType,
    searchTerm: string,
    updateUrl: boolean
  ) => InlineSearchSelect;
}

export interface OwnProps {
  placeholder?: string;
  size?: string;
}

export type SearchBarProps = StateFromProps &
  DispatchFromProps &
  OwnProps &
  RouteComponentProps<{}>;

interface SearchBarState {
  showTypeAhead: boolean;
  searchTerm: string;
}

export class SearchBar extends React.Component<SearchBarProps, SearchBarState> {
  private refToSelf: React.RefObject<HTMLDivElement>;

  public static defaultProps: Partial<SearchBarProps> = {
    placeholder: Constants.PLACEHOLDER_DEFAULT,
    size: '',
  };

  constructor(props) {
    super(props);
    this.refToSelf = React.createRef<HTMLDivElement>();

    this.state = {
      showTypeAhead: false,
      searchTerm: this.props.searchTerm,
    };
  }

  clearSearchTerm = (): void => {
    this.setState({ showTypeAhead: false, searchTerm: '' });

    /*
      This method fires when the searchTerm is empty to re-execute a search.
      This should only be applied on the SearchPage route to keep the results
      up-to-date as the user refines their search interacting back & forth with
      the filter UI & SearchBar
    */
    if (this.props.clearSearch) {
      this.props.clearSearch();
    }
  };

  componentDidMount = () => {
    document.addEventListener('mousedown', this.updateTypeAhead, false);
  };

  componentWillUnmount = () => {
    document.removeEventListener('mousedown', this.updateTypeAhead, false);
  };

  componentDidUpdate = (prevProps: SearchBarProps) => {
    const { searchTerm } = this.props;

    if (searchTerm !== prevProps.searchTerm) {
      this.setState({ searchTerm });
    }
  };

  handleValueChange = (event: React.SyntheticEvent<HTMLInputElement>): void => {
    const searchTerm = (event.target as HTMLInputElement).value.toLowerCase();

    if (this.isFormValid(searchTerm)) {
      if (searchTerm.length > 0) {
        this.props.onInputChange(searchTerm);
        this.setState({ searchTerm, showTypeAhead: true });
      } else {
        this.clearSearchTerm();
      }
    } else {
      this.setState({ searchTerm, showTypeAhead: false });
    }
  };

  handleValueSubmit = (event: React.FormEvent<HTMLFormElement>): void => {
    const searchTerm = this.state.searchTerm.trim();
    event.preventDefault();

    if (this.isFormValid(searchTerm)) {
      const { submitSearch } = this.props;

      submitSearch(searchTerm);
      this.hideTypeAhead();
    }
  };

  hideTypeAhead = (): void => {
    this.setState({ showTypeAhead: false });
  };

  isFormValid = (searchTerm: string): boolean => {
    const form = document.getElementById('search-bar-form') as HTMLFormElement;
    const input = document.getElementById('search-input') as HTMLInputElement;
    const isValid = searchTerm.indexOf(':') < 0;

    /* This will set the error message, it must be explicitly set or cleared each time */
    input.setCustomValidity(isValid ? '' : Constants.INVALID_SYNTAX_MESSAGE);

    if (searchTerm.length > 0) {
      /* This will show the error message */
      form.reportValidity();
    }

    return isValid;
  };

  onSelectInlineResult = (
    resourceType: ResourceType,
    updateUrl: boolean = false
  ): void => {
    this.hideTypeAhead();
    this.props.onSelectInlineResult(
      resourceType,
      this.state.searchTerm,
      updateUrl
    );
  };

  shouldShowTypeAhead = (searchTerm: string): boolean => searchTerm.length > 0;

  updateTypeAhead = (event: Event): void => {
    /* This logic will hide/show the inline results component when the user clicks
      outside/inside of the search bar */
    if (
      this.refToSelf.current &&
      this.refToSelf.current.contains(event.target as Node)
    ) {
      this.setState({
        showTypeAhead: this.shouldShowTypeAhead(this.state.searchTerm),
      });
    } else {
      this.hideTypeAhead();
    }
  };

  render() {
    const inputClass = `${
      this.props.size === Constants.SIZE_SMALL
        ? 'text-title-w2 small'
        : 'text-headline-w2 large'
    } search-bar-input form-control`;
    const searchButtonClass = `btn btn-flat-icon search-button ${
      this.props.size === Constants.SIZE_SMALL ? 'small' : 'large'
    }`;

    return (
      <div id="search-bar" className="search-bar" ref={this.refToSelf}>
        <form
          id="search-bar-form"
          className="search-bar-form"
          onSubmit={this.handleValueSubmit}
        >
          {/* eslint-disable jsx-a11y/no-autofocus */}
          <label className="sr-only">{this.props.placeholder}</label>
          <input
            id="search-input"
            required
            className={inputClass}
            value={this.state.searchTerm}
            onChange={this.handleValueChange}
            placeholder={this.props.placeholder}
            autoFocus
            autoComplete="off"
          />
          {/* eslint-enable jsx-a11y/no-autofocus */}
          <button className={searchButtonClass} type="submit">
            <span className="sr-only">{Constants.SEARCH_BUTTON_TEXT}</span>
            <img className="icon icon-search" alt="" />
          </button>
          {this.props.size === Constants.SIZE_SMALL && (
            <button
              type="button"
              className="btn btn-close clear-button"
              onClick={this.clearSearchTerm}
            >
              <span className="sr-only">{Constants.BUTTON_CLOSE_TEXT}</span>
            </button>
          )}
        </form>
        {this.state.showTypeAhead && (
          // @ts-ignore: Investigate proper configuration for 'className' to be valid by default on custom components
          <InlineSearchResults
            className={this.props.size === Constants.SIZE_SMALL ? 'small' : ''}
            onItemSelect={this.onSelectInlineResult}
            searchTerm={this.state.searchTerm}
          />
        )}
      </div>
    );
  }
}

export const mapStateToProps = (state: GlobalState): StateFromProps => ({
  searchTerm: state.search.search_term,
});

export const mapDispatchToProps = (
  dispatch: any,
  ownProps
): DispatchFromProps => {
  /* These values activate behavior only applicable on SearchPage */
  const useFilters = ownProps.history.location.pathname === '/search';
  const updateStateOnClear = ownProps.history.location.pathname === '/search';

  const dispatchableActions: DispatchFromProps = bindActionCreators(
    {
      clearSearch: () => submitSearch({ useFilters, searchTerm: '' }),
      submitSearch: (searchTerm: string) =>
        submitSearch({ searchTerm, useFilters }),
      onInputChange: getInlineResultsDebounce,
      onSelectInlineResult: selectInlineResult,
    },
    dispatch
  );

  // Tricky: we want to clear this property, but the bindActionCreators convenience
  // wrapper won't allow undefined values, so clear it after.
  if (!updateStateOnClear) {
    dispatchableActions.clearSearch = undefined;
  }

  return dispatchableActions;
};

export default withRouter(
  connect<StateFromProps, DispatchFromProps, OwnProps>(
    mapStateToProps,
    mapDispatchToProps
  )(SearchBar)
);
