# Remote Assist Display
This project is meant to be an alternative to browser_mod for building dashboards
controllable from Home Assistant, specifically for use with [ViewAssist](https://dinki.github.io/View-Assist/),
but it's effectively a remotely controllable browser.
*It is currently under heavy development and not ready for production use.*

The project consists of two components - the Custom Component in [custom_components](/custom_components) and the gui 
app in [application](/application).

## The Remote Assist Display Custom Component
The custom component should be installed in your Home Assistant instance prior to installing the GUI application.

### Installation
#### With HACS
* Install [HACS](https://hacs.xyz/docs/use/) if you have not already
* Click 
[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.
](https://my.home-assistant.io/badges/hacs_repository.svg)
](https://my.home-assistant.io/redirect/hacs_repository/?owner=michelle-avery&category=integration&repository=remote-assist-display)  
to add this as a custom repository, or add it manually.
* Click "Add" to confirm, and then click "Download" to download and install the integration
* Restart Home Assistant

#### Manual Installation
* Copy the contents of [custom_components/remote_assist_display](/custom_components/remote_assist_display) to 
`config/custom_components/remote_assist_display` in your Home Assistant instance
* Restart Home Assistant

#### For development
* Clone this repository to your local machine, and mount the `custom_components/remote_assist_display` directory 
to `config/custom_components/remote_assist_display` in your Home Assistant instance by adding a mount in your 
devcontainer.json file like this (make sure to change the source to match your environment):
```json
  "mounts": [
      "source=${localENV:HOME}/remote-assist-display/custom_components/remote_assist_display,target=${containerWorkspaceFolder}/config/custom_components/remote_assist_display,type=bind"
  ]
```
#### Completing the installation
There is currently one more step needed as a workaround. Devices running the Remote Assist Display GUI application
should automatically be registered in Home Assistant, but the endpoints for this are currently not being loaded unless a
device already exists. To work around this, you can create a temporary device in Home Assistant. This can be done by going
to Integrations, clicking "Add Integration", searching for "Remote Assist Display", and adding a temporary device. Once
your first device is added, the endpoints will be loaded and you can remove the temporary device.
    
## The Remote Assist Display GUI Application
The GUI application is a Python application that uses Pywebview to display a web page in a window. The application 
connects to HomeAssistant and accepts commands to navigate to different dashboards within home assistant, or different 
URLs altogether. Compared to using the similar browser_mod approach, Remote Assist Display requires more initial setup, 
but removes the need for the user to interact with the display prior to use after a restart.

### Installation

#### From Source
* Clone this repository to your local machine
* Install the required dependencies. This list is a work in progress, so if you find any missing, please open 
an [issue](https://github.com/michelle-avery/remote-assist-display/issues)
  * For debian-based systems:
  `sudo apt-get install pkg-config cmake libcairo2-dev libgirepository1.0-dev 
  python3-gi python3-gi-cairo gir1.2-gtk-3.0 gir1.2-webkit2-4.1`
  * For Alpine-based systems (including Postmarketos):
  `sudo apk add g++ cmake pkgconf py3-cairo-dev gobject-introspection-dev`
  * For all systems:
    * A Python 3.12+ environment
    * [Pipenv](https://pipenv.pypa.io/en/latest/installation.html)
* Run `pipenv install` to install the required Python packages
* Run the application with `pipenv run python main.py`. If you just see a white screen when the application launches
  (this will be the  case with  ThinkSmart View devices, and potentially others as well), preface the command with 
`MESA_GLES_VERSION_OVERRIDE=2.0`

### Configuration
* When the application starts up for the first time, it will prompt you to enter the URL of your Home Assistant 
instance. You will then be directed to that instance to log in.
* Once you've logged in to Home Assistant, you will be redirected to a page that lets you know the device is waiting 
for a configuration. You can now configure the device in Home Assistant.
* Go to Integrations, find the "Remote Assist Display" integration, and click on it. You should see a new device
in addition to the temporary device you previously created. Click on the "Configure" button next to the new device.
* Under "assist_entity_id", select the corresponding assist entity that this display will be used with.
* The "event_type" functionality is not yet fully implemented, so you enter any placeholder text here.
* For "default_dashboard", enter the relative path to the dashboard you'd like to display when the application starts.
* Click submit to save the configuration, which should automatically be picked up by the device.

## Known Issues
This project is still in an early prototype stage. In addition to the usual implications (rapidly chanaging code base, 
little error handling, etc.), there are a few known issues:
* See the workaround above in the installation instructions for the custom component
* Once the application registers itself to home assistant, it currently polls home assistant every 60 seconds until it
finds a configuration with the default dashboard defined. This will be moved to a pub/sub model in the future, but for
now, you'll need to wait up to 60 seconds after configuring the device in Home Assistant for the dashboard to load. Note
that there's also no timeout on this polling, so you probably don't want to leave it in this state indefinitely.
* The devices currently only check for their configuration at startup and during the initial configuration. This means
if you change the configuration in Home Assistant, you'll need to restart the application on the device for the changes
to take effect.