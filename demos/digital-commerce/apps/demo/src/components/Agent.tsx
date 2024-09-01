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

import React, {useContext, useRef} from 'react';
import {
    BottomNavigation,
    BottomNavigationAction,
    Box,
    Drawer,
    FormControl,
    IconButton,
    InputAdornment,
    InputLabel,
    OutlinedInput,
    Stack,
    Typography
} from '@mui/material';
import {ConversationContext, ProductContext, SessionIDContext} from '../contexts';
import RecordRTC from 'recordrtc';
import {AudioPromptRequest} from 'libs/model/src/lib/api';
import MicIcon from '@mui/icons-material/Mic';
import MicOffIcon from '@mui/icons-material/MicOff';
import RestartAltIcon from '@mui/icons-material/RestartAlt';
import SendIcon from '@mui/icons-material/Send';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';

const MarkdownPreview = React.lazy(() => import('@uiw/react-markdown-preview/nohighlight'));

const Agent = ({open, setOpen}: { open: boolean; setOpen: (value: boolean) => void }) => {
    const {sessionID} = useContext(SessionIDContext);
    // Use contextual state for the product.
    const {product} = useContext(ProductContext);

    const {conversation, setConversation, socket} = useContext(ConversationContext);

    const stopRecording = useRef(() => {
    });

    const captureMic = (cb: (stream: MediaStream) => void) => {
        navigator.mediaDevices.getUserMedia({audio: true}).then(cb);
    };

    const startRecorder = () => {
        captureMic((mic) => {
            const recorder = new RecordRTC(mic, {
                type: 'audio',
                mimeType: 'audio/webm',
                sampleRate: 48000,
            });

            recorder.startRecording();

            stopRecording.current = () => {
                recorder.stopRecording(() => {
                    recorder.getDataURL((dataUrl) => {
                        const data = {
                            sessionID: sessionID,
                            type: recorder.getBlob().type,
                            size: recorder.getBlob().size,
                            value: dataUrl,
                            prompt: JSON.stringify(product.base),
                        } as AudioPromptRequest;
                        socket.emit('voice:request', data);
                        mic.getTracks().forEach((track) => track.stop());
                    });
                });
            };
        });
    };

    return (
        <Drawer
            open={open}
            anchor={'right'}

            onClose={() => {
                setOpen(false);
            }}>
            <Stack direction={'column'} minWidth={'400px'} height={'100vh'}>
                <Box sx={{ml: 2}}>
                    <Typography variant='h5'>Assistant</Typography>
                </Box>
                <Box sx={{
                    flex: '1 1 auto',
                    p: 2,
                    overflowY: 'auto',
                    borderBottom: '1px solid #ccc',
                    borderRadius: '10px',
                    boxShadow: '0px 4px 4px rgba(0, 0, 0, 0.25)',
                    backdropFilter: 'blur(4px)',
                    background: 'linear-gradient(186deg, rgba(205,229,245,.5) 0%, rgba(155,188,212,.5) 100%)'
                }}>
                    {conversation.map((u, idx) =>
                        u.role === 'system' ? (
                            <Box
                                key={`__sys__${idx}`}
                                sx={{
                                    color: 'white',
                                    p: 1,
                                    lineHeight: '12px',
                                    borderRadius: '7px',
                                    mb: 2,
                                    width: '90%',
                                    position: 'relative',
                                    border: '0.2px solid rgba(155,188,212,.5) 100%',
                                    background: 'linear-gradient(186deg, rgba(57, 117, 213, 0.4) 0%, rgba(66, 133, 244,.6) 100%)',
                                }}>
                                <Box maxWidth={300}>
                                    <MarkdownPreview source={u.value} style={{background: 'none', color: '#FFF'}}/>
                                    <Box sx={{display: 'flex', justifyContent: 'right', m: 0, p: 0}}>
                                        <IconButton
                                            onClick={() => navigator.clipboard.writeText(u.value)}><ContentCopyIcon/></IconButton>
                                    </Box>
                                </Box>
                            </Box>
                        ) : (
                            <Box key={`__usr__${idx}`} sx={{
                                p: 1,
                                lineHeight: '12px',
                                mb: 2,
                                width: '90%',
                                position: 'relative',
                                borderRadius: '7px',
                                border: '0.2px solid rgba(155,155,155,.5) 100%',
                                background: 'linear-gradient(186deg, rgba(107, 108, 111, 0.5) 0%, rgba(53, 55, 58, 0.5) 100%)',
                                ml: '10%'
                            }}>
                                <Box maxWidth={300}>
                                    <MarkdownPreview source={u.value} style={{background: 'none', color: '#FFF'}}/>
                                </Box>
                            </Box>
                        )
                    )}
                </Box>

                <FormControl variant='outlined' sx={{mt: 2, mb: 1, p: 0}}>
                    <InputLabel htmlFor='chatInput'>Chat</InputLabel>
                    <OutlinedInput id='chatInput' type='text' fullWidth sx={{
                        borderRadius: '10px',
                        backgroundColor: '#FFFFFF'
                    }} endAdornment={
                        <InputAdornment position='end'>
                            <IconButton><SendIcon/></IconButton>
                        </InputAdornment>
                    }/>
                </FormControl>

                <BottomNavigation sx={{borderRadius: '10px'}}>
                    <BottomNavigationAction label="Listen" icon={<MicIcon/>} onClick={startRecorder}/>
                    <BottomNavigationAction label="Stop" icon={<MicOffIcon/>} onClick={() => stopRecording.current()}/>
                    <BottomNavigationAction label="Reset" icon={<RestartAltIcon/>} onClick={() => setConversation([])}/>
                </BottomNavigation>
            </Stack>
        </Drawer>
    );
};

export default Agent;
