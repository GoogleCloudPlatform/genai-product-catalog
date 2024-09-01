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

import {
    Box,
    Button,
    Card,
    CardContent,
    CardHeader,
    CardMedia,
    Dialog,
    DialogContent,
    DialogTitle,
    Grid,
    Stack,
    TextField,
    Typography,
} from '@mui/material';
import React, {useState} from 'react';
import {Product} from 'model';
import Agent from './Agent';
import {useFormik} from 'formik';
import * as Yup from 'yup';

const ProductPreview = React.lazy(() => import('./ProductPreview'));

const ProductDetail = ({product}: { product: Product }) => {
    const [preview, setPreview] = useState<boolean>(false);
    const [assistant, setAssistant] = useState<boolean>(false);

    const handleClickOpen = () => {
        setPreview(true);
    };

    const handleClose = () => {
        setPreview(false);
    };

    const productSchema = Yup.object().shape({
        base: Yup.object().shape({
            name: Yup.string().min(5).required('Required'),
            description: Yup.string().min(5).required('Required'),
        })
    });

    const formik = useFormik<Product>({
        initialValues: product,
        validationSchema: productSchema,
        onSubmit: async (values: Product) => {
            console.log(JSON.stringify(values))
        }
    });

    return (
        <form method="post" onSubmit={formik.handleSubmit}>
            <Grid container spacing={2}>
                <Grid item xs={4}>
                    <Stack>
                        <Box>
                            <Card>
                                {formik.values.images && formik.values.images.length > 0 && formik.values.images[0].uri ? (
                                    <CardMedia sx={{height: '200px', mb: 0, pb: 0}}
                                               image={formik.values.images[0].uri}/>
                                ) : (
                                    <></>
                                )}
                                <CardHeader title="SEO"/>
                                <CardContent>
                                    <TextField
                                        fullWidth
                                        name="base.seoHtmlHeader"
                                        label="SEO Header"
                                        variant="outlined"
                                        InputLabelProps={{shrink: true}}
                                        multiline
                                        rows={5}
                                        value={formik.values.base.seoHtmlHeader}
                                        error={formik.touched.base?.seoHtmlHeader && Boolean(formik.errors.base?.seoHtmlHeader)}
                                        onChange={formik.handleChange}
                                        onBlur={formik.handleBlur}
                                    />
                                </CardContent>
                            </Card>
                        </Box>
                        <Stack direction={'row'} spacing={2} sx={{pt: 2}}>
                            <Button fullWidth onClick={() => setAssistant(true)}>
                                Digital Assistant
                            </Button>
                            <Button fullWidth onClick={handleClickOpen}>
                                Preview
                            </Button>
                        </Stack>
                    </Stack>
                </Grid>
                <Grid item xs={8}>
                    <Stack spacing={2}>
                        <TextField
                            fullWidth
                            label="Name"
                            InputLabelProps={{shrink: true}}
                            variant="outlined"
                            name="base.name"
                            value={formik.values.base.name}
                            error={formik.touched.base?.name && Boolean(formik.errors.base?.name)}
                            onChange={formik.handleChange}
                            onBlur={formik.handleBlur}
                        />

                        <TextField
                            fullWidth
                            name="base.description"
                            label="Description"
                            InputLabelProps={{shrink: true}}
                            variant="outlined"
                            multiline
                            rows={10}
                            type="text"
                            value={formik.values.base.description}
                            error={formik.touched.base?.description && Boolean(formik.errors.base?.description)}
                            onChange={formik.handleChange}
                            onBlur={formik.handleBlur}
                        />

                        <Typography variant="h5">Attributes</Typography>

                        <Grid container spacing={2}>

                            {product && product.base.attributeValues ? (
                                product.base.attributeValues.map((v, vIdx) => (
                                    <Grid key={`cat_attr_grd_${vIdx}`} item xs={4}>
                                        <TextField
                                            key={`cat_attr_val_${vIdx}`}
                                            fullWidth
                                            label={v.name}
                                            InputLabelProps={{shrink: true}}
                                            variant="outlined"
                                            value={v.value}
                                        />
                                    </Grid>
                                ))
                            ) : (
                                <></>
                            )}

                        </Grid>
                    </Stack>
                </Grid>
            </Grid>

            <Dialog open={preview} onClose={handleClose} maxWidth="lg">
                <DialogTitle>{'Preview'}</DialogTitle>
                <DialogContent>
                    <ProductPreview img={formik.values.images[0]} category={formik.values.category}
                                    base={formik.values.base}/>
                </DialogContent>
            </Dialog>

            <Agent open={assistant} setOpen={setAssistant}/>
        </form>
    );
};

export default ProductDetail;
