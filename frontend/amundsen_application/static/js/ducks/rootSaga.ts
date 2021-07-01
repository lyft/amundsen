import { all } from 'redux-saga/effects';

// AnnouncementPage

import {
  addBookmarkWatcher,
  getBookmarksForUserWatcher,
  getBookmarksWatcher,
  removeBookmarkWatcher,
} from 'ducks/bookmark/sagas';

// Dashboard
import { getDashboardWatcher } from 'ducks/dashboard/sagas';
import {
  getFeatureWatcher,
  getFeatureCodeWatcher,
  getFeatureDescriptionWatcher,
  getFeatureLineageWatcher,
  updateFeatureDescriptionWatcher,
  updateFeatureOwnerWatcher,
  getFeaturePreviewDataWatcher,
} from 'ducks/feature/sagas';

import { getAnnouncementsWatcher } from './announcements/sagas';

// Notifications
import { submitNotificationWatcher } from './notification/sagas';

// Feature

// FeedbackForm
import { submitFeedbackWatcher } from './feedback/sagas';

// Issues
import { createIssueWatcher, getIssuesWatcher } from './issue/sagas';

// PopularResources
import { getPopularResourcesWatcher } from './popularResources/sagas';
// Search
import {
  inlineSearchWatcher,
  inlineSearchWatcherDebounce,
  loadPreviousSearchWatcher,
  searchAllWatcher,
  searchResourceWatcher,
  selectInlineResultsWatcher,
  submitSearchWatcher,
  submitSearchResourceWatcher,
  updateSearchStateWatcher,
  urlDidUpdateWatcher,
} from './search/sagas';
import { filterWatcher } from './search/filters/sagas';

// TableDetail
import { updateTableOwnerWatcher } from './tableMetadata/owners/sagas';
import {
  getTableDataWatcher,
  getColumnDescriptionWatcher,
  getPreviewDataWatcher,
  getTableDescriptionWatcher,
  updateColumnDescriptionWatcher,
  updateTableDescriptionWatcher,
} from './tableMetadata/sagas';

// LastIndexed
import { getLastIndexedWatcher } from './lastIndexed/sagas';

// Tags
import { getAllTagsWatcher, updateResourceTagsWatcher } from './tags/sagas';

// User
import {
  getLoggedInUserWatcher,
  getUserOwnWatcher,
  getUserReadWatcher,
  getUserWatcher,
} from './user/sagas';

// Lineage
import {
  getColumnLineageWatcher,
  getTableLineageWatcher,
  getTableColumnLineageWatcher,
} from './lineage/sagas';

export default function* rootSaga() {
  yield all([
    // AnnouncementPage
    getAnnouncementsWatcher(),
    // Bookmarks
    addBookmarkWatcher(),
    getBookmarksForUserWatcher(),
    getBookmarksWatcher(),
    removeBookmarkWatcher(),
    // Dashboard
    getDashboardWatcher(),
    // Notification
    submitNotificationWatcher(),
    // Feature
    getFeatureWatcher(),
    getFeatureCodeWatcher(),
    getFeatureLineageWatcher(),
    getFeaturePreviewDataWatcher(),
    getFeatureDescriptionWatcher(),
    updateFeatureDescriptionWatcher(),
    updateFeatureOwnerWatcher(),
    // FeedbackForm
    submitFeedbackWatcher(),
    // Issues
    getIssuesWatcher(),
    createIssueWatcher(),
    // Search
    filterWatcher(),
    inlineSearchWatcher(),
    inlineSearchWatcherDebounce(),
    loadPreviousSearchWatcher(),
    searchAllWatcher(),
    searchResourceWatcher(),
    selectInlineResultsWatcher(),
    submitSearchWatcher(),
    submitSearchResourceWatcher(),
    updateSearchStateWatcher(),
    urlDidUpdateWatcher(),
    // PopularResources
    getPopularResourcesWatcher(),
    // Tags
    getAllTagsWatcher(),
    updateResourceTagsWatcher(),
    // TableDetail
    getTableDataWatcher(),

    getColumnDescriptionWatcher(),

    getPreviewDataWatcher(),
    getTableDescriptionWatcher(),
    updateColumnDescriptionWatcher(),
    updateTableDescriptionWatcher(),
    updateTableOwnerWatcher(),
    // LastIndexed
    getLastIndexedWatcher(),
    // User
    getLoggedInUserWatcher(),
    getUserWatcher(),
    getUserOwnWatcher(),
    getUserReadWatcher(),
    // Lineage
    getTableLineageWatcher(),
    getColumnLineageWatcher(),
    getTableColumnLineageWatcher(),
  ]);
}
