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

import React, { ReactNode, Suspense, useContext, useEffect, useMemo, useState } from 'react';

import {
  Box,
  Fab,
  FormControl,
  Grid,
  InputLabel,
  MenuItem,
  Select,
  SelectChangeEvent,
  Stack,
  Typography,
  Tab,
  Tabs,
} from '@mui/material';

import AddIcon from '@mui/icons-material/Add';
import GoogleBackdrop from '../../components/GoogleBackdrop';
import { api, Attribute, BaseProduct, languages, Product, ProductAttributeValue } from 'model';
import { ConfigurationContext, ProductContext, SessionIDContext } from '../../contexts';
import AxiosInstance from '../../utils/WebClient';

const ProductDetail = React.lazy(() => import('../../components/ProductDetail'));

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const a11yProps = (index: number) => {
  return {
    id: `ph-tab-${index}`,
    'aria-controls': `ph-tabpanel-${index}`,
  };
};

const ProductTabPanel = (props: TabPanelProps) => {
  const { children, value, index, ...other } = props;
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`ph-tabpanel-${index}`}
      aria-labelledby={`ph-tab-${index}`}
      {...other}>
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
};

const Step3 = () => {
  const { sessionID } = useContext(SessionIDContext);
  const { product, setProduct } = useContext(ProductContext);
  const { config } = useContext(ConfigurationContext);

  const [backdrop, setBackdrop] = useState(false);
  const [language, setLanguage] = useState<string>(() => config.defaultLanguage);
  const [selectedTab, setSelectedTab] = useState<number>(0);

  const handleTabChange = (_: React.SyntheticEvent, newValue: number) => {
    if (newValue === 0) {
      setLanguage(product.base.language);
    } else {
      if (product.alternatives) {
        setLanguage(product.alternatives[newValue - 1].base.language);
      }
    }
    setSelectedTab(newValue);
  };

  const handleLanguageChange = (event: SelectChangeEvent<string>, _: ReactNode) => {
    setLanguage(event.target.value);
  };

  const addLanguage = () => {
    setBackdrop(true);
    if (product.alternatives && product.alternatives.filter((p) => p.base.language === language).length === 0) {
      let prompt = config.promptTranslateProductDetail;

      prompt = prompt.replace('${base_language}', product.base.language);
      prompt = prompt.replace('${target_language}', language);
      prompt = prompt.replace('${product_json}', JSON.stringify(product.base));

      AxiosInstance.post(`/text`, { sessionID: sessionID, prompt: prompt } as api.TextPromptRequest)
        .then((resp) => {
          if (resp.status === 200) {
            const newBase = resp.data as BaseProduct;
            const newProduct = {} as Product;
            newProduct.base = newBase;
            newProduct.category = product.category;
            if (product.images) {
              newProduct.images = [...product.images];
            }

            newProduct.alternatives = new Array<Product>();
            if (product.alternatives) {
              setProduct({ ...product, alternatives: [...product.alternatives, newProduct] });
              setSelectedTab(product.alternatives.length + 1);
            }

            setBackdrop(false);
          }
        })
        .catch((err) => console.error(err));
    }
  };

  useMemo(() => {
    if (product.base.name.trim().length === 0) {
      setBackdrop(true);
      let prompt = config.promptExtractProductDetail;
      prompt = prompt.replace(
        '${product_attribute_value_model}',
        JSON.stringify({ name: '', value: '' } as ProductAttributeValue)
      );

      if (product.category && product.category.attributes && product.category.attributes.length > 0) {
        prompt = prompt.replace('${category_attributes}', JSON.stringify(product.category.attributes));
      } else {
        prompt = prompt.replace(
          '${category_attributes}',
          JSON.stringify([
            {
              name: 'weight',
              description: 'weight of product in ounces',
              valueRange: [],
            } as Attribute,
          ])
        );
      }

      prompt = prompt.replace('${product_json}', JSON.stringify(product.base));
      AxiosInstance.post(`/text`, { sessionID: sessionID, prompt: prompt } as api.TextPromptRequest)
        .then((resp) => {
          if (resp.status === 200) {
            setProduct({ ...product, base: resp.data as BaseProduct });
          }
        })
        .catch((err) => {
          console.error(err);
        })
        .finally(() => setBackdrop(false));
    } else {
      setBackdrop(false);
    }
  }, [product, setProduct, setBackdrop]);

  return (
    <React.Fragment>
      <Grid container spacing={2} padding={2}>
        <Grid item xs={6}>
          <Typography variant="h5">Preview Detail</Typography>
        </Grid>
        <Grid item xs={6}>
          <Stack direction={'row'} spacing={2} sx={{ justifyContent: 'right' }}>
            <FormControl>
              <InputLabel id="all-languages-label">Languages</InputLabel>
              <Select
                id="language-select"
                size="small"
                labelId="all-languages-label"
                variant={'outlined'}
                value={language}
                label="Languages"
                onChange={handleLanguageChange}
                sx={{ minWidth: '180px' }}>
                {languages.SupportedLanguages.map((l, idx) => (
                  <MenuItem
                    key={`lng_${idx}`}
                    value={l.value}
                    disabled={
                      product.alternatives
                        ? product.alternatives?.filter((p) => p.base.language === l.value).length > 0
                        : true
                    }>
                    {l.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <Box sx={{ '& > :not(style)': { m: 0 } }}>
              <Fab size="small" color="primary" aria-label="add" onClick={addLanguage}>
                <AddIcon />
              </Fab>
            </Box>
          </Stack>
        </Grid>
      </Grid>

      <Suspense>
        <Tabs value={selectedTab} onChange={handleTabChange}>
          <Tab key="selected_tab_0" label={product.base.language} {...a11yProps(0)} />
          {product.alternatives?.map((entry, idx) => (
            <Tab key={`selected_tab_${idx + 1}`} label={entry.base.language} {...a11yProps(idx + 1)} />
          ))}
        </Tabs>
        {product && product.base && product.base.name ? (
          <React.Fragment>
            <ProductTabPanel key="product_panel_0" value={selectedTab} index={0}>
              <ProductDetail product={product} />
            </ProductTabPanel>

            {product.alternatives?.map((entry, idx) => (
              <ProductTabPanel key={`product_panel_${idx + 1}`} value={selectedTab} index={idx + 1}>
                <ProductDetail product={entry} />
              </ProductTabPanel>
            ))}
          </React.Fragment>
        ) : (
          <></>
        )}
      </Suspense>
      <GoogleBackdrop backdrop={backdrop} setBackdrop={setBackdrop} />
    </React.Fragment>
  );
};

export default Step3;
