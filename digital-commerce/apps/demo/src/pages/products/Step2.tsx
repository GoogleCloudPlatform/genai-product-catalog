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
  CardActions,
  CardContent,
  CardHeader,
  FormControlLabel,
  Grid,
  List,
  ListItem,
  Paper,
  Radio,
  RadioGroup,
  Typography,
} from '@mui/material';
import React, { useContext, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import GoogleBackdrop from '../../components/GoogleBackdrop';
import { ConfigurationContext, ProductContext, SessionIDContext } from '../../contexts';

import { api, Category } from 'model';
import AxiosInstance from '../../utils/WebClient';

const initialCategories = () => {
  return new Array<Category>();
};

const Step2 = () => {
  const { sessionID } = useContext(SessionIDContext);
  const { config } = useContext(ConfigurationContext);
  const { product } = useContext(ProductContext);
  const nav = useNavigate();

  const [backdrop, setBackdrop] = useState(false);
  const [categories, setCategories] = useState<Array<Category>>(initialCategories);
  const [selectedCategory, setSelectedCategoy] = useState<number>(-1);

  const categoryLength = categories.length;

  useEffect(() => {
    if (categoryLength === 0) {
      setBackdrop(true);
      let prompt = config.promptDetectCategories;
      prompt = prompt.replace(
        '${category_model}',
        JSON.stringify({
          name: '',
          attributes: [{ name: '', description: '', valueRange: [] }],
        } as Category)
      );

      AxiosInstance.post(`/images`, {
        sessionID: sessionID,
        prompt: prompt,
        value: product.images,
      } as api.ImagePromptRequest)
        .then((resp) => {
          if (resp.status === 200) {
            setCategories([...(resp.data as Category[])]);
            setBackdrop(false);
          }
        })
        .catch((err) => console.error(err));
    }
  }, [setCategories]);

  const handleCategoryChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSelectedCategoy(parseInt(event.target.value));
  };

  const handleClick = () => {
    product.category = categories[selectedCategory];
    nav('/products/3', { replace: true });
  };

  return (
    <React.Fragment>
      <Typography variant="h5" sx={{ mb: 2 }}>
        Choose one of the suggested categories
      </Typography>

      <Grid container spacing={2}>
        <Grid item xs={2}>
          <Paper elevation={1} sx={{ borderRadius: '7px' }}>
            {product.images?.map((image, idx) => (
              <img key={`product_image_${idx}`} src={image.uri} style={{ width: '100%', objectFit: 'contain' }} />
            ))}
          </Paper>
        </Grid>
        <Grid item xs={10}>
          <React.Fragment>
            <Grid container spacing={2}>
              <Grid item xs={6}>
                <Card raised={true} sx={{ borderRadius: '7px' }}>
                  <CardHeader title="Categories" />
                  <CardContent>
                    <RadioGroup onChange={handleCategoryChange}>
                      {categories.map((c: Category, idx) => (
                        <FormControlLabel key={`cat_sel_${idx}`} value={idx} control={<Radio />} label={c.name} />
                      ))}
                    </RadioGroup>
                  </CardContent>
                  <CardActions sx={{ justifyContent: 'right' }}>
                    <Button variant="contained" disabled={selectedCategory === -1} onClick={handleClick}>
                      Next
                    </Button>
                  </CardActions>
                </Card>
              </Grid>
              <Grid item xs={6}>
                <Card sx={{ borderRadius: '7px' }}>
                  <CardHeader
                    title="Attributes"
                    subheader={selectedCategory > -1 ? categories[selectedCategory].name : ''}
                  />
                  <CardContent>
                    <List>
                      {selectedCategory > -1 ? (
                        categories[selectedCategory].attributes?.map((attr, attrIdx) => (
                          <ListItem key={`cat_attr_li_${attrIdx}`}>
                            <Box>
                              {attr.name} - {attr.description}
                              {attr.valueRange.length > 0 ? (
                                <>
                                  <br />
                                  <Typography variant="body2">{attr.valueRange.join(', ')}</Typography>
                                </>
                              ) : (
                                <></>
                              )}
                            </Box>
                          </ListItem>
                        ))
                      ) : (
                        <></>
                      )}
                    </List>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </React.Fragment>
        </Grid>
      </Grid>
      <GoogleBackdrop backdrop={backdrop} setBackdrop={setBackdrop} />
    </React.Fragment>
  );
};

export default Step2;
