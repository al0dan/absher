"""
Wathq API Service
Commercial Registration (CR) Verification via Ministry of Commerce

API Docs: developer.wathq.sa
Version: v6.0.0
"""
import os
import requests
import logging
from functools import lru_cache
from datetime import datetime

logger = logging.getLogger(__name__)

class WathqService:
    # Production and Sandbox URLs
    PRODUCTION_URL = "https://api.wathq.sa/commercial-registration"
    SANDBOX_URL = "https://api.wathq.sa/sandbox/commercial-registration"
    
    def __init__(self):
        self.api_key = os.getenv('WATHQ_API_KEY')
        self.use_sandbox = os.getenv('WATHQ_SANDBOX', 'true').lower() == 'true'
        self.base_url = self.SANDBOX_URL if self.use_sandbox else self.PRODUCTION_URL
        self._cache = {}
        
    def get_cr_info(self, cr_number: str) -> dict | None:
        """Get basic CR info (name, status, expiry)."""
        return self._call_api(f"/info/{cr_number}", cr_number)
    
    def get_cr_full(self, cr_number: str) -> dict | None:
        """Get comprehensive CR data including capital, owners, managers."""
        return self._call_api(f"/fullinfo/{cr_number}", cr_number)
    
    def get_cr_status(self, cr_number: str) -> dict | None:
        """Get just the registration status."""
        return self._call_api(f"/status/{cr_number}", cr_number)

    def get_cr_data(self, cr_number: str) -> dict | None:
        """Legacy method for backwards compatibility."""
        return self.get_cr_info(cr_number)
    
    def _call_api(self, endpoint: str, cr_number: str) -> dict | None:
        if not cr_number or len(cr_number) != 10:
            return None
        
        # Check cache first
        cache_key = f"{endpoint}:{cr_number}"
        if cache_key in self._cache:
            logger.info(f"Wathq cache hit for {cr_number}")
            return self._cache[cache_key]
        
        # Simulation mode if no API key
        if not self.api_key:
            logger.info(f"Wathq: No API key, simulating lookup for {cr_number}")
            return self._simulate_lookup(cr_number)
        
        try:
            headers = {
                'apiKey': self.api_key,
                'Accept': 'application/json'
            }
            url = f"{self.base_url}{endpoint}"
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                parsed = self._parse_response(data)
                self._cache[cache_key] = parsed  # Cache result
                logger.info(f"Wathq: Successfully retrieved data for CR {cr_number}")
                return parsed
            elif response.status_code == 404:
                logger.warning(f"Wathq: CR {cr_number} not found")
                return None
            elif response.status_code == 401:
                logger.error("Wathq: Invalid API key")
                return self._simulate_lookup(cr_number)  # Fallback
            else:
                logger.warning(f"Wathq API error: {response.status_code}")
                return None
                
        except requests.Timeout:
            logger.error("Wathq: Request timed out")
            return self._simulate_lookup(cr_number)
        except Exception as e:
            logger.error(f"Wathq API exception: {e}")
            return None

    def _parse_response(self, data: dict) -> dict:
        """Parse Wathq v6 response into normalized format."""
        try:
            # Log raw response for debugging
            logger.debug(f"Wathq raw response: {data}")
            
            # Handle nested address structure
            address = data.get('address', {})
            if isinstance(address, str):
                city = address
            else:
                city = address.get('city', '') or address.get('cityName', '')
            
            # Try multiple possible field names for company name
            company_name = (
                data.get('crName') or 
                data.get('crEntityName') or 
                data.get('name') or 
                data.get('crNameAr') or
                data.get('entityName') or
                ''
            )
            
            return {
                'company_name': company_name,
                'company_name_en': data.get('crNameEn') or data.get('nameEn', ''),
                'cr_number': str(data.get('crNumber') or data.get('crMainNumber', '')),
                'expiry_date': data.get('expiryDate', ''),
                'city': city,
                'status': data.get('status', {}).get('name', 'unknown') if isinstance(data.get('status'), dict) else str(data.get('status', 'unknown')),
                'status_id': data.get('status', {}).get('id', '') if isinstance(data.get('status'), dict) else '',
                'capital': data.get('capital', {}).get('value', 0) if isinstance(data.get('capital'), dict) else data.get('capital', 0),
                'type': data.get('businessType', {}).get('name', '') if isinstance(data.get('businessType'), dict) else data.get('businessType', ''),
                'retrieved_at': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Wathq parse error: {e}")
            return None

    def _simulate_lookup(self, cr: str) -> dict | None:
        """Return mock data when API is unavailable."""
        # Known Saudi companies for demo
        known_crs = {
            '1010084764': {'name': 'شركة المراعي', 'en': 'Almarai Company', 'city': 'الرياض', 'capital': 8000000000},
            '1010012345': {'name': 'شركة الاتصالات السعودية', 'en': 'STC', 'city': 'الرياض', 'capital': 50000000000},
            '2050008440': {'name': 'أرامكو السعودية', 'en': 'Saudi Aramco', 'city': 'الظهران', 'capital': 60000000000},
            '1010010030': {'name': 'سابك', 'en': 'SABIC', 'city': 'الرياض', 'capital': 30000000000},
            '1010209450': {'name': 'شركة اتحاد اتصالات', 'en': 'Mobily', 'city': 'الرياض', 'capital': 5839000000},
            '4030073366': {'name': 'شركة النهدي الطبية', 'en': 'Al Nahdi Medical', 'city': 'جدة', 'capital': 1125000000},
        }
        
        if cr in known_crs:
            match = known_crs[cr]
            return {
                'company_name': match['name'],
                'company_name_en': match['en'],
                'cr_number': cr,
                'status': 'قائم',  # Active
                'status_id': '1',
                'city': match['city'],
                'capital': match['capital'],
                'type': 'شركة ذات مسؤولية محدودة',
                'retrieved_at': datetime.now().isoformat(),
                '_simulated': True
            }
        
        # Generic fallback for valid-looking CRs
        region_map = {'1': 'الرياض', '2': 'مكة', '3': 'المدينة', '4': 'الشرقية', '5': 'القصيم', '6': 'عسير'}
        if len(cr) == 10 and cr[0] in region_map:
            return {
                'company_name': f'مؤسسة {cr[-4:]}',
                'company_name_en': f'Est. {cr[-4:]}',
                'cr_number': cr,
                'status': 'قائم',
                'status_id': '1',
                'city': region_map.get(cr[0], 'الرياض'),
                'capital': 100000,
                'type': 'مؤسسة فردية',
                'retrieved_at': datetime.now().isoformat(),
                '_simulated': True
            }
        
        return None
