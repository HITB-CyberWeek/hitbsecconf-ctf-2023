import type { AdminConfig } from '@keystone-6/core/types';
import { CustomNavigation } from './components/CustomNavigation';
import { jsx } from '@keystone-ui/core';

function CustomLogo() {
    return (<h3>Lockstone</h3>)
}

export const components: AdminConfig['components']= {
    Logo: CustomLogo,
    Navigation: CustomNavigation,
};
