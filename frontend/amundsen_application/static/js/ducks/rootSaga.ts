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
import { getAnnouncementsWatcher } from './announcements/sagas';

// Notifications
import { submitNotificationWatcher } from './notification/sagas';

// FeedbackForm
import { submitFeedbackWatcher } from './feedback/sagas';

// Issues
import { createIssueWatcher, getIssuesWatcher } from './issue/sagas';

// PopularTables
import { getPopularTablesWatcher } from './popularTables/sagas';
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
  getTableQualityChecksWatcher,
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
    // PopularTables
    getPopularTablesWatcher(),
    // Tags
    getAllTagsWatcher(),
    updateResourceTagsWatcher(),
    // TableDetail
    getTableDataWatcher(),

    getColumnDescriptionWatcher(),

    getPreviewDataWatcher(),
    getTableDescriptionWatcher(),
    getTableQualityChecksWatcher(),
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
