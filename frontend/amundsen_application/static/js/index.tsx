// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import 'core-js/stable';

import * as React from 'react';
import * as ReactDOM from 'react-dom';
import * as ReduxPromise from 'redux-promise';
import createSagaMiddleware from 'redux-saga';
import { Provider } from 'react-redux';
import { createStore, applyMiddleware } from 'redux';
import { Router, Route, Switch } from 'react-router-dom';
import DocumentTitle from 'react-document-title';

import { getDocumentTitle } from 'config/config-utils';

import { analyticsMiddleware } from 'ducks/middlewares';

import { BrowserHistory } from 'utils/navigationUtils';

import { pageViewed } from 'ducks/ui';
import rootReducer from 'ducks/rootReducer';
import rootSaga from 'ducks/rootSaga';

import AnnouncementPage from './pages/AnnouncementPage';
import BrowsePage from './pages/BrowsePage';
import DashboardPage from './pages/DashboardPage';
import FeaturePage from './pages/FeaturePage';
import HomePage from './pages/HomePage';
import NotFoundPage from './pages/NotFoundPage';
import SearchPage from './pages/SearchPage';
import ProfilePage from './pages/ProfilePage';
import TableDetail from './pages/TableDetailPage';
import LineagePage from './pages/LineagePage';

import Preloader from './components/Preloader';
import Footer from './features/Footer';
import NavBar from './features/NavBar';

const sagaMiddleware = createSagaMiddleware();
const createStoreWithMiddleware = applyMiddleware(
  ReduxPromise,
  analyticsMiddleware,
  sagaMiddleware
)(createStore);
const store = createStoreWithMiddleware(rootReducer);

sagaMiddleware.run(rootSaga);

const Routes: React.FC = () => {
  const history = BrowserHistory;

  function trackPageView() {
    store.dispatch(pageViewed(window.location.pathname));
  }

  React.useEffect(() => {
    trackPageView(); // To track the first pageview upon load
    history.listen(trackPageView); // To track the subsequent pageviews
  }, [history]);

  return (
    <>
      <Route component={NavBar} />
      <Switch>
        <Route path="/announcements" component={AnnouncementPage} />
        <Route path="/browse" component={BrowsePage} />
        <Route path="/dashboard/:uri" component={DashboardPage} />
        <Route path="/feature/:group/:name/:version" component={FeaturePage} />
        <Route path="/search" component={SearchPage} />
        <Route
          path="/table_detail/:cluster/:database/:schema/:table"
          component={TableDetail}
        />
        <Route
          path="/lineage/:resource/:cluster/:database/:schema/:table"
          component={LineagePage}
        />
        <Route path="/user/:userId" component={ProfilePage} />
        <Route path="/404" component={NotFoundPage} />
        <Route path="/" component={HomePage} />
      </Switch>
    </>
  );
};

ReactDOM.render(
  <DocumentTitle title={getDocumentTitle()}>
    <Provider store={store}>
      <Router history={BrowserHistory}>
        <div id="main">
          <Preloader />
          <Routes />
          <Footer />
        </div>
      </Router>
    </Provider>
  </DocumentTitle>,
  document.getElementById('content') || document.createElement('div')
);
