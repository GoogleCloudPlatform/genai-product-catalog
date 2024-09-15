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

import {useContext} from 'react';
import {useNavigate} from 'react-router-dom';
import {AppBar, Box, Button, Toolbar, Typography} from '@mui/material';
import {ConfigurationContext} from '../contexts';

const Header = () => {
    const {config} = useContext(ConfigurationContext);
    const nav = useNavigate();

    return (
        <Box component={'nav'}>
            <AppBar position="sticky" color="transparent">
                <Toolbar sx={{p: 0}}>
                    <Typography variant="h4" sx={{fontFamily: 'Google Sans'}}>
                        <Typography variant="inherit" component={'span'} sx={{color: '#4285F4'}}>
                            G
                        </Typography>
                        <Typography variant="inherit" component={'span'} sx={{color: '#DB4437'}}>
                            o
                        </Typography>
                        <Typography variant="inherit" component={'span'} sx={{color: '#F4B400'}}>
                            o
                        </Typography>
                        <Typography variant="inherit" component={'span'} sx={{color: '#4285F4'}}>
                            g
                        </Typography>
                        <Typography variant="inherit" component={'span'} sx={{color: '#0F9D58'}}>
                            l
                        </Typography>
                        <Typography variant="inherit" component={'span'} sx={{color: '#DB4437'}}>
                            e
                        </Typography>{' '}
                        <Typography variant="inherit" component={'span'} sx={{color: '#666666'}}>
                            Cloud
                        </Typography>
                    </Typography>
                    <Box sx={{ml: 4, flexGrow: 1, display: 'flex'}}>
                        <Button
                            sx={{
                                my: 2,
                                display: 'block',
                                color: '#333333',
                                fontFamily: 'Google Sans',
                            }}
                            onClick={() => nav('/')}>
                            Overview
                        </Button>
                        <Button
                            sx={{
                                my: 2,
                                display: 'block',
                                color: '#333333',
                                fontFamily: 'Google Sans',
                            }}
                            onClick={() => nav('/product-reset', {replace: true})}
                            disabled={!config || !config.customerName || config.customerName === ''}>
                            Products
                        </Button>
                        <Button 
                            sx={{
                                my: 2,
                                display: 'block',
                                color: '#333333',
                                fontFamily: 'Google Sans',
                            }}
                            onClick={() => nav('/batch', {replace: true})}
                            disabled={!config || !config.customerName || config.customerName === ''}>
                            Batch
                        </Button>
                        <Button
                            sx={{
                                my: 2,
                                display: 'block',
                                color: '#333333',
                                fontFamily: 'Google Sans',
                            }}
                            onClick={() => nav('/settings', {replace: true})}>
                            Settings
                        </Button>
                    </Box>
                </Toolbar>
            </AppBar>
        </Box>
    );
};

export default Header;
