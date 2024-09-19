# <------------------------------ Imports ------------------------------->

# System imports
import pyotp
from typing import Optional, Dict, Any
from SmartApi.smartConnect import SmartConnect

# Project imports
from config.secrets import users


# <------------------------------ User Class ----------------------------->

class User:
    """
    Represents a user for the SmartConnect trading platform.

    Attributes:
    -----------
    user_id : str
        The user ID for the trading platform.
    pin : str
        The user's PIN for authentication.
    api_key : str
        API key required for SmartConnect login.
    secret_key : str
        Secret key for generating TOTP.
    name : str
        Name of the user.
    user_instance : Optional[SmartConnect]
        Holds the authenticated session instance after a successful login.
    """
    
    def __init__(self, user_id: str, pin: str, api_key: str, secret_key: str, name: str):
        """
        Initializes a User object with the necessary credentials and attributes.
        
        Parameters:
        -----------
        user_id : str
            The user ID for the trading platform.
        pin : str
            The user's PIN for authentication.
        api_key : str
            API key required for SmartConnect login.
        secret_key : str
            Secret key for generating TOTP.
        name : str
            Name of the user.
        """
        self.user_id = user_id
        self.pin = pin
        self.api_key = api_key
        self.secret_key = secret_key
        self.name = name
        self.user_instance: Optional[SmartConnect] = None

    @classmethod
    def from_dict(cls, user_data: Dict[str, str]) -> 'User':
        """
        Creates a User instance from a dictionary.

        Parameters:
        -----------
        user_data : dict
            Dictionary containing user information.
        
        Returns:
        --------
        User
            An instance of the User class.
        """
        return cls(
            user_id=user_data.get("user_id", ""),
            pin=user_data.get("pin", ""),
            api_key=user_data.get("api_key", ""),
            secret_key=user_data.get("secret_key", ""),
            name=user_data.get("name", "")
        )

    
    # <------------------------- Login ------------------------->

    def login(self) -> Dict[str, SmartConnect]:
        """
        Logs into SmartConnect and initializes the session using TOTP authentication.

        Returns:
        --------
        dict:
            A dictionary containing:
            - 'success' (bool): Whether the login was successful.
            - 'userInstance' (str or None): String representation of the user instance if login succeeds, 
              otherwise None.
            - 'error' (str, optional): Error message if login fails or an exception occurs.
        """
        try:
            user_instance = SmartConnect(api_key=self.api_key)
            totp = pyotp.TOTP(self.secret_key).now()
            session = user_instance.generateSession(self.user_id, self.pin, totp)
            
            if session.get('status') == True:
                self.user_instance = user_instance
                refresh_token = session['data'].get('refreshToken')
                
                print(f"Login successful for user: {self.name}")
                print(f"User profile: {user_instance.getProfile(refresh_token)}")
                return {"success": True, 'userInstance': self.user_instance}

            else:
                print(f"Login failed for user: {self.name} - Status: {session.get('status')}")
                return {"success": False, 'error': "Login failed", 'userInstance': None}

        except Exception as e:
            print(f"Exception during login for user: {self.name}: {str(e)}")
            return {"success": False, 'error': f"An error occurred: {str(e)}", 'userInstance': None}

    
    # <------------------------- Margin ------------------------->

    def get_available_margin(self) -> Optional[float]:
        """
        Retrieves the available margin for the user from the SmartConnect API.

        Returns:
        --------
        Optional[float]:
            The available margin as a float, or None if an error occurs or the user is not logged in.
        """
        if not self.user_instance:
            print("User instance is not initialized. Call login() first.")
            return None

        try:
            rms_limit = self.user_instance.rmsLimit()
            net_margin = float(rms_limit['data']['net'])
            return net_margin

        except Exception as e:
            print(f"Exception while retrieving available margin: {str(e)}")
            return None
    
    def get_required_margin(self, buy_leg_token: str, sell_leg_token: str) -> Optional[float]:
        """
        Calculates the required margin for a pair of buy and sell legs using their tokens.

        Parameters:
        -----------
        buy_leg_token : str
            Token for the buy leg of the trade.
        sell_leg_token : str
            Token for the sell leg of the trade.

        Returns:
        --------
        Optional[float]:
            The calculated required margin as a float, or None if an error occurs or the user is not logged in.
        """
        if not self.user_instance:
            print("User instance is not initialized. Call login() first.")
            return None

        request_params = {

            "positions": [
                {
                    "exchange": "NFO",
                    "qty": 25,
                    "price": 0,
                    "productType": "CARRYFORWARD",
                    "token": buy_leg_token,
                    "tradeType": "BUY"
                },
                {
                    "exchange": "NFO",
                    "qty": 25,
                    "price": 0,
                    "productType": "CARRYFORWARD",
                    "token": sell_leg_token,
                    "tradeType": "SELL"
                }
            ]
        }

        try:
            response = self.user_instance.getMarginApi(request_params)
            margin_required = float(response['data']['totalMarginRequired'])
            
            updated_margin_required = float(margin_required + (margin_required * 0.20))
            return updated_margin_required

        except Exception as e:
            # Handle any errors during margin calculation
            print(f"Exception while calculating required margin: {str(e)}")
            return None

# <------------------------------ Test ------------------------------->
# if __name__ == "__main__":
#     for user_data in users:
#         user = User.from_dict(user_data)
#         response = user.login()
#         print(response)
#         print("Available Margin:", user.get_available_margin())
#         print("Required Margin:", user.get_required_margin("21198", "24604"))
        