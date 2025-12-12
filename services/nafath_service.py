import os
import logging
from authlib.integrations.flask_client import OAuth
from flask import redirect, url_for, session, current_app

logger = logging.getLogger(__name__)

oauth = OAuth()

def init_nafath(app):
    # If client secrets are present, register the real provider
    if os.getenv('NAFATH_CLIENT_ID') and os.getenv('NAFATH_CLIENT_SECRET'):
        oauth.register(
            name='nafath',
            client_id=os.getenv('NAFATH_CLIENT_ID'),
            client_secret=os.getenv('NAFATH_CLIENT_SECRET'),
            access_token_url='https://api.nafath.sa/token',
            access_token_params=None,
            authorize_url='https://api.nafath.sa/authorize',
            authorize_params=None,
            api_base_url='https://api.nafath.sa/userinfo',
            client_kwargs={'scope': 'openid profile national_id'},
        )
        oauth.init_app(app)
        logger.info("Nafath OAuth initialized (Real Mode)")
    else:
        logger.warning("Nafath credentials missing. Running in SIMULATION MODE.")

def get_nafath_redirect():
    if not os.getenv('NAFATH_CLIENT_ID'):
        # SIMULATION URL
        return redirect(url_for('auth.nafath_callback_sim'))
    return oauth.nafath.authorize_redirect(redirect_uri=url_for('auth.nafath_callback', _external=True))
