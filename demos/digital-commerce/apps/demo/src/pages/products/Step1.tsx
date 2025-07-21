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

import {Box, Grid, IconButton, Stack, Typography} from '@mui/material';

import React from 'react';
import apparel from '../../assets/apparel.jpeg';
import beauty from '../../assets/beauty.jpeg';
import headphones from '../../assets/headphones.jpeg';
import sofa from '../../assets/sofa.jpeg';
import jewelry from '../../assets/jewelry.jpeg';
import mustard from '../../assets/mustard.jpeg';
import ImageCard from '../../components/ImageCard';
import VideoCameraBackIcon from '@mui/icons-material/VideoCameraBack';
import {useNavigate} from 'react-router-dom';

const Step1 = () => {
    const navigate = useNavigate();

    return (
        <React.Fragment>
            <Box sx={{display: 'flex', justifyContent: 'center'}}>
                <Stack>
                    <Grid container>
                        <Grid size={6}>
                            <Typography variant="h5" sx={{mb: 2}}>
                                Select an potential product image
                            </Typography>
                        </Grid>
                        <Grid size={6}>
                            <Box sx={{display: 'flex', justifyContent: 'right'}}>
                                <IconButton size="medium"
                                            onClick={() => navigate('/products/video-setup')}><VideoCameraBackIcon/></IconButton>
                            </Box>
                        </Grid>
                    </Grid>

                    <Grid container spacing={2} maxWidth={'800px'}>
                        <ImageCard title="Apparel" img={apparel}/>
                        <ImageCard title="Beauty" img={beauty}/>
                        <ImageCard title="Electronics" img={headphones}/>
                        <ImageCard title="Furniture" img={sofa}/>
                        <ImageCard title="Jewelry" img={jewelry}/>
                        <ImageCard title="Grocery" img={mustard}/>
                    </Grid>
                </Stack>
            </Box>
        </React.Fragment>
    );
};

export default Step1;
