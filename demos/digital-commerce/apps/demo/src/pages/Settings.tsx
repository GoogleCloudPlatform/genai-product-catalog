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
  Container,
  FormControl,
  Grid,
  InputLabel,
  Paper,
  Slider,
  Stack,
  Switch,
  TextField,
  Tooltip,
  Typography,
} from '@mui/material';

import React, { useContext, useState } from 'react';
import { useFormik } from 'formik';
import { useNavigate } from 'react-router-dom';

import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import SafetySetting from '../components/SafetySetting';
import * as Yup from 'yup';

import { api, Config } from 'model';
import { ConfigurationContext, SessionIDContext } from '../contexts';
import AxiosInstance from '../utils/WebClient';
import { HarmBlockThreshold, HarmCategory } from '@google/generative-ai';

const Settings = () => {
  const [modelControls, setModelControls] = useState<boolean>(true);
  const { sessionID, setSessionID } = useContext(SessionIDContext);
  const { config, setConfig } = useContext(ConfigurationContext);

  const nav = useNavigate();

  const SettingSchema = Yup.object().shape({
    customerName: Yup.string().min(2).max(255).required('Required'),
    engineerLdap: Yup.string().min(2).max(255).required('Required'),
    generativeConfig: Yup.object().shape({
      genAIToken: Yup.string().min(20).max(255).required('Required'),
      instructions: Yup.string().min(20).required('Required'),
    }),
  });

  const formik = useFormik<Config>({
    initialValues: config,
    validationSchema: SettingSchema,
    onSubmit: async (values: Config) => {
      AxiosInstance.post('/registration', { sessionID: sessionID, config: values } as api.ConfigurationRequest)
        .then((resp) => {
          if (resp.status === 201 || resp.status === 202) {
            const reg = resp.data as api.ConfigurationResponse;
            setSessionID(reg.sessionID);
            setConfig(values);
            nav('/overview', { replace: true });
          } else if (resp.status === 400) {
            const err = resp.data as api.ErrorResponse;
            console.error(err.error);
          }
        })
        .catch((registrationErr) => console.error(registrationErr));
    },
  });

  const updateSafetySetting = (category: HarmCategory, threshold: HarmBlockThreshold) => {
    console.log(threshold);
    const curVal = formik.values.generativeConfig.safetySettings;
    const idx = curVal.findIndex((i) => i.category === category);
    curVal[idx] = { category, threshold };

    formik.setFieldValue('generativeConfig.safetySettings', [...curVal]);
  };

  const openInNewTab = (uri: string) => {
    const win = window.open(uri, '_blank');
    if (win != null) {
      win.focus();
    }
  };

  return (
    <React.Fragment>
      <Typography variant="h5">Settings</Typography>

      <Container maxWidth="md">
        <form method="post" onSubmit={formik.handleSubmit}>
          <Grid container spacing={2}>
            <Grid item xs={12}>
              <Typography variant="h5">Required Information</Typography>
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Customer Name"
                variant="outlined"
                name="customerName"
                helperText={'Use "Googler" if you are only testing'}
                value={formik.values.customerName}
                error={formik.touched.customerName && Boolean(formik.errors.customerName)}
                onChange={formik.handleChange}
                onBlur={formik.handleBlur}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Engineer LDAP"
                variant="outlined"
                name="engineerLdap"
                helperText={'Displayed as "Presented By: <name>"'}
                value={formik.values.engineerLdap}
                error={formik.touched.engineerLdap && Boolean(formik.errors.engineerLdap)}
                onChange={formik.handleChange}
                onBlur={formik.handleBlur}
              />
            </Grid>
            <Grid item xs={12}>
              <Stack direction={'row'} spacing={2}>
                <TextField
                  fullWidth
                  name="generativeConfig.genAIToken"
                  type="password"
                  label="Generative AI Token"
                  variant="outlined"
                  onChange={formik.handleChange}
                  onBlur={formik.handleBlur}
                  value={formik.values.generativeConfig.genAIToken}
                  error={
                    formik.touched.generativeConfig?.genAIToken && Boolean(formik.errors.generativeConfig?.genAIToken)
                  }
                />

                <Button
                  variant="outlined"
                  sx={{ minWidth: '150px' }}
                  onClick={() => openInNewTab('https://aistudio.google.com/app/apikey')}>
                  Get API Key
                </Button>
              </Stack>
            </Grid>
            <Grid item xs={12}>
              <Box sx={{ display: 'flex', justifyContent: 'right' }}>
                <Button type="submit" variant="contained">
                  Save
                </Button>
              </Box>
            </Grid>
          </Grid>

          {/* Gen AI Setting */}
          <Grid container spacing={2} sx={{ mt: 6, borderTop: '.5px solid #DDD' }}>
            <Grid item xs={12}>
              <Stack direction={'row'}>
                <Typography variant="h5">Generative AI Settings</Typography>
                <Box sx={{ display: 'flex', flex: 1, justifyContent: 'right', alignContent: 'center' }}>
                  <Typography gutterBottom>
                    Enable Controls <Switch color="warning" onChange={(_) => setModelControls(!modelControls)} />
                  </Typography>
                </Box>
              </Stack>
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Instructions"
                name="generativeConfig.instructions"
                multiline
                rows={3}
                error={
                  formik.touched.generativeConfig?.instructions && Boolean(formik.errors.generativeConfig?.instructions)
                }
                onChange={formik.handleChange}
                onBlur={formik.handleBlur}
                value={formik.values.generativeConfig?.instructions}
                disabled={modelControls}
              />
            </Grid>
            <Grid item xs={12}>
              <Typography variant="h5">Prompts</Typography>
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                name="promptDetectCategories"
                label="Detect Category"
                multiline
                rows={3}
                value={config.promptDetectCategories}
                disabled={modelControls}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Extract Product Detail"
                name="promptExtractProductDetail"
                multiline
                rows={3}
                value={formik.values.promptExtractProductDetail}
                disabled={modelControls}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                name="promptTranslateProductDetail"
                label="Translate Product Detail"
                multiline
                rows={3}
                value={config.promptTranslateProductDetail}
                disabled={modelControls}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                name="promptVideo"
                label="Translate Video to Product"
                multiline
                rows={3}
                value={config.promptVideo}
                disabled={modelControls}
              />
            </Grid>
          </Grid>

          {/* Model Controls */}
          <Grid container spacing={2} sx={{ pt: 2 }}>
            <Grid item xs={12}>
              <Typography variant="h5">Model Controls</Typography>
            </Grid>
            <Grid item xs={6}>
              <Paper elevation={3} sx={{ p: 1 }}>
                <Typography variant="h6">Generative Settings</Typography>
                <Stack spacing={4}>
                  <FormControl fullWidth variant="outlined" sx={{ mt: 2 }}>
                    <Stack direction={'row'} spacing={2}>
                      <InputLabel shrink={true} htmlFor="config-temp">
                        Temperature
                      </InputLabel>

                      <Slider
                        id="config-temp"
                        name="generativeConfig.temperature"
                        aria-describedby="config-temp-helper"
                        size="medium"
                        value={formik.values.generativeConfig.temperature}
                        onChange={formik.handleChange}
                        onBlur={formik.handleBlur}
                        step={0.1}
                        valueLabelDisplay="auto"
                        min={0.0}
                        max={1.0}
                        disabled={modelControls}
                      />
                      <Tooltip
                        title="The temperature is used for sampling during response
                    generation, which occurs when topP and topK are applied.
                    Temperature controls the degree of randomness in token
                    selection. Lower temperatures are good for prompts that
                    require a less open-ended or creative response, while higher
                    temperatures can lead to more diverse or creative results. A
                    temperature of 0 means that the highest probability tokens
                    are always selected. In this case, responses for a given
                    prompt are mostly deterministic, but a small amount of
                    variation is still possible.">
                        <InfoOutlinedIcon />
                      </Tooltip>
                    </Stack>
                  </FormControl>

                  <FormControl fullWidth variant="outlined" sx={{ mt: 2 }}>
                    <Stack direction={'row'} spacing={2}>
                      <InputLabel shrink={true} htmlFor="config-top-p">
                        Top P
                      </InputLabel>

                      <Slider
                        id="config-top-p"
                        name="generativeConfig.topP"
                        aria-describedby="config-top-p-helper"
                        size="medium"
                        value={formik.values.generativeConfig.topP}
                        onChange={formik.handleChange}
                        onBlur={formik.handleBlur}
                        step={0.01}
                        valueLabelDisplay="auto"
                        min={0.0}
                        max={1.0}
                        disabled={modelControls}
                      />
                      <Tooltip
                        title="Top-P changes how the model selects tokens for output.
                      Tokens are selected from the most (see top-K) to least
                      probable until the sum of their probabilities equals the
                      top-P value. For example, if tokens A, B, and C have a
                      probability of 0.3, 0.2, and 0.1 and the top-P value is
                      0.5, then the model will select either A or B as the next
                      token by using temperature and excludes C as a candidate.">
                        <InfoOutlinedIcon />
                      </Tooltip>
                    </Stack>
                  </FormControl>

                  <FormControl fullWidth variant="outlined" sx={{ mt: 2 }}>
                    <Stack direction={'row'} spacing={2}>
                      <InputLabel shrink={true} htmlFor="config-top-k">
                        Top K
                      </InputLabel>

                      <Slider
                        id="config-top-k"
                        name="generativeConfig.topK"
                        aria-describedby="config-top-k-helper"
                        size="medium"
                        value={formik.values.generativeConfig.topK}
                        onChange={formik.handleChange}
                        onBlur={formik.handleBlur}
                        step={1}
                        valueLabelDisplay="auto"
                        min={1}
                        max={40}
                        disabled={modelControls}
                      />
                      <Tooltip
                        title="Top-K changes how the model selects tokens for output. A
                      top-K of 1 means the next selected token is the most
                      probable among all tokens in the model's vocabulary (also
                      called greedy decoding), while a top-K of 3 means that the
                      next token is selected from among the three most probable
                      tokens by using temperature.">
                        <InfoOutlinedIcon />
                      </Tooltip>
                    </Stack>
                  </FormControl>
                </Stack>
              </Paper>
            </Grid>
            <Grid item xs={6}>
              <Paper elevation={3} sx={{ p: 1 }}>
                <Typography variant="h6">Safety Settings</Typography>
                {formik.values.generativeConfig.safetySettings.map((safetySetting) => (
                  <SafetySetting
                    key={`safety_settings_${safetySetting.category}`}
                    disabled={modelControls}
                    category={safetySetting.category}
                    threshold={safetySetting.threshold}
                    setThreshold={(value: HarmBlockThreshold) => updateSafetySetting(safetySetting.category, value)}
                  />
                ))}
              </Paper>
            </Grid>
          </Grid>

          <Box sx={{ display: 'flex', flexGrow: 1, justifyContent: 'right', pt: 2 }}>
            <Button type="submit" variant="contained">
              Save
            </Button>
          </Box>
        </form>
      </Container>
    </React.Fragment>
  );
};

export default Settings;
