# <------------------------------ Imports ------------------------------->

# System imports 
import requests
import pandas as pd
from typing import Dict, Any, Optional

# Project imports
from user import User
from config.secrets import users


# <---------------------------- AngelBroking Class ---------------------------->

class AngelBroking:
    """
    A class to interact with Angel Broking APIs for token management and data retrieval.

    Attributes:
    -----------
    angel_instance : User
        The logged-in user instance for accessing Angel Broking services.
    """
    
    def __init__(self, userObject: User):
        """
        Initializes the AngelBroking object with the logged-in user instance.

        Parameters:
        -----------
        user_instance : User
            A logged-in user instance with an active session for Angel Broking services.
        """
        self.user_object = userObject
        self.user_instance = userObject.user_instance

    def _ensure_logged_in(self) -> None:
        """
        Internal method to ensure the user is logged in. Raises a RuntimeError if the user is not logged in.

        Raises:
        -------
        RuntimeError:
            If the user instance is not initialized (i.e., not logged in).
        """
        if not self.user_instance:
            raise RuntimeError("User is not logged in. Call login() first.")

    
    # <-------------------- Traded Entity Retrieval -------------------->

    def get_all_tokens_tradable(self, save_path: str = 'data/tokens.csv') -> Optional[pd.DataFrame]:
        """
        Retrieve tradable token data from a CSV file. If the file is not found, updates the data by fetching it 
        from the Angel Broking API.

        Parameters:
        -----------
        save_path : str, optional
            The path to save the token data (default is 'data/tokens.csv').

        Returns:
        --------
        Optional[pd.DataFrame]:
            A DataFrame containing the token data, or None if an error occurs.
        
        Logs:
        -----
        - Logs success or failure of token data loading or updating.
        """
        try:
            tokens_df = pd.read_csv(save_path)
            print("Token data loaded successfully from %s", save_path)
            return tokens_df

        except FileNotFoundError:
            print("Token data file not found at %s. Attempting to update data.", save_path)
            return self.update_all_tokens_tradable(save_path)

        except Exception as e:
            print(f"An error occurred while loading token data from {save_path}: {e}")
            return None

    def update_all_tokens_tradable(self, save_path: str = 'data/tokens.csv') -> Optional[pd.DataFrame]:
        """
        Updates and saves the tradable tokens data by fetching the latest ScriptMaster data from Angel Broking.

        Parameters:
        -----------
        save_path : str, optional
            The path where the updated token data will be saved (default is 'data/tokens.csv').

        Returns:
        --------
        Optional[pd.DataFrame]:
            A DataFrame containing the updated token data, or None if an error occurs.
        
        Logs:
        -----
        - Logs the status of the update (success or failure).
        """
        try:
            url = 'https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json'
            
            response = requests.get(url)
            response.raise_for_status()

            scripts = response.json()
            scripts_df = pd.DataFrame.from_dict(scripts)

            scripts_df = scripts_df.astype({'strike': float})

            scripts_df.to_csv(save_path, index=False)
            print("ScriptMaster data updated and saved successfully to %s", save_path)
            
            return scripts_df

        except requests.exceptions.RequestException as req_err:
            print(f"Request error occurred while fetching ScriptMaster data: {req_err}")

        except ValueError as val_err:
            print(f"Value error occurred while processing ScriptMaster data: {val_err}")

        except Exception as e:
            print(f"An unexpected error occurred while updating ScriptMaster data: {e}")

        print("ScriptMaster update was unsuccessful.")
        return None


# <---------------------------- END ---------------------------->
# if __name__ == "__main__":
#     for user_data in users:
#         user = User.from_dict(user_data)
#         user_object = user.login()["userInstance"]
#         angel = AngelBroking(user_object)
#         # print(angel.user_instance)
#         # print(angel.get_all_tokens_tradable())

#         from utils.orders import execute
#         print(angel.user_instance)