import { HarmBlockThreshold, HarmCategory, SafetySetting, SchemaType } from '@google/generative-ai';

export interface GenerativeConfig {
  modelName: string;
  genAIToken: string;
  instructions: string;
  temperature: number;
  topP: number;
  topK: number;
  maxTokenCount: number;
  safetySettings: SafetySetting[];
}

export const NewGenerativeConfig = (instructions: string) => {
  return {
    modelName: 'gemini-1.5-flash',
    genAIToken: '',
    instructions: instructions,
    temperature: 0.2,
    topP: 0.94,
    topK: 32,
    maxTokenCount: 8192,
    safetySettings: [
      {
        category: HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
        threshold: HarmBlockThreshold.HARM_BLOCK_THRESHOLD_UNSPECIFIED,
      },
      {
        category: HarmCategory.HARM_CATEGORY_HARASSMENT,
        threshold: HarmBlockThreshold.HARM_BLOCK_THRESHOLD_UNSPECIFIED,
      },
      {
        category: HarmCategory.HARM_CATEGORY_HATE_SPEECH,
        threshold: HarmBlockThreshold.HARM_BLOCK_THRESHOLD_UNSPECIFIED,
      },
      {
        category: HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
        threshold: HarmBlockThreshold.HARM_BLOCK_THRESHOLD_UNSPECIFIED,
      },
    ],
  } as GenerativeConfig;
};

export class SafetySettings {
  static categoryLabel = (category: HarmCategory): string => {
    switch (category) {
      case HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT:
        return 'Dangerous Content';
      case HarmCategory.HARM_CATEGORY_HATE_SPEECH:
        return 'Hate Speech';
      case HarmCategory.HARM_CATEGORY_HARASSMENT:
        return 'Harassment';
      case HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT:
        return 'Sexually Explicit';
      default:
        return 'Undefined'
    }
  };

  static thresholdLabel = (threshold: number): string => {
    switch (threshold) {
      case 0:
        return `Unspecified`;
      case 1:
        return `Low and Above`;
      case 2:
        return `Medium and Above`;
      case 3:
        return `Block High Only`;
      case 4:
        return `Block None`;
      default:
        return `Default`;
    }
  };

  static thresholdToNumber = (threshold: HarmBlockThreshold): number => {
    switch (threshold) {
      case HarmBlockThreshold.BLOCK_LOW_AND_ABOVE:
        return 1;
      case HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE:
        return 2;
      case HarmBlockThreshold.BLOCK_ONLY_HIGH:
        return 3;
      case HarmBlockThreshold.BLOCK_NONE:
        return 4;
      default:
        return 0;
    }
  };

  static numberToThreshold = (value: number | number[]): HarmBlockThreshold => {
    const input = Array.isArray(value) ? value[0] : value;
    switch (input) {
      case 0:
        return HarmBlockThreshold.HARM_BLOCK_THRESHOLD_UNSPECIFIED;
      case 1:
        return HarmBlockThreshold.BLOCK_LOW_AND_ABOVE;
      case 2:
        return HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE;
      case 3:
        return HarmBlockThreshold.BLOCK_ONLY_HIGH;
      case 4:
        return HarmBlockThreshold.BLOCK_NONE;
      default:
        return HarmBlockThreshold.HARM_BLOCK_THRESHOLD_UNSPECIFIED;
    }
  };
}

export const CategorySchema = {
  description: 'A retail product category',
  type: SchemaType.OBJECT,
  properties: {
    name: {
      type: SchemaType.STRING,
      description: 'The name of the category',
      nullable: false,
    },
    attributes: {
      type: SchemaType.ARRAY,
      description: 'The attributes of the category such as color, dimensions, etc.',
      items: {
        type: SchemaType.OBJECT,
        nullable: false,
        properties: {
          name: {
            type: SchemaType.STRING,
            description: 'The name of the attribute',
            nullable: false,
          },
          description: {
            type: SchemaType.STRING,
            description: 'The description of the attribute',
            nullable: false,
          },
          valueRange: {
            type: SchemaType.ARRAY,
            description: 'The value range of the attribute',
            items: {
              type: SchemaType.STRING,
              description: 'The value of the attribute',
              nullable: false,
            }
          }
        }
      }
    }
  }
}


export const ProductSchema = {
  description: 'A retail product',
  type: SchemaType.OBJECT,
  properties: {
    base: {
      type: SchemaType.OBJECT,
      properties: {
        language: {
          type: SchemaType.STRING,
          description: 'The ISO language code of the product',
          nullable: false,
        },
        name: {
          type: SchemaType.STRING,
          description: 'The name of the product',
          nullable: false,
        },
        description: {
          type: SchemaType.STRING,
          description: 'The description of the product',
          nullable: false,
        },
        seoHtmlHeader: {
          type: SchemaType.STRING,
          description: 'The SEO HTML header of the product',
          nullable: false,
        },
        attributeValues: {
          type: SchemaType.ARRAY,
          description: 'The attribute values of the product',
          items: {
            type: SchemaType.OBJECT,
            properties: {}
          }
        }
      },
      required: ['language', 'name', 'description', 'seoHtmlHeader', 'attributeValues']
    },
    images: {
      type: SchemaType.ARRAY,
      description: 'The images of the product',
      items: {
        type: SchemaType.OBJECT,
        properties: {
          uri: {
            type: SchemaType.STRING,
            description: 'The URI of the image',
            nullable: true,
          },
          base64: {
            type: SchemaType.STRING,
            description: 'The base64 of the image',
            nullable: false,
          },
          type: {
            type: SchemaType.STRING,
            description: 'The type of the image',
            nullable: false,
          }
        },
        required: ["base64", "type"]
      }
    }
  }
}