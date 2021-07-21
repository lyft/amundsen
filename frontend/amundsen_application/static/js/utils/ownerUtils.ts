import { OwnerDict, ResourceType, UpdateOwnerPayload, User } from 'interfaces';
import { indexUsersEnabled } from 'config/config-utils';
import { OwnerItemProps } from 'components/OwnerEditor';
import * as API from 'ducks/tableMetadata/api/v0';

/**
 * Converts a list of Users to a dictionary of users OwnersDict
 */
export function getOwnersDictFromUsers(owners: User[]): OwnerDict {
  const ownerObj = owners.reduce((resultObj, currentOwner) => {
    resultObj[currentOwner.user_id] = currentOwner as User;
    return resultObj;
  }, {});
  return ownerObj;
}

/**
 * Converts a list of Users to OwnerItemProps
 */
export function getOwnerItemPropsFromUsers(
  owners: User[],
  profileLinkSource: string
): OwnerItemProps {
  return owners.reduce((obj, user) => {
    const { profile_url, user_id, display_name } = user;
    let profileLink = profile_url;
    let isExternalLink = true;
    if (indexUsersEnabled()) {
      isExternalLink = false;
      profileLink = `/user/${user_id}?source=${profileLinkSource}`;
    }
    return {
      ...obj,
      [user_id]: {
        label: display_name,
        link: profileLink,
        isExternal: isExternalLink,
      },
    };
  }, {});
}

/**
 * Creates axios payload for the request to update an owner
 */
export function createOwnerUpdatePayload(
  resourceType: ResourceType,
  resourceKey: string,
  payload: UpdateOwnerPayload
) {
  const updateOwnerEndpointMap = {
    [ResourceType.table]: `${API.API_PATH}/update_table_owner`,
    [ResourceType.feature]: `${API.API_PATH}/update_feature_owner`,
  };
  const url = updateOwnerEndpointMap[resourceType];
  if (url === undefined) {
    throw new Error(`Update Owner not supported for ${resourceType}`);
  }
  return {
    url,
    method: payload.method,
    data: {
      key: resourceKey,
      owner: payload.id,
    },
  };
}
