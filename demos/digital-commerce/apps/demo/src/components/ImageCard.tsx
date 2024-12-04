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

import {Box, Button, Card, CardContent, CardMedia, Grid, Typography} from '@mui/material';
import {useContext} from 'react';
import {useNavigate} from 'react-router-dom';
import {Image, utils} from 'model';
import {ProductContext} from '../contexts';

type ImageCardArgs = {
    title: string;
    img: string;
};

const ImageCard = ({title, img}: ImageCardArgs) => {
    const {product} = useContext(ProductContext);
    const nav = useNavigate();

    const handleClick = (img: string) => {
        utils.imageToBase64(img, (image: Image) => {
            product.images[0] = image;
            nav('/products/2');
        });
    };

    return (
        <Grid item xs={4}>
            <Card sx={{maxWidth: '230px', mb: 2, borderRadius: '30px', backgroundColor: 'primary.dark'}} raised={true}>
                <CardMedia sx={{height: '200px', mb: 0, pb: 0, borderRadius: '0px'}} image={img} title={title}/>
                <CardContent>
                    <Box sx={{display: 'flex', justifyContent: 'center'}}>
                        <Button onClick={() => handleClick(img)}>
                            <Typography variant="body2" color={'primary.contrastText'}>{title}</Typography>
                        </Button>
                    </Box>
                </CardContent>
            </Card>
        </Grid>
    );
};

export default ImageCard;
