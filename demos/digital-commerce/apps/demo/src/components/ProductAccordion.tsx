// Copyright 2024 Google, LLC
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

import { Product } from 'model';
import { Accordion,
    AccordionDetails,
    AccordionSummary, Typography, Grid,
    Paper} from "@mui/material";
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import React from "react";


const MarkdownPreview = React.lazy(() => import('@uiw/react-markdown-preview'));

const ProductAccordionPanel = ({ index, product }: { index: number; product: Product }) => {
    return (
      <Accordion>
        <AccordionSummary
          expandIcon={<ExpandMoreIcon />}
          aria-controls={`panel-content-${index}`}
          id={`panel-header-${index}`}>
          {product.base.name}
        </AccordionSummary>
        <AccordionDetails sx={{ p: 1, borderRadius: '10px' }}>
          <Typography variant="overline">{product.category.name}</Typography>
          <Grid container spacing={2}>
            <Grid size={8}>
              <MarkdownPreview
                source={product.base.description}
                style={{ backgroundColor: '#fff', color: '#666', marginBottom: '2em' }}
              />
            </Grid>
            <Grid size={4}>
              {product.images ? (
                product.images.map((i) => (
                  <Paper elevation={5} sx={{borderRadius: '10px', display: 'flex', flexGrow: 1}}>
                      <img src={`data:${i.type};base64,${i.base64}`} width="100%" style={{objectFit: 'cover', borderRadius: '10px'}}/>
                  </Paper>
                ))
              ) : (
                <></>
              )}
            </Grid>
          </Grid>
  
          {product.base.attributeValues ? (
            <React.Fragment>
              <Typography variant="h6">Attributes</Typography>
              <Grid container spacing={2}>
                {product.base.attributeValues.map((a) => (
                  <Grid size={3}>
                    <Typography variant="overline">{a.name}</Typography>
                    <br />
                    <Typography variant="caption">{a.value}</Typography>
                  </Grid>
                ))}
              </Grid>
            </React.Fragment>
          ) : (
            <></>
          )}
  
          <Typography variant="h6" sx={{ mt: 2 }}>
            SEO
          </Typography>
          <MarkdownPreview
            source={`\`\`\`html\n${product.base.seoHtmlHeader}\`\`\``}
            style={{ margin: '2em', backgroundColor: '#fff', color: '#666', marginBottom: '2em' }}
          />
        </AccordionDetails>
      </Accordion>
    );
  };

  export default ProductAccordionPanel;