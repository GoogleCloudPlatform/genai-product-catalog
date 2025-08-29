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

import React from 'react';
import {Grid, Skeleton, Typography} from '@mui/material';
import {BaseProduct, Category, Image} from 'model';

const MarkdownPreview = React.lazy(() => import('@uiw/react-markdown-preview/nohighlight'));

const ProductPreview = ({img, category, base}: { img: Image; category: Category; base: BaseProduct }) => {
    return (
        <React.Fragment>
            <Grid container>
                <Grid size={4}>
                    {(img && img.uri) ?
                        <img src={img.uri} style={{maxWidth: '250px'}}/> :
                        <Skeleton variant='rounded'/>
                    }
                </Grid>
                <Grid size={8}>
                    <Typography variant="h5">{base.name}</Typography>
                    {(category && category.name) ? <Typography variant="body2">{category.name}</Typography> : <></>}


                    <MarkdownPreview source={base.description}
                                     style={{backgroundColor: '#fff', color: '#666', marginBottom: '2em'}}/>

                    <Typography variant='h6'>Attributes</Typography>
                    <Grid container>
                        {base.attributeValues.map((av, idx) => (
                            <Grid size={4} key={`av_idx_${idx}`}>
                                <Grid container spacing={1}>
                                    <Grid size={4}>
                                        <Typography variant='body2' sx={{fontWeight: 'bold'}}>{av.name}</Typography>
                                    </Grid>
                                    <Grid size={8}>
                                        <Typography variant='body2'>{av.value}</Typography>
                                    </Grid>
                                </Grid>
                            </Grid>
                        ))}
                    </Grid>
                </Grid>
            </Grid>
        </React.Fragment>
    );
};

export default ProductPreview;
