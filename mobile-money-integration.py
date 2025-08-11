
import requests
import json
from datetime import datetime
import hashlib
import secrets

class SomaliaMobileMoneyAPI:
    """Real Somalia Mobile Money Integration"""
    
    def __init__(self):
        self.evc_plus_api = "https://api.evcplus.com/"  # Hormuud EVC Plus
        self.zaad_api = "https://api.zaad.com/"         # Telesom ZAAD
        self.edahab_api = "https://api.edahab.com/"     # Somtel eDahab
    
    def process_evc_plus_payment(self, amount, phone, merchant_id, api_key):
        """Process EVC Plus payment"""
        try:
            # Generate transaction ID
            transaction_id = f"EVC-{secrets.token_hex(8).upper()}"
            
            # API payload
            payload = {
                "merchant_id": merchant_id,
                "amount": amount,
                "phone": phone,
                "transaction_id": transaction_id,
                "currency": "USD",
                "timestamp": datetime.now().isoformat(),
                "description": "Dadaal App Payment"
            }
            
            # Generate signature (example)
            signature = self.generate_signature(payload, api_key)
            payload["signature"] = signature
            
            # Make API request
            response = requests.post(
                f"{self.evc_plus_api}/payments",
                json=payload,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "transaction_id": transaction_id,
                    "status": result.get("status", "completed"),
                    "message": "EVC Plus payment successful"
                }
            else:
                return {
                    "success": False,
                    "error": f"EVC Plus API Error: {response.text}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"EVC Plus payment failed: {str(e)}"
            }
    
    def process_zaad_payment(self, amount, phone, merchant_code, secret_key):
        """Process ZAAD payment"""
        try:
            transaction_id = f"ZAAD-{secrets.token_hex(8).upper()}"
            
            payload = {
                "merchantCode": merchant_code,
                "amount": amount,
                "customerPhone": phone,
                "transactionId": transaction_id,
                "description": "Dadaal App Payment"
            }
            
            # ZAAD signature generation
            signature = self.generate_zaad_signature(payload, secret_key)
            payload["signature"] = signature
            
            response = requests.post(
                f"{self.zaad_api}/api/payment",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "transaction_id": transaction_id,
                    "message": "ZAAD payment successful"
                }
            else:
                return {
                    "success": False,
                    "error": f"ZAAD API Error: {response.text}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"ZAAD payment failed: {str(e)}"
            }
    
    def generate_signature(self, payload, secret_key):
        """Generate payment signature"""
        # Create string to sign
        string_to_sign = f"{payload['merchant_id']}{payload['amount']}{payload['phone']}{payload['transaction_id']}{secret_key}"
        
        # Generate SHA256 hash
        signature = hashlib.sha256(string_to_sign.encode()).hexdigest()
        return signature
    
    def generate_zaad_signature(self, payload, secret_key):
        """Generate ZAAD signature"""
        string_to_sign = f"{payload['merchantCode']}{payload['amount']}{payload['customerPhone']}{secret_key}"
        return hashlib.sha256(string_to_sign.encode()).hexdigest()

# Usage example
def integrate_real_mobile_money():
    """Integration example"""
    mobile_money = SomaliaMobileMoneyAPI()
    
    # EVC Plus payment
    evc_result = mobile_money.process_evc_plus_payment(
        amount=10.00,
        phone="+252611234567",
        merchant_id="YOUR_MERCHANT_ID",
        api_key="YOUR_EVC_API_KEY"
    )
    
    # ZAAD payment
    zaad_result = mobile_money.process_zaad_payment(
        amount=10.00,
        phone="+252631234567", 
        merchant_code="YOUR_ZAAD_MERCHANT_CODE",
        secret_key="YOUR_ZAAD_SECRET_KEY"
    )
    
    return evc_result, zaad_result
