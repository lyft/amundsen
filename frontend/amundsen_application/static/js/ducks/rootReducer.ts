// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import { combineReducers } from 'redux';

import dashboard, { DashboardReducerState } from 'ducks/dashboard/reducer';
import feature, { FeatureReducerState } from 'ducks/feature/reducer';
import announcements, { AnnouncementsReducerState } from './announcements';
import feedback, { FeedbackReducerState } from './feedback/reducer';
import popularResources, {
  PopularResourcesReducerState,
} from './popularResources/reducer';
import search, { SearchReducerState } from './search/reducer';
import tableMetadata, {
  TableMetadataReducerState,
} from './tableMetadata/reducer';
import lastIndexed, { LastIndexedReducerState } from './lastIndexed/reducer';
import tags, { TagsReducerState } from './tags/reducer';
import user, { UserReducerState } from './user/reducer';
import ui, { UIReducerState } from './ui';
import bookmarks, { BookmarkReducerState } from './bookmark/reducer';
import notification, { NotificationReducerState } from './notification/reducer';
import issue, { IssueReducerState } from './issue/reducer';
import lineage, { LineageReducerState } from './lineage/reducer';

export interface GlobalState {
  announcements: AnnouncementsReducerState;
  bookmarks: BookmarkReducerState;
  dashboard: DashboardReducerState;
  feature: FeatureReducerState;
  feedback: FeedbackReducerState;
  issue: IssueReducerState;
  notification: NotificationReducerState;
  popularResources: PopularResourcesReducerState;
  search: SearchReducerState;
  tableMetadata: TableMetadataReducerState;
  lastIndexed: LastIndexedReducerState;
  tags: TagsReducerState;
  user: UserReducerState;
  ui: UIReducerState;
  lineage: LineageReducerState;
}

const rootReducer = combineReducers<GlobalState>({
  announcements,
  bookmarks,
  dashboard,
  feature,
  feedback,
  issue,
  notification,
  popularResources,
  search,
  tableMetadata,
  lastIndexed,
  tags,
  user,
  ui,
  lineage,
});

export default rootReducer;

export type RootState = ReturnType<typeof rootReducer>;
