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
            main: '#1565c0',
        },
        secondary: {
            main: '#37474f',
        },
        error: {
            main: '#b71c1c',
        },
        warning: {
            main: '#f4511e',
        },
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
