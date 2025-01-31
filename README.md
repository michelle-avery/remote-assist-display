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
Once the component is in place, add it via the integrations dashboard or click here: [![Open](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=remote_assist_display). 
It's possible to set default dashboards on a per-device basis, but if you'd like to use the default dashboard on all of your devices,
you can sest that now from the integration's configuration page. Otherwise, new devices added will default to using the default
lovelace dashboard, and can be individually changed.

By default, each device will store its unique id in the `browser_mod-browser-id` key of the browser's local storage. This is intended for ease of compatibility  with ViewAssist, but if you are also using browser mod, and you wish to change this, you can change this default value as well in the configuration, or on a per-system basis. 
    
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
  python3-gi python3-gi-cairo gir1.2-gtk-3.0 gir1.2-webkit2-4.1 python3-dev`
  * For Alpine-based systems (including Postmarketos):
  `sudo apk add g++ cmake pkgconf py3-cairo-dev gobject-introspection-dev python3-dev`
  * For all systems:
    * A Python 3.12+ environment
    * [Pipenv](https://pipenv.pypa.io/en/latest/installation.html) (on many systems, this can easily be installed by installing pipx from your package manager, and then running `pipx install pipenv`)
* Run `pipenv install` to install the required Python packages
* Run the application with `pipenv run python main.py`. If you just see a white screen when the application launches
  (this will be the  case with  ThinkSmart View devices, and potentially others as well), preface the command with 
`MESA_GLES_VERSION_OVERRIDE=2.0`

### Running the Standalone Executable
Standalone executables for the ThinkSmart View (which theoretically should work on any alpine-based arm system) are
published with each release. Just download the file, make sure it's executable with `chmod +x remote-assist-display-app`,
and run it.

### Creating a Standalone Executable for the ThinkSmart View
The ThinkSmart View devices have become popular for applications like this due to their currently low price point.
These devices can also be flashed to run PostmarketOS, which allows for more flexibility in the applications that can
be installed. Given the limited disk space on these devices, and the additional dependencies needed, however, this
project provides the ability to create a standalone executable that can be run on the device without needing to install
dependencies, check out the repository, etc. This will eventually be published with each release, but if you'd like to
create your own in the interim, and you have docker installed on a workstation:
* Clone this repository to your local machine
* The ThinkSmart Views run on ARM processors, so assuming your workstation is x86, you'll need to enable quemu
  emulation. This can be done by running `docker run --rm --privileged multiarch/qemu-user-static --reset -p yes`
* Run `docker build --platform linux/arm64 . -t rad-builder` to build the builder image
* From the application directory, run `docker run --rm -v $(pwd):/usr/src/app --platform linux/arm64 rad-builder` 
to build the standalone executable. This will create a file called `remote-assist-display-app` in the `dist` directory under
your current directory.
* Copy the `remote_assist_display` file to your ThinkSmart View device, and run it with 
`MESA_GLES_VERSION_OVERRIDE=2.0 ./remote-assist-display-app`

### Configuration
* When the application starts up for the first time, it will prompt you to enter the URL of your Home Assistant 
instance. You will then be directed to that instance to log in.
* Once you've logged in to Home Assistant, you will be redirected the default dashboard - either the one you've set
at the integration level, or "lovelace" if none is set.
* Go to Integrations, find the "Remote Assist Display" integration, and click on it. You should see your new device.
Click on that device and look for the section at the top that says "Controls", with an input box for "Default 
Dashboard". Type in the name of the default dashboard for that device. It will be saved and the device will be updated
as soon as that text box loses focus (so click somewhere else on the page, hit tab, etc.).

## Usage

### Services
The integration provides two services:
* `remote_assist_display.navigate` is meant to be a browser-mod-compatible service. It takes a target (the device),
and a path (relative to your home assistant base URL).
* `remote_assist_display.navigate_url` is different in that it can accept any URL, not just a home assistant one.

### Event Bus Integration
The integration has the ability to listen to the event bus for messages containing conversation
responses from a specific device (ie, the assist satellite to which your Remote Assist Display 
is paired) and update an automatically-create sensor with the result of the conversation. This
does require the usage of a conversation component that emits assist pipeline events to the 
service bus, which Home Assistant does not natively do. 
[This](https://github.com/michelle-avery/custom-conversation) conversation component can be 
used either as-is, or as an example for modifying a conversation component of your own. If 
[this](https://github.com/home-assistant/core/pull/136083) PR gets merged, this project will be 
updated to work with that by default.

To configure this, go to the Remote Assist Display integration's Configuration page and set the 
event_type you want your devices to listen to (for the custom conversation integration, this will 
be custom_conversation_conversation_ended). On each Remote Assist Display Device's device page
select the corresponding Assist Satellite in the dropdown. 

### Environment Variable Configuration (Linux Only)

Linux installs  support some customization via environment variables. The following are available:


| Variable Name | Description | Default |
| ------------- | ------------- | -------------
| `LOG_LEVEL` | The level of application logging (e.g., DEBUG, INFO, WARNING, ERROR). | INFO, except on Android, which currently defaults to DEBUG.
| `FLASK_DEBUG` | Turns on Flask debugging in the webview. | False
| `FULLSCREEN` | Launches the webview window in fullscreen. | True
| `WEBVIEW_DEBUG` | Launches a devtools window for debugging purposes. | False
| `TOKEN_RETRY_LIMIT` | The number of times the application will attempt to fetch a valid token from the frontend before giving up. | 10
| `MAC_ADDRESS` | The mac address of the system. Used to determine the unique id if one is not set. | The mac address detected by the application. Note that if MAC address randomization is being used on the system, this will result in a different mac address being detected every time the system is rebooted.
| `HOSTNAME` | The hostname of the  system. Used by default in the unique id | The actual hostname detected by the application. 
| `UNIQUE_ID` | The unique id used to identify this device in Home Assistant. This is also the value set in the browser's localStorage in order for dashboards to detect which device they are being displayed on. | remote-assist-display-MAC_ADDRESS-HOSTNAME
| `LOG_DIR` | The directory where logs are stored. | On source-based installs, this is the "application" directory. On pyinstaller-based installs, this will be the same directory as the executable. On Android, it's the appdata folder for the application.
| `CONFIG_DIR` | The directory where the configuration file is stored | The same as above.

### Using with ViewAssist
* Set up Remote Assist Display on your device, per the installation directions. You need to do 
this and connect it to your Home Assistant instance in order to create the entities you'll need 
for the rest of these directions.
* In your Home Assistant `configuration.yaml` file, create a ViewAssist template sensor (or 
modify an existing one) according the the ViewAssist directions, and use the following values:
  - `mic_device` - if you're using this with an Assist Satellite (ie, Wyoming, or an ESP-based 
  voice satellite) should be your `assist_satellite` entity.
  - `display_device` - Set this to the `current_url` sensor entity of your Remote Assist Display.
  - `browser_id` - This is the unique id of the  device. Unless you've set something different, 
  it will be in the format of `remote-assist-display-<mac address with no separators>-<hostname>
* Currently, ViewAssist calls the `browser_mod.navigate` service to navigate from one dashboard 
to another. You need to change this to use the `remote_assist_display.navigate` service instead. 
You can do this either by creating a copy of the ViewAssist Device Control Blueprint with that 
value changed or taking control of the automation created by the blueprint (keep in mine this 
won't let you easily update later) and changing specifically for a device's automation. The RAD 
service maintains the same API as the browser_mod one, so you don't need to change anything else, 
just the service name. You may also need to change it in other blueprints that you have installed.
* If you're using a wyoming satellite, you have two options for configuring the intent sensor:
  - You can run the Wyoming Intent Update from [here](https://github.com/michelle-avery/
  wyoming-intent-updater). This should work regardless of which conversation component you use, 
  but it will not give you the ability to use the "intent" dashboard (that's the one that, when 
  you tell it to turn on a light, shows the light on the dashboard so that you can turn it off, 
  adjust the brightness, etc.).
  - Use [this](https://github.com/michelle-avery/custom-conversation) custom conversation agent, 
  or another that publishes handled intents to the event bus, and follow the directions above 
  under "Event Bus Integration". If you use this option, your Intent Sensor will be the Intent 
  Sensor for your RAD device. 

## Known Issues
This project is still in an early prototype stage. In addition to the usual implications (rapidly 
changing code base, little error handling, etc.), there are some known 
[issues](https://github.com/michelle-avery/remote-assist-display/issues).