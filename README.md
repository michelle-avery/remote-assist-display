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
* Click [![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=michelle-avery&category=integration&repository=remote-assist-display)  to add this as a custom repository, or add it manually.
* Click "Add" to confirm, and then click "Download" to download and install the integration
* Restart Home Assistant

#### Manual Installation
* Copy the contents of [custom_components/remote_assist_display](/custom_components/remote_assist_display) to `config/custom_components/remote_assist_display` in your Home Assistant instance
* Restart Home Assistant

#### For development
* Clone this repository to your local machine, and mount the `custom_components/remote_assist_display` directory to `config/custom_components/remote_assist_display` in your Home Assistant instance by adding a mount in your devcontainer.json file like this (make sure to change the source to match your environment):
```json
  "mounts": [
      "source=${localENV:HOME}/remote-assist-display/custom_components/remote_assist_display,target=${containerWorkspaceFolder}/config/custom_components/remote_assist_display,type=bind"
  ]
```
Once you  have the  component installed, you can proceed to install the GUI application on the device you wish to use as a remote display.
    

## Requirements
pkg-config 
cmake
libcairo2-dev
libgirepository1.0-dev
python3-gi 
python3-gi-cairo 
gir1.2-gtk-3.0 
gir1.2-webkit2-4.1
