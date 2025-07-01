from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import base64
from pathlib import Path

app = Flask(__name__)
CORS(app)

class WatchImageMatcher:
    def __init__(self, images_folder="watch_images"):
        self.images_folder = Path(images_folder)
        # Ensure the images folder exists
        if not self.images_folder.exists():
            self.images_folder.mkdir(exist_ok=True)
            
        self.watch_models = {
            "Tradition Auto 40": ["tradition auto 40", "tradition auto fourty", "tradition auto forty"],
            "Regent 38": ["regent 38", "regent thirty-eight", "regent thirty eight"],
            "Classic 34": ["classic 34", "classic thirty-four", "classic thirty four"],
            "Halo 37": ["halo 37", "halo thirty-seven", "halo thirty seven"],
            "Explorer 42": ["explorer 42", "explorer fourty-two", "explorer forty-two", "explorer forty two"],
            "Dive Master 44": ["dive master 44", "dive master fourty-four", "dive master forty-four", "dive master forty four"],
            "Chrono Speed 40": ["chrono speed 40", "chrono speed fourty", "chrono speed forty"],
            "Field Ranger 41": ["field ranger 41", "field ranger fourty-one", "field ranger forty-one", "field ranger forty one"],
            "Urban 38": ["urban 38", "urban thirty-eight", "urban thirty eight"],
            "Minimalist 35": ["minimalist 35", "minimalist thirty-five", "minimalist thirty five"],
            "Canvas 39": ["canvas 39", "canvas thirty-nine", "canvas thirty nine"],
            "Bloom 34": ["bloom 34", "bloom thirty-four", "bloom thirty four"],
            "Nightfall 41": ["nightfall 41", "nightfall fourty-one", "nightfall forty-one", "nightfall forty one"],
            "Tempo Luxe 40": ["tempo luxe 40", "tempo luxe fourty", "tempo luxe forty"],
            "Neon Pulse 42": ["neon pulse 42", "neon pulse fourty-two", "neon pulse forty-two", "neon pulse forty two"],
            "Nova Crystal 36": ["nova crystal 36", "nova crystal thirty-six", "nova crystal thirty six"]
        }
        
        self.variation_to_model = {}
        for model, variations in self.watch_models.items():
            for variation in variations:
                self.variation_to_model[variation.lower()] = model
    
    def find_watch_model(self, text):
        text_lower = text.lower()
        
        for variation, model in self.variation_to_model.items():
            if variation in text_lower:
                return model
        
        for model in self.watch_models.keys():
            model_name = model.rsplit(' ', 1)[0].lower()
            if model_name in text_lower:
                return model
        
        return None
    
    def get_image_path(self, model_name):
        if not model_name:
            return None
            
        for ext in ['.jpg', '.jpeg', '.png', '.webp']:
            image_path = self.images_folder / f"{model_name}{ext}"
            if image_path.exists():
                return str(image_path)
        
        return None
    
    def get_image_base64(self, model_name):
        image_path = self.get_image_path(model_name)
        if not image_path:
            return None
        
        try:
            with open(image_path, 'rb') as f:
                image_data = f.read()
                return base64.b64encode(image_data).decode('utf-8')
        except FileNotFoundError:
            print(f"Image not found: {image_path}")
            return None
        except Exception as e:
            print(f"Error reading image {image_path}: {e}")
            return None

watch_matcher = WatchImageMatcher()

@app.route('/')
def index():
    """Serve the main HTML page"""
    try:
        # Path relative to api directory
        html_path = Path(__file__).parent.parent / 'static' / 'index.html'
        with open(html_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return content, 200, {'Content-Type': 'text/html; charset=utf-8'}
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth', methods=['GET'])
def get_auth_token():
    """Generate authentication token for Hume API"""
    try:
        hume_api_key = os.environ.get('HUME_API_KEY')
        hume_secret_key = os.environ.get('HUME_SECRET_KEY')
        
        # Get config_id from query parameter, fallback to env variable
        config_id = request.args.get('config_id')
        if not config_id:
            config_id = os.environ.get('HUME_CONFIG_ID')
        
        if not all([hume_api_key, hume_secret_key, config_id]):
            missing = []
            if not hume_api_key:
                missing.append('HUME_API_KEY')
            if not hume_secret_key:
                missing.append('HUME_SECRET_KEY')
            if not config_id:
                missing.append('HUME_CONFIG_ID (provide via ?config_id=... URL parameter)')
            return jsonify({'error': f'Missing: {", ".join(missing)}'}), 500
        
        return jsonify({
            'apiKey': hume_api_key,
            'secretKey': hume_secret_key,
            'configId': config_id
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/watch-image', methods=['POST'])
def get_watch_image():
    """Get watch image based on text content"""
    try:
        data = request.get_json()
        text = data.get('text', '')
        
        watch_model = watch_matcher.find_watch_model(text)
        
        if not watch_model:
            return jsonify({'watchModel': None, 'watchImage': None}), 200
        
        watch_image = watch_matcher.get_image_base64(watch_model)
        
        return jsonify({
            'watchModel': watch_model,
            'watchImage': watch_image
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/watch-models', methods=['GET'])
def get_watch_models():
    """Get all available watch models"""
    try:
        return jsonify({'models': list(watch_matcher.watch_models.keys())}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': 'Internal server error'}), 500

# This is required for Vercel
if __name__ == "__main__":
    app.run()
