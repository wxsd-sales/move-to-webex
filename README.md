<p align="center">
  <h2 align="center"> Migrate to Webex</h2>

  <p align="center">
Move your existing meetings from Zoom, MS Teams, or even a different Webex org to Webex in your Calendar.  This app will search your Microsoft Outlook/O365 calendar for existing meetings, based on a search term you provide. Then, you can simply select which calendar events you want to turn into Webex meetings (or Webex FEDRamp).
    <br />
    <a href="https://zoomtowebex.wbx.ninja/simplified"><strong>View Demo</strong></a>
    ·
    <a href="https://github.com/WXSD-Sales/MigrateToWebex/issues"><strong>Report Bug</strong></a>
    ·
    <a href="https://github.com/WXSD-Sales/MigrateToWebex/issues"><strong>Request Feature</strong></a>
  </p>
</p>

## About The Project

### Quick Note!

This project was originally built to migrate only Zoom meetings to a commercial Webex org, so you will see some urls that remain as a result of that.  Since its inception, this project has been updated to include moving any meetings based on a search parameter from an Outlook calendar, or even Webex commercial meetings to Webex FEDRamp.


### Video Demo

[![MigrateToWebex Video Demo](https://img.youtube.com/vi/iws4osHV42Y/0.jpg)](https://youtu.be/iws4osHV42Y, "MigrateToWebex Video Demo")

### NEW Simplified Walkthrough
<a href="https://zoomtowebex.wbx.ninja/simplified"><strong>Simplified Demo</strong></a>  
This version follows a similar path as the old walkthrough, but does not require authentication with Zoom!  

1. To use the simplified version, click the above link or navigate to https://zoomtowebex.wbx.ninja/simplified
2. Sign in with your Webex account credentials.
3. Sign in with your Microsoft Outlook/0365 version.
4. Enter a search parameter to find meetings. For example, **zoom.us** or **your_org.zoom.us**, then click Search.
5. Review and select meetings to transfer.
6. Click Transfer.

### NEW Webex FedRAMP Walkthrough
<a href="https://zoomtowebex.wbx.ninja/fedramp"><strong>FedRAMP Demo</strong></a>  
This version works exactly the same as the **simplified** version, but moves calendar meetings to Webex FedRAMP (requires Webex FedRAMP user login).

1. To use the FedRAMP version, click the above link or navigate to https://zoomtowebex.wbx.ninja/fedramp
2. Follow the steps for the simplified version, beginning with step 2.

### Built With

- Python3 (v3.8.1)  

<!-- GETTING STARTED -->

## Installation

If you simply want to use this application, you only need to follow the Walkthrough.<br/>
<br/>
Installation is only needed if you wish to host a version of this application yourself. However, most Microsoft & Zoom organizations restrict which applications  their users can access, so you may need to install your own version, or have your org admins grant permission for the corresponding app(s).<br/>

### Installation

1. Clone this repo.
2. Install the required python modules:
   ```
   pip install python-dotenv
   pip install pymongo==3.10.1
   pip install pymongo[srv]
   pip install tornado==4.5.2
   pip install requests
   pip install requests-toolbelt
   pip install pytz
   pip install python-dateutil
   ```
3. The following Environment variables are required for this demo, set with the appropriate values (see the Environment Variables section below for more details):
      ```
      MY_APP_PORT=10031
      MY_WEBEX_CLIENT_ID=ABCD
      MY_WEBEX_SECRET=0123
      MY_WEBEX_REDIRECT_URI=https://yourserver.com/webex-oauth
        MY_WEBEX_SCOPES=spark%3Akms%20meeting%3Aschedules_read%20meeting%3Aparticipants_read%20spark%3Apeople_read%20meeting%3Apreferences_write%20meeting%3Apreferences_read%20meeting%3Aparticipants_write%20meeting%3Aschedules_write

      MY_ZOOM_CLIENT_ID=XYZA
      MY_ZOOM_SECRET=A123
      MY_ZOOM_REDIRECT_URI=https://yourserver.com/zoom-oauth

      MY_AZURE_CLIENT_ID=MNOP
      MY_AZURE_SECRET=qrst
      MY_AZURE_REDIRECT_URI=https://yourserver.com/azure
      MY_AZURE_SCOPES=user.read%20mail.read%20calendars.read

      MY_MONGO_URI="mongodb+srv://username:password@your_instance.abcdef.mongodb.net/zoomdb?retryWrites=true&w=majority"
      MY_MONGO_DB=zoomdb
      ```
4. Start the server
   ```
   python server.py
   ```
   
<!-- ENV VARS -->

### Environment Variables

```MY_WEBEX_SCOPES``` and ```MY_AZURE_SCOPES``` can remain unchanged from the example above.
<br/><br/>
You will need to create an **Azure** Application, a **Webex** Integration, and a **Zoom** integration - and fill in the corresponding ```CLIENT_ID```s and ```SECRET```s for each environment variable listed above.
<br/><br/>
The paths for each of the above ```REDIRECT_URI```s should remain unchanged, however the hostname ```yourserver.com``` will need to point to your webserver running your application code.  Similarly, the ```MY_APP_PORT``` can be changed to a different value if you'd like.
<br/><br/>

```
MY_MONGO_URL
```
You will need a MongoDB instance to store data.  You can setup a free cluster using MongoDB [Atlas](https://cloud.mongodb.com).
Notice the url in the example wraps the string in quotation marks ```"```.  Be aware of any special characters when setting the environment variables.
<br/>

```
MY_MONGO_DB=zoomdb
```
This can remain unchanged.  Remember to update the DB in the ```MY_MONGO_URL``` string to match this value.


<!-- LICENSE -->

## License

Distributed under the MIT License. 

<!-- CONTACT -->

## Contact
Please contact us at wxsd@external.cisco.com

