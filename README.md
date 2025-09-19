Ntuity Home Assistant custom integration (OAuth2 - Authorization Code)
--------------------------------------------------------------------

Important notes to get the integration working:

1) Application Credentials
   - Home Assistant uses the Application Credentials mechanism for local OAuth client_id/client_secret.
   - Go to Settings -> Devices & Services -> (three dots) -> Application credentials.
   - Click 'Add', choose 'Ntuity' from the integration list and paste the OAuth Client ID and Client Secret
     you obtained from Ntuity developer portal, then Save.
   - See Home Assistant docs on application credentials for details:
     https://developers.home-assistant.io/docs/core/platform/application_credentials/

2) Add integration:
   - After creating application credentials, open Settings -> Devices & services -> Add Integration -> Ntuity.
   - Follow the OAuth login flow in the popup.

3) If you still see 'Missing configuration' or errors:
   - Check Server Controls -> Logs in Home Assistant for errors referencing 'ntuity' or 'config_entry_oauth2_flow'.
   - Verify the custom component folder is in <config>/custom_components/ntuity and contains the files.
   - Ensure Home Assistant was restarted after adding/updating the custom component.

