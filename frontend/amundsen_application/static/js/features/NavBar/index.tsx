// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import * as Avatar from 'react-avatar';
import { RouteComponentProps } from 'react-router';
import { Link, NavLink, withRouter } from 'react-router-dom';
import { connect } from 'react-redux';

import AppConfig from 'config/config';
import { LinkConfig } from 'config/config-types';
import { GlobalState } from 'ducks/rootReducer';
import { Dropdown, MenuItem } from 'react-bootstrap';

import { LoggedInUser } from 'interfaces';

import { logClick } from 'utils/analytics';
import {
  feedbackEnabled,
  indexUsersEnabled,
  getNavLinks,
  getLogoTitle,
} from 'config/config-utils';

import Feedback from 'features/Feedback';
import SearchBar from 'components/SearchBar';

import './styles.scss';

const PROFILE_LINK_TEXT = 'My Profile';

// Props
interface StateFromProps {
  loggedInUser: LoggedInUser;
}

export type NavBarProps = StateFromProps & RouteComponentProps<{}>;

export class NavBar extends React.Component<NavBarProps> {
  generateNavLinks(navLinks: LinkConfig[]) {
    return navLinks.map((link, index) => {
      if (link.use_router) {
        return (
          <NavLink
            className="title-3 border-bottom-white"
            key={index}
            to={link.href}
            target={link.target}
            onClick={logClick}
          >
            {link.label}
          </NavLink>
        );
      }
      return (
        <a
          className="title-3 border-bottom-white"
          key={index}
          href={link.href}
          target={link.target}
          onClick={logClick}
        >
          {link.label}
        </a>
      );
    });
  }

  renderSearchBar = () => {
    if (this.props.location.pathname !== '/') {
      return (
        <div className="nav-search-bar">
          <SearchBar size="small" />
        </div>
      );
    }
    return null;
  };

  render() {
    const { loggedInUser } = this.props;
    const userLink = `/user/${loggedInUser.user_id}?source=navbar`;
    let avatar = <div className="shimmering-circle is-shimmer-animated" />;

    if (loggedInUser.display_name) {
      avatar = <Avatar name={loggedInUser.display_name} size={32} round />;
    }

    return (
      <nav className="container-fluid">
        <div className="row">
          <div className="nav-bar">
            <div id="nav-bar-left" className="nav-bar-left">
              <Link to="/">
                {AppConfig.logoPath && (
                  <img
                    id="logo-icon"
                    className="logo-icon"
                    src={AppConfig.logoPath}
                    alt=""
                  />
                )}
                <span className="title-3">{getLogoTitle()}</span>
              </Link>
            </div>
            {this.renderSearchBar()}
            <div id="nav-bar-right" className="ml-auto nav-bar-right">
              {this.generateNavLinks(getNavLinks())}
              {feedbackEnabled() && <Feedback />}
              {loggedInUser && indexUsersEnabled() && (
                <Dropdown id="user-dropdown" pullRight>
                  <Dropdown.Toggle
                    noCaret
                    className="nav-bar-avatar avatar-dropdown"
                  >
                    {avatar}
                  </Dropdown.Toggle>
                  <Dropdown.Menu className="profile-menu">
                    <div className="profile-menu-header">
                      <div className="title-2">{loggedInUser.display_name}</div>
                      <div>{loggedInUser.email}</div>
                    </div>
                    <MenuItem
                      componentClass={Link}
                      id="nav-bar-avatar-link"
                      to={userLink}
                      href={userLink}
                    >
                      {PROFILE_LINK_TEXT}
                    </MenuItem>
                  </Dropdown.Menu>
                </Dropdown>
              )}
              {loggedInUser && !indexUsersEnabled() && (
                <div className="nav-bar-avatar">{avatar}</div>
              )}
            </div>
          </div>
        </div>
      </nav>
    );
  }
}

export const mapStateToProps = (state: GlobalState) => ({
  loggedInUser: state.user.loggedInUser,
});

export default connect<StateFromProps>(mapStateToProps)(withRouter(NavBar));
