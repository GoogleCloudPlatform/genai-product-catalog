// Copyright 2023 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     https://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

import {Box} from '@mui/material';
import image from '../assets/loader.webp';

export const LoadingIcon = () => {
    return (
        <Box
            sx={{
                position: 'relative',
                width: '100%',
                minHeight: '100%',
                textAlign: 'center',
                paddingTop: '20%',
            }}>
            <img src={image} style={{width: '200px'}}/>
        </Box>
    );
};
