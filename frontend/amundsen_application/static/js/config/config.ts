import { AppConfig } from './config-types';
import configDefault from './config-default';
import configCustom from './config-custom';

// This is not a shallow merge. Any defined members of customConfig will override configDefault.
const appConfig: AppConfig = { ...configDefault, ...configCustom };

export default appConfig;
