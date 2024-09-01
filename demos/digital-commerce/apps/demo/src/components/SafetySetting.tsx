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


import {Container, Slider, Typography} from '@mui/material';
import {HarmBlockThreshold, HarmCategory, SafetySettings} from 'model';

const CustomMarks = [
    {value: 0, label: 'Default'},
    {value: 1, label: 'Low+'},
    {value: 2, label: 'Medium+'},
    {value: 3, label: 'High'},
    {value: 4, label: 'None'},
];

type SafetySettingsArgs = {
    category: HarmCategory;
    threshold: HarmBlockThreshold;
    disabled: boolean;
    setThreshold: (value: HarmBlockThreshold) => void;
};

const SafetySetting = ({category, threshold, setThreshold, disabled}: SafetySettingsArgs) => {
    return (
        <Container sx={{mt: 2}}>
            <Typography gutterBottom>{SafetySettings.categoryLabel(category)}</Typography>
            <Slider
                aria-label={category}
                value={SafetySettings.thresholdToNumber(threshold)}
                getAriaValueText={SafetySettings.thresholdLabel}
                valueLabelDisplay="auto"
                shiftStep={1}
                step={1}
                marks={CustomMarks}
                min={0}
                max={4}
                onChange={(_, v) => setThreshold(SafetySettings.numberToThreshold(v))}
                disabled={disabled}
            />
        </Container>
    );
};

export default SafetySetting;
