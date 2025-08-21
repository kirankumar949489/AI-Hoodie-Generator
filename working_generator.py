#!/usr/bin/env python3
"""
Working AI Product Generator - Simplified for Interview
"""

import os
import json
import sys
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

class WorkingProductGenerator:
    def __init__(self):
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    def generate_product(self, prompt, product_type='hoodie', style='natural', quality='standard'):
        try:
            print(f"🚀 Generating {product_type} for: {prompt}")
            
            # Generate image with DALL-E 3
            print("🎨 Creating image...")
            
            # Product-specific prompts
            prompts = {
                'hoodie': f"A hoodie with {prompt} design on front, professional product photo, white background",
                'tshirt': f"A t-shirt with {prompt} design on front, professional product photo, white background", 
                'mug': f"A coffee mug with {prompt} design, professional product photo, white background"
            }
            
            image_prompt = prompts.get(product_type, f"A {product_type} with {prompt} design, professional product photo, white background")
            
            image_response = self.openai_client.images.generate(
                model="dall-e-3",
                prompt=image_prompt,
                size="1024x1024",
                quality=quality,
                style=style,
                n=1
            )
            
            image_url = image_response.data[0].url
            print(f"✅ Image created: {image_url[:50]}...")
            
            # Generate product info with GPT-4
            print("✍️ Creating product copy...")
            text_response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert e-commerce copywriter. Create a catchy product title and compelling description."},
                    {"role": "user", "content": f"Create a product title and description for a {product_type} with this design: {prompt}. Format as: TITLE: [title]\nDESCRIPTION: [description]"}
                ],
                max_tokens=200
            )
            
            content = text_response.choices[0].message.content
            lines = content.split('\n')
            title = lines[0].replace('TITLE: ', '').strip()
            description = lines[1].replace('DESCRIPTION: ', '').strip() if len(lines) > 1 else f"Awesome {product_type} with {prompt} design"
            
            print(f"✅ Copy created: {title}")
            
            # Mock Printful URL
            mockup_urls = {
                'hoodie': 'https://files.printful.com/mockup-generator/hoodie-mockup-demo.jpg',
                'tshirt': 'https://files.printful.com/mockup-generator/tshirt-mockup-demo.jpg', 
                'mug': 'https://files.printful.com/mockup-generator/mug-mockup-demo.jpg'
            }
            
            result = {
                "image_url": image_url,
                "printful_mockup_url": mockup_urls.get(product_type, 'https://files.printful.com/mockup-demo.jpg'),
                "product_title": title,
                "product_description": description
            }
            
            print("🎉 Generation complete!")
            return result
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return {"error": str(e)}

def main():
    if len(sys.argv) < 2:
        print("Usage: python working_generator.py 'your prompt here'")
        return
    
    prompt = sys.argv[1]
    generator = WorkingProductGenerator()
    result = generator.generate_product(prompt)
    
    print("\n" + "="*50)
    print("🎯 FINAL RESULT")
    print("="*50)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
