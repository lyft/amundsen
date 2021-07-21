import { UpdateMethod } from './Enums';

export interface UpdateTagData {
  methodName: UpdateMethod;
  tagName: string;
}

export enum TagType {
  TAG = 'default',
}

export interface Tag {
  tag_count?: number;
  tag_name: string;
  tag_type?: TagType.TAG;
}
