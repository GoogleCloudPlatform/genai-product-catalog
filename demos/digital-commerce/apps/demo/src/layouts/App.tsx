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

import {Outlet} from 'react-router-dom';

import React from 'react';
import {Box, Container, createTheme, CssBaseline, ThemeOptions, ThemeProvider} from '@mui/material';
import Footer from '../components/Footer';
import Header from '../components/Header';

import {LoadingIcon} from '../components/LoadingIcon';
import ConfigurationProvider from '../providers/ConfigurationProvider';
import SessionIDProvider from '../providers/SessionIDProvider';
import ConversationProvider from '../providers/ConversationProvider';

import './app.css';

const themeOptions: ThemeOptions = {
  palette: {
    mode: 'light',
    primary: {
      main: '#CF0731',
    },
    secondary: {
      main: '#9F0021',
    },
    error: {
      main: '#B51C1C',
    },
    warning: {
      main: '#F4C436',
    },
    success: {
      main: '#28956E',
    },
    info: {
      main: '#823A5C',
    },
  },
  typography: {
    h1: {
      fontSize: '80pt',
      fontFamily: 'DM Sans',
    },
    h2: {
      fontFamily: 'DM Sans',
      fontSize: '60pt',
    },
    h3: {
      fontFamily: 'DM Sans',
      fontSize: '48pt',
    },
    h4: {
      fontFamily: 'DM Sans',
      fontSize: '30pt',
      fontWeight: 600,
    },
    h5: {
      fontFamily: 'DM Sans',
      fontSize: '24pt',
      fontWeight: 600,
    },
    h6: {
      fontFamily: 'DM Sans',
      fontSize: '20pt',
      fontWeight: 600,
    },
    subtitle1: {
      fontFamily: 'DM Sans',
      fontSize: '16pt',
      fontWeight: 500,
    },
    subtitle2: {
      fontFamily: 'DM Sans',
      fontSize: '14pt',
    },
    body1: {
      fontFamily: 'DM Sans',
      fontSize: '14pt',
      fontWeight: 500,
    },
    body2: {
      fontFamily: 'DM Sans',
      fontSize: '14pt',
      fontWeight: 500,
    },
    button: {
      fontFamily: 'DM Sans',
      fontSize: '12pt',
      fontWeight: 600,
    },
    caption: {
      fontFamily: 'DM Sans',
      fontSize: '12pt',
    },
    overline: {
      fontFamily: 'DM Sans',
      fontSize: '12pt',
      fontWeight: 600,
    },
    fontFamily: 'DM Sans',
    fontSize: 12,
  },
};

const theme = createTheme(themeOptions);

function App() {
    return (
        <ThemeProvider theme={theme}>
            <SessionIDProvider>
                <ConversationProvider>
                    <ConfigurationProvider>
                            <Box
                                sx={{
                                    position: 'relative',
                                    display: 'flex',
                                    flexDirection: 'column',
                                    minHeight: '100vh',
                                }}>
                                <CssBaseline/>
                                <Header/>
                                <Container component="main" sx={{mt: 3, pb: '3.5em', mb: 2, overflow: 'auto'}}
                                           maxWidth="xl">
                                    <React.Suspense fallback={<LoadingIcon/>}>
                                        <Outlet/>
                                    </React.Suspense>
                                </Container>
                                <Footer/>
                            </Box>
                    </ConfigurationProvider>
                </ConversationProvider>
            </SessionIDProvider>
        </ThemeProvider>
    );
}

export default App;
