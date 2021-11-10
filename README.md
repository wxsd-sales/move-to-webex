# ZoomToWebex<p align="center">
  <h2 align="center"> Zoom to Webex</h2>

  <p align="center">
Move your existing meetings from Zoom to Webex in your Calendar.  This app will search your Microsoft calendar for existing Zoom meetings and make Webex meetings to fill the spots.
    <br />
    <a href="https://zoomtowebex.wbx.ninja/"><strong>View Demo</strong></a>
    ·
    <a href="https://github.com/WXSD-Sales/ZoomToWebex/issues"><strong>Report Bug</strong></a>
    ·
    <a href="https://github.com/WXSD-Sales/ZoomToWebex/issues"><strong>Request Feature</strong></a>
  </p>
</p>

## About The Project

### Video Demo

[![ZoomToWebex Video Demo](https://img.youtube.com/vi/iws4osHV42Y/0.jpg)](https://youtu.be/iws4osHV42Y, "ZoomToWebex Video Demo")

### Walkthrough

1. To use this application as it exists in production, [click here](https://zoomtowebex.wbx.ninja).
2. Sign in with your Webex account credentials.
3. Sign in with your Zoom account credentials.
4. Sign in with your Microsoft Outlook/O365 credentials.
5. Click Search for Zoom meetings.
6. Review the found meetings, and select any you wish to transfer.
7. Click Transfer.

### Built With

- Python3 (v3.8.1)  

<!-- GETTING STARTED -->

## Installation

If you simply want to use this application, you only need to follow the Walkthrough.<br/>
<br/>
Installation is only needed if you wish to host a version of this application yourself. However, most Microsoft & Zoom organizations restrict which applications  their users can access, so you may need to install your own version, or have your org admins grant permission for the corresponding app(s).<br/>

### Installation

1. Clone the repo
   ```sh
   git clone https://github.com/WXSD-Sales/BlurBackground.git
   ```
2. Install the required python modules:
   ```
   pip install pymongo==3.10.1
   pip install pymongo[srv]
   pip install tornado==4.5.2
   pip install requests
   pip install requests-toolbelt
   ```
3. The following Environment variables are required for this demo, set with the appropriate values (see the Environment Variables section below for more details):
      ```
      MY_BOT_ID=1234567890
      MY_BOT_TOKEN=ABCDEFG-1234-567A_ZYX
      MY_SECRET_PHRASE=apmtestexample
      MY_BOT_PORT=10031

      MY_CLIENT_ID=C51234567890
      MY_CLIENT_SECRET=7851234567890
      MY_BASE_URI=https://1234.eu.ngrok.io
      MY_REDIRECT_URI=/auth
      MY_SCOPES=spark%3Akms%20spark%3Apeople_read

      MY_MONGO_URL="mongodb+srv://username:password@your_instance.abcdef.mongodb.net/apm_demo?retryWrites=true&w=majority"
      MY_MONGO_DB=apm_demo
      ```
4. Create the Webhooks (see below).
5. Start the server
   ```
   python apm_bot.py
   ```
   
<!-- ENV VARS -->

### Environment Variables
```
MY_BOT_TOKEN
``` 
1. login to the my-apps section of the [developer portal](https://developer.webex.com/my-apps)
2. Click "Create a New App"
3. Select Bot
4. Fill in the required fields
You will be returned a unique bearer token for the bot.
<br/>

```MY_BOT_ID``` 
This is actually the bot's personId (NOT application_id).  To get the bot's personId, 
1. [click here](https://developer.webex.com/docs/api/v1/people/get-my-own-details).
2. Use the Try It editor on the right side of the page.
3. toggle off the "Use personal access token" switch.
4. paste the bot's token from step 1
5. click Run
The JSON returned will include an "id" property.  This is the bot's personId.
<br/>

```
MY_BASE_URI
```
1. This will need to be a publicly accessible location where your bot will be exposed.  You can use something like [ngrok](https://ngrok.com/) to provide a tunnel from your laptop or desktop to the world.
2. You will use this value again when you create your webhooks, and will use it + ```/auth``` as the redirect_uri when you create the integration for ```MY_CLIENT_ID``` and ```MY_CLIENT_SECRET```.
<br/>

```
MY_REDIRECT_URI=/auth
MY_SCOPES=spark%3Akms%20spark%3Apeople_read
```
These can remain unchanged.
<br/>

```
MY_CLIENT_ID
MY_CLIENT_SECRET
```
1. login to the my-apps section of the [developer portal](https://developer.webex.com/my-apps)
2. Click "Create a New App"
3. Select Integration
4. Fill in the required fields.<br/>
      a. Your redirect_uri value when creating this integration will need to be the ```MY_BASE_URI``` + ```MY_REDIRECT_URI``` values<br/>
      b. For example, if you were to use the values given in the examples from the Installation step, your redirect_uri would be:<br/>
      ```https://1234.eu.ngrok.io/auth```<br/>
You will be returned a unique clientId and clientSecret when the application is created.
<br/>

```
MY_MONGO_URL
```
You will need a MongoDB instance to store data.  You can setup a free cluster using MongoDB [Atlas](https://cloud.mongodb.com).
Notice the url in the example wraps the string in quotation marks ```"```.  Be aware of any special characters when setting the environment variables.
<br/>

```
MY_MONGO_DB=apm_demo
```
This can remain unchanged.  Remember to update the DB in the ```MY_MONGO_URL``` string to match this value.


<!-- WEBHOOKS -->

### Webhooks

This application requires 2 webhooks. To create them through the developer portal [click here](https://developer.webex.com/docs/api/v1/webhooks/create-a-webhook).
1.Use the Try It Editor on the right side of the page<br/>
2.Untoggle the "Use my personal access token" switch<br/>
3.Paste the bot's token in that field.<br/>
4.Enter any name<br/>
5.targetUrl: Enter your ```BASE_URI```<br/>
6.resource: ```messages```<br/>
7.event: ```created```<br/>
8.secret: Enter your ```MY_SECRET_PHRASE``` value<br/>
<br/>
Repeat this process a second time, to create an attachment Action webhook, will slight differences:<br/>
4.Enter any name<br/>
5.targetUrl: Enter your ```BASE_URI``` + ```/cards```<br/>
6.resource: ```attachmentActions```<br/>
7.event: ```created```<br/>
8.secret: Enter your ```MY_SECRET_PHRASE``` value<br/>


<!-- LICENSE -->

## License

Distributed under the MIT License. 

<!-- CONTACT -->

## Contact
Please contact us at wxsd@external.cisco.com

