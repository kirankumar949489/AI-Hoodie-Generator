#!/usr/bin/env python3
"""
Working AI Product Generator - Simplified for Interview
"""

import os
import json
import sys
from dotenv import load_dotenv
from openai import OpenAI
import time
import requests

load_dotenv()

class WorkingProductGenerator:
    def __init__(self):
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.printful_key = os.getenv('PRINTFUL_API_KEY')
        self.printful_base = 'https://api.printful.com'
        # Map simple product types to Printful catalog product IDs
        self.product_type_to_printful_id = {
            'hoodie': 146,   # Gildan 18500
            'tshirt': 71,    # Bella + Canvas 3001
            'mug': 19        # 11oz Mug
        }
    
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

            content = (text_response.choices[0].message.content or "").strip()
            # Robust parsing for TITLE/DESCRIPTION regardless of formatting
            title = None
            description = None
            if content:
                for line in content.split('\n'):
                    line = line.strip()
                    if line.lower().startswith('title:') and not title:
                        title = line.split(':', 1)[1].strip()
                    elif line.lower().startswith('description:') and not description:
                        description = line.split(':', 1)[1].strip()
            # Fallbacks if the LLM format is different or empty
            if not title:
                # Titleize the prompt and append product type
                safe_prompt = ' '.join(w.capitalize() for w in prompt.split())
                pretty_product = {'hoodie': 'Hoodie', 'tshirt': 'T-Shirt', 'mug': 'Mug'}.get(product_type, product_type.title())
                title = f"{safe_prompt} {pretty_product}"
            if not description:
                description = f"Unleash style with this {product_type} featuring a '{prompt}' design. Premium feel, everyday comfort."
            
            print(f"✅ Copy created: {title}")
            
            # Try to generate a real Printful mockup if API key is present; otherwise fall back to demo URLs
            printful_mockup_url = None
            if self.printful_key:
                print("🧵 Creating Printful mockup...")
                try:
                    printful_mockup_url = self._create_printful_mockup(product_type, image_url)
                    if printful_mockup_url:
                        print("✅ Printful mockup created")
                except Exception as printful_error:
                    print(f"⚠️ Printful mockup failed: {printful_error}")
            else:
                print("ℹ️ PRINTFUL_API_KEY not set. Using demo mockup URLs.")

            if not printful_mockup_url:
                # Guaranteed fallback: reuse the generated image as the mockup preview
                # This ensures the frontend always has a valid URL to display
                print("ℹ️ Falling back to generated image URL for mockup preview.")
                printful_mockup_url = image_url
            
            result = {
                "image_url": image_url,
                "printful_mockup_url": printful_mockup_url,
                "product_title": title,
                "product_description": description
            }
            
            print("🎉 Generation complete!")
            return result
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return {"error": str(e)}

    def _printful_headers(self):
        return {
            'Authorization': f'Bearer {self.printful_key}',
            'Content-Type': 'application/json'
        }

    def _get_first_variant_id(self, product_id):
        # Query catalog to find any valid variant for this product
        url = f"{self.printful_base}/catalog/products/{product_id}"
        resp = requests.get(url, headers=self._printful_headers(), timeout=20)
        resp.raise_for_status()
        data = resp.json().get('result', {})
        variants = data.get('variants') or []
        if not variants:
            raise RuntimeError('No variants found for product')
        return variants[0].get('id')

    def _create_printful_mockup(self, product_type, image_url):
        product_id = self.product_type_to_printful_id.get(product_type)
        if not product_id:
            raise ValueError(f'Unsupported product type for Printful: {product_type}')

        # Pick a valid variant id
        variant_id = self._get_first_variant_id(product_id)

        # Create mockup task
        create_url = f"{self.printful_base}/mockup-generator/create-task/{product_id}"
        payload = {
            "variant_ids": [variant_id],
            "format": "jpg",
            "files": [
                {
                    "placement": "front",
                    "image_url": image_url,
                    "position": {"area_width": 1800, "area_height": 2400}
                }
            ]
        }
        resp = requests.post(create_url, headers=self._printful_headers(), data=json.dumps(payload), timeout=30)
        resp.raise_for_status()
        task_key = resp.json().get('result', {}).get('task_key')
        if not task_key:
            raise RuntimeError('Printful did not return a task_key')

        # Poll task until ready
        task_url = f"{self.printful_base}/mockup-generator/task"
        for _ in range(10):
            time.sleep(2)
            status_resp = requests.get(task_url, headers=self._printful_headers(), params={"task_key": task_key}, timeout=20)
            status_resp.raise_for_status()
            status_data = status_resp.json().get('result', {})
            status = status_data.get('status')
            if status == 'completed':
                # Try multiple possible locations for URL depending on API version
                mockups = status_data.get('mockups') or []
                if mockups:
                    # Try common fields
                    first = mockups[0]
                    if isinstance(first, dict):
                        # 1) direct url on mockup
                        if first.get('url'):
                            return first['url']
                        # 2) files[0].preview_url
                        files = first.get('files') or []
                        if files and isinstance(files[0], dict) and files[0].get('preview_url'):
                            return files[0]['preview_url']
                # Fallback: overall url field
                if status_data.get('url'):
                    return status_data['url']
                break
            if status in ('pending', 'processing'):
                continue
            # Any other status treated as failure
            raise RuntimeError(f'Unexpected Printful task status: {status}')

        raise RuntimeError('Printful mockup task timed out')

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
