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

import {Box, Container, Typography} from "@mui/material";
import TextLogo from '../assets/cymbol/TextCymbolLogoWhite.svg';

const Footer = () => {
    return (
        <Box component="footer" sx={{
            position: 'absolute',
            bottom: 0,
            height: '3.5em',
            width: '100vw',
            backgroundColor: '#333',
            color: '#FFF',
            zIndex: 999,
            borderTop: '0.5px solid #AAA',
            alignContent: 'center'
        }}>
            <Container maxWidth="xl" sx={{display: 'flex', justifyContent: 'left', alignItems: 'center'}}>
              <img src={TextLogo} height={40} alt={"Cymbal Logo"} />
              <Typography variant="body2" sx={{display: 'inline', pr: 5, color: 'white'}}>&copy;2024 Cymbal <span style={{fontStyle: 'italic'}}>Retail</span></Typography>
            </Container>
        </Box>
    )
}

export default Footer