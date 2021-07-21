import axios, { AxiosResponse } from 'axios';

import { ResourceType, Tag } from 'interfaces';
import { GetDashboardAPI } from 'ducks/dashboard/api/v0';
import { GetFeatureAPI } from 'ducks/feature/api/v0';
import { API_PATH, TableDataAPI } from 'ducks/tableMetadata/api/v0';
import { sortTagsAlphabetical } from 'ducks/utilMethods';

export type AllTagsAPI = {
  msg: string;
  tags: Tag[];
};

export function getAllTags() {
  return axios
    .get('/api/metadata/v0/tags')
    .then((response: AxiosResponse<AllTagsAPI>) =>
      response.data.tags.sort(sortTagsAlphabetical)
    );
}

export function getResourceTags(resourceType, uriKey: string) {
  if (resourceType === ResourceType.table) {
    return axios
      .get(`${API_PATH}/table?key=${uriKey}`)
      .then((response: AxiosResponse<TableDataAPI>) =>
        (response.data.tableData.tags || []).sort(sortTagsAlphabetical)
      );
  }
  if (resourceType === ResourceType.dashboard) {
    return axios
      .get(`${API_PATH}/dashboard?uri=${uriKey}`)
      .then((response: AxiosResponse<GetDashboardAPI>) =>
        (response.data.dashboard.tags || []).sort(sortTagsAlphabetical)
      );
  }
  if (resourceType === ResourceType.feature) {
    return axios
      .get(`${API_PATH}/feature?key=${uriKey}`)
      .then((response: AxiosResponse<GetFeatureAPI>) =>
        (response.data.featureData.tags || []).sort(sortTagsAlphabetical)
      );
  }
}

/* TODO: Typing this method generates redux-saga related type errors that needs more dedicated debugging */
// TODO - Unify this API and split the logic in the Flask layer.
export function updateResourceTag(
  tagObject,
  resourceType: ResourceType,
  uriKey: string
) {
  const updateTagEndpointMap = {
    [ResourceType.table]: `${API_PATH}/update_table_tags`,
    [ResourceType.dashboard]: `${API_PATH}/update_dashboard_tags`,
    [ResourceType.feature]: `${API_PATH}/update_feature_tags`,
  };
  const url = updateTagEndpointMap[resourceType];
  if (url === undefined) {
    throw new Error(`Update Tag not supported for ${resourceType}`);
  }
  return axios({
    url,
    method: tagObject.methodName,
    data: {
      key: uriKey,
      tag: tagObject.tagName,
    },
  });
}
