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
import { AppBar, Box, Button, Container, Toolbar, Typography } from '@mui/material';
import {ConfigurationContext} from '../contexts';
import pageLogo from '../assets/cymbol/LogoCircle.svg';
import cymbolText from '../assets/cymbol/Retail.svg';

const Header = () => {
    const {config} = useContext(ConfigurationContext);
    const nav = useNavigate();

    return (
        <Box component={'nav'}>
          <Box sx={{backgroundColor: '#000', height: '5px'}}>
            <Container maxWidth="xl" sx={{display: 'flex', justifyContent: 'left', alignItems: 'center'}}>
              <Typography sx={{fontSize: '11pt', pl: 5}} color={'primary'}></Typography>
            </Container>
          </Box>
            <AppBar position="sticky" sx={{backgroundColor: '#333'}}>
                <Toolbar sx={{p: 0}}>
                    <Box sx={{ml: 4, flexGrow: 1, display: 'flex'}}>
                        <Button
                            sx={{
                                my: 2,
                                display: 'block',
                                color: '#FFFFFF',
                                fontFamily: 'Google Sans',
                            }}
                            onClick={() => nav('/')}>
                            Overview
                        </Button>
                        <Button
                            sx={{
                                my: 2,
                                display: (!config || !config.customerName || config.customerName === '') ? 'none' : 'block',
                                color: '#FFFFFF',
                                fontFamily: 'Google Sans',
                            }}
                            onClick={() => nav('/product-reset', {replace: true})}>
                            Products
                        </Button>
                        <Button 
                            sx={{
                                my: 2,
                                display: (!config || !config.customerName || config.customerName === '') ? 'none' : 'block',
                                color: '#FFFFFF',
                                fontFamily: 'Google Sans',
                            }}
                            onClick={() => nav('/batch', {replace: true})}>
                            Batch
                        </Button>
                        <Button
                            sx={{
                                my: 2,
                                display: 'block',
                                color: '#FFFFFF',
                                fontFamily: 'Google Sans',
                            }}
                            onClick={() => nav('/settings', {replace: true})}>
                            Settings
                        </Button>
                    </Box>
                  <Box>
                    <Box sx={{display: { xs: 'none', sm: 'inline'} }}><img src={cymbolText} height={50} alt="Cymbol Logo" style={{marginTop: 4, paddingTop: 2 }} /></Box>
                    <Box sx={{display: 'inline' }}><img src={pageLogo} height={50} alt="Cymbol Logo" style={{marginTop: 4, paddingTop: 2}} /></Box>
                  </Box>
                </Toolbar>
            </AppBar>
        </Box>
    );
};

export default Header;
