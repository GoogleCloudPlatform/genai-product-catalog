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

import React, {useContext, useRef, useState} from 'react';
import {
    BottomNavigation,
    BottomNavigationAction,
    Box, Container,
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
import {AudioPromptRequest, ChatPromptRequest} from 'libs/model/src/lib/api';
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

    const [textValue, setTextValue] = useState<string>('');

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
                        socket.emit('agent:voice', data);
                        mic.getTracks().forEach((track) => track.stop());
                    });
                });
            };
        });
    };

    const textAgent = () => {
        if (textValue && textValue.trim().length > 0) {
            const data = {
                sessionID: sessionID,
                value: textValue,
                prompt: JSON.stringify(product.base),
            } as ChatPromptRequest;
            socket.emit('agent:text', data);
            setTextValue('');
        }
    }

    const textOnClick = () => {
        if (textValue && textValue.trim().length > 0) {
            setConversation([...conversation, {
                role: 'user',
                value: textValue,
            }])
            textAgent();
        }
    }

    const handleEnter = (e:  React.KeyboardEvent<HTMLInputElement | HTMLTextAreaElement>) => {
        if (e.key === 'Enter') {
            textOnClick();
        }
    }

    return (
        <Drawer
            open={open}
            anchor={'right'}
            onClose={() => {
                setOpen(false);
            }}>
            <Stack direction={'column'} minWidth={'400px'} height={'100vh'}>
                <Box sx={{ml: 2}}>
                    <Typography variant='h5' color={'white'}>Assistant</Typography>
                </Box>
                <Box sx={{
                    flex: '1 1 auto',
                    p: 2,
                    overflowY: 'auto'}}>
                    {conversation.map((u, idx) =>
                        u.role === 'system' ? (
                            <Box
                                key={`__sys__${idx}`}
                                sx={{
                                    color: 'white',
                                    p: 2,
                                    mb: 2,
                                    lineHeight: '12px',
                                    borderRadius: '20px',
                                    width: '350px',
                                    position: 'relative',
                                    background: 'rgba(111,0,23,1)',
                                }}>
                                <Box maxWidth={350}>
                                    <MarkdownPreview source={u.value} style={{background: 'none', color: '#FFF'}}/>
                                    <Box sx={{display: 'flex', justifyContent: 'right', m: 0, p: 0}}>
                                        <IconButton sx={{color: 'primary.contrastText'}}
                                            onClick={() => navigator.clipboard.writeText(u.value)}><ContentCopyIcon/></IconButton>
                                    </Box>
                                </Box>
                            </Box>
                        ) : (
                            <Box key={`__usr__${idx}`} sx={{
                                p: 2,
                                mb: 2,
                                lineHeight: '12px',
                                borderRadius: '20px',
                                width: '350px',
                                position: 'relative',
                                backgroundColor: 'white',
                                ml: '60px'
                            }}>
                                <Box maxWidth={350}>
                                    <MarkdownPreview source={u.value} style={{background: 'none', color: '#000'}}/>
                                </Box>
                            </Box>
                        )
                    )}
                </Box>

                <FormControl variant='filled' sx={{mt: 2, p: 1}}>
                    <InputLabel htmlFor='chatInput'>Chat</InputLabel>
                    <OutlinedInput id='chatInput'
                        type='text'
                        onChange={e => setTextValue(e.target.value)}
                        onKeyUp={handleEnter}
                        value={textValue}
                        fullWidth
                        sx={{
                        borderRadius: '10px',
                        backgroundColor: '#FFFFFF'
                    }} endAdornment={
                        <InputAdornment position='end'>
                            <IconButton onClick={textOnClick}><SendIcon/></IconButton>
                        </InputAdornment>
                    }/>
                </FormControl>

                <BottomNavigation sx={{m: 0, p: 0}}>
                    <BottomNavigationAction label="Listen" icon={<MicIcon sx={{fontSize: '24px'}}/>} onClick={startRecorder}/>
                    <BottomNavigationAction label="Stop" icon={<MicOffIcon sx={{fontSize: '24px'}}/>} onClick={() => stopRecording.current()}/>
                    <BottomNavigationAction label="Reset" icon={<RestartAltIcon sx={{fontSize: '24px'}}/>} onClick={() => setConversation([])}/>
                </BottomNavigation>
            </Stack>
        </Drawer>
    );
};

export default Agent;
