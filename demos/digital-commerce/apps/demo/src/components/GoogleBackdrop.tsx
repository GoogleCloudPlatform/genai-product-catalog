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

import {Backdrop} from '@mui/material';
import loader from '../assets/loader.webp';

const GoogleBackdrop = ({backdrop, setBackdrop}: { backdrop: boolean; setBackdrop: (value: boolean) => void }) => {
    const clearBackdrop = () => {
        setBackdrop(false);
    };

    return (
        <Backdrop sx={{color: '#fff', zIndex: (theme) => theme.zIndex.drawer + 1}} open={backdrop}
                  onClick={clearBackdrop}>
            <img src={loader} style={{maxWidth: '150px', borderRadius: '100px'}}/>
        </Backdrop>
    );
};

export default GoogleBackdrop;
