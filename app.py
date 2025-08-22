from flask import Flask, request, jsonify, render_template
from working_generator import WorkingProductGenerator
import json
import os

app = Flask(__name__)

@app.route('/')
def index():
    """Serve the enhanced web interface"""
    return render_template('index.html')

@app.route('/api/generate', methods=['POST'])
def generate_product_api():
    """API endpoint to generate products - matches exact requirements format"""
    try:
        data = request.get_json()
        
        if not data or 'prompt' not in data:
            return jsonify({
                "success": False,
                "error": "Missing 'prompt' in request body"
            }), 400
        
        prompt = data['prompt'].strip()
        if not prompt:
            return jsonify({
                "success": False,
                "error": "Prompt cannot be empty"
            }), 400
        
        # Extract optional parameters
        product_type = data.get('product_type', 'hoodie').lower()
        style = data.get('style', 'natural')
        quality = data.get('quality', 'standard')
        
        # Validate product type
        generator = WorkingProductGenerator()
        valid_products = ['hoodie', 'tshirt', 'mug']
        if product_type not in valid_products:
            return jsonify({
                "success": False,
                "error": f"Invalid product type. Available: {valid_products}"
            }), 400
        
        # Generate product
        result = generator.generate_product(prompt, product_type, style, quality)
        
        if "error" in result:
            return jsonify({"error": result["error"]}), 500
        
        # Return exact format as specified in requirements
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/products', methods=['GET'])
def get_available_products():
    """Get list of available product types"""
    products = {
        'hoodie': {'name': 'Hoodie', 'id': 146},
        'tshirt': {'name': 'T-Shirt', 'id': 71},
        'mug': {'name': 'Mug', 'id': 19}
    }
    return jsonify({
        "success": True,
        "products": products
    })

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "AI Product Generator",
        "version": "2.0"
    })

if __name__ == '__main__':
    # Use PORT from environment (e.g., Render) or default to 5000 locally
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
