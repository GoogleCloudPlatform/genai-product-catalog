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

import { Box, Button, Container, Fab, Stack } from '@mui/material';
import React, { useContext, useRef } from 'react';
import RecordRTC from 'recordrtc';
import { ConfigurationContext, ProductContext, SessionIDContext } from '../../contexts';
import { api, Category, Product, ProductAsJsonString } from 'model';
import { useNavigate } from 'react-router-dom';
import AxiosInstance from '../../utils/WebClient';
import PhotoCameraFrontIcon from '@mui/icons-material/PhotoCameraFront';
import StopIcon from '@mui/icons-material/Stop';

const captureCamera = (cb: (stream: MediaStream) => void) => {
  navigator.mediaDevices.getUserMedia({ audio: true, video: true }).then(cb);
};

const categoryPrompt = `
    - Suggest the top 2 categories and their top 25 attributes from the product information.
    - The category hierarchy must be 4 levels deep, separated by ' > ' character.
        
    Example JSON Output: [\${category_model}]
      `.trim();

const VideoSetup = () => {
  const { sessionID } = useContext(SessionIDContext);
  const { config } = useContext(ConfigurationContext);
  const { product, setProduct } = useContext(ProductContext);

  const navigate = useNavigate();
  const stopRecording = useRef<() => void>(null!);
  const localVideoRef = React.createRef<HTMLVideoElement>();

  const startRecorder = () => {
    captureCamera((camera) => {
      const recorder = new RecordRTC(camera, {
        type: 'video',
        mimeType: 'video/mp4',
        frameRate: 10,
      });

      if (localVideoRef.current) {
        localVideoRef.current.srcObject = camera;
        localVideoRef.current.muted = true;
      }

      recorder.startRecording();

      stopRecording.current = () => {
        recorder.stopRecording(() => {
          recorder.getDataURL((url) => {
            const requestBody = {
              sessionID: sessionID,
              prompt: config.promptVideo,
              categoryPrompt: "Find a JSON array of the top 2 categories and their top 25 attributes from the product description. The category hierarchy must be 4 levels deep, separated by ' > ' character. Example JSON Output: [ ${category_model} ]".replace('${category_model}',
                JSON.stringify({
                  name: 'parent > child > grand_child > great_grand_child',
                  attributes: [{ name: 'weight', description: '', valueRange: ['a', 'b', 'c'] }],
                } as Category)
              ),
              productDetailPrompt: config.promptExtractProductDetail.replace('${product_json}', ProductAsJsonString()),
              type: recorder.getBlob().type,
              size: recorder.getBlob().size,
              value: url,
            } as api.VideoPromptRequest;

            AxiosInstance.post(`/video`, requestBody)
              .then((resp) => {
                console.log('stage 1 complete');
                if (resp.status === 200) {


                  const productResponse = resp.data as Product;
                  console.log('####')
                  console.log(productResponse)
                  setProduct({ ...product, ...productResponse });
                  navigate('/products/3');
                }
              })
              .catch((err) => console.error(err));

            camera.getTracks().forEach((track) => {
              track.stop();
            });
          });
        });
      };
    });
  };

  return (
    <Container>
      <Box sx={{ display: 'grid', justifyContent: 'center', justifyItems: 'center' }}>
        <Box height={400} sx={{aspectRatio: '16/9', border: '1px solid #666', borderRadius: '10px', p: 1, m:2}}>
          <video ref={localVideoRef} height="100%" width="100%" autoPlay></video>
        </Box>
        <Stack direction={'row'} spacing={2}>
          <Fab variant={'extended'} color={'success'} onClick={() => startRecorder()}><PhotoCameraFrontIcon /> Start</Fab>
          <Fab variant={'extended'} color={'secondary'} onClick={() => stopRecording.current()}><StopIcon /> Stop</Fab>
        </Stack>
      </Box>
    </Container>
  );
};

export default VideoSetup;
