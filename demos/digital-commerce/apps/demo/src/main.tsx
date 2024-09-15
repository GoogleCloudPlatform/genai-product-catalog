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

import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './layouts/App'
import {createBrowserRouter, Navigate, RouterProvider} from 'react-router-dom';
import axios from 'axios';
import BatchProvider from './providers/BatchProvider';

const MarkdownPreview = React.lazy(() => import('@uiw/react-markdown-preview/nohighlight'));

const API_BASE = import.meta.env.VITE_API_URL_BASE

const Overview = React.lazy(() => import('./pages/Overview'));

const Settings = React.lazy(() => import('./pages/Settings'));

const Products = React.lazy(() => import('./layouts/Products'))

const Step1 = React.lazy(() => import('./pages/products/Step1'));
const Step2 = React.lazy(() => import('./pages/products/Step2'));
const Step3 = React.lazy(() => import('./pages/products/Step3'));
const VideoSetup = React.lazy(() => import('./pages/products/VideoSetup'));
const Batch = React.lazy(() => import('./pages/Batch'));

const ErrorBoundary = () => {
    return (<Navigate to="/"/>)
}

const router = createBrowserRouter([
    {
        path: "/",
        element: <App/>,
        children: [
            {
                index: true,
                element: <Overview/>,
                errorElement: <ErrorBoundary/>,
            },
            {
                path: "/overview",
                element: <Overview/>,
                errorElement: <ErrorBoundary/>,
            },
            {
                path: 'settings',
                element: <Settings/>,
                errorElement: <ErrorBoundary/>,
            },
            {
                path: 'batch',
                element: <BatchProvider><Batch /></BatchProvider>,
                errorElement: <ErrorBoundary />,
                loader: async () => {
                    return (await axios.get(`${API_BASE}/batch`)).data
                }
            },
            {
                path: 'product-reset', // Forces the product state to refresh
                element: <Navigate to='/products'/>
            },
            {
                path: "products",
                element: <Products/>,
                errorElement: <ErrorBoundary/>,
                children: [
                    {
                        index: true,
                        element: <Step1/>
                    },
                    {
                        path: "2",
                        element: <Step2/>
                    },
                    {
                        path: "3",
                        element: <Step3/>
                    },
                    {
                        path: 'video-setup',
                        element: <VideoSetup/>
                    }
                ]
            }
        ]
    }
])

ReactDOM.createRoot(document.getElementById('root')!).render(<RouterProvider router={router}/>)
