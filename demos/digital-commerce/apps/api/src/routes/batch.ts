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

import { Request, Response, Router } from "express";
import { BatchProduct } from "model";

const router = Router();


// Initial products, may be added onto in the UI
const MIXED_PRODUCTS: BatchProduct[] = [
    {id: 1, gtin: "00012345678905", name: "Apple iPhone 15 Pro Max", short_description: "Smartphone with A17 Pro chip and Super Retina XDR display"},
    {id: 2, gtin: "00023456789014", name: "Samsung Galaxy Tab S9 Ultra", short_description: "Tablet with Dynamic AMOLED 2X display and Snapdragon 8 Gen 2 for Galaxy processor"},
    {id: 3, gtin: "0003456789013", name: "Sony WH-1000XM5", short_description: "Wireless noise-cancelling headphones with industry-leading noise cancellation"},
    {id: 4, gtin: "0004567890122", name: "Bose QuietComfort Earbuds II", short_description: "True wireless noise-cancelling earbuds with CustomTune technology"},
    {id: 5, gtin: "0005678901231", name: "LG C3 OLED TV", short_description: "Smart TV with α9 AI Processor Gen6 and 4K self-lit OLED evo panel"},
    {id: 6, gtin: "0006789012340", name: "Dyson V15 Detect Absolute", short_description: "Cordless vacuum cleaner with laser dust detection and HEPA filtration"},
    {id: 7, gtin: "0007890123459", name: "KitchenAid Artisan Stand Mixer", short_description: "5-quart stand mixer with 10 speeds and tilt-head design"},
    {id: 8, gtin: "0008901234568", name: "Nespresso Vertuo Next", short_description: "Single-serve coffee machine with centrifusion technology"},
    {id: 9, gtin: "0009012345677", name: "Nike Air Zoom Pegasus 40", short_description: "Running shoes with React foam and Zoom Air unit"},
    {id: 10, gtin: "0010123456786", name: "LEGO Star Wars Millennium Falcon", short_description: "7,541-piece LEGO set of the iconic Star Wars spaceship"},
]

router.get('/', (req: Request, resp: Response) => {
    resp.status(200)
    resp.json(MIXED_PRODUCTS)
})

export default router;