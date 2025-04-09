# Remote Assist Display
This project is meant to be an alternative to browser_mod for building dashboards
controllable from Home Assistant, specifically for use with [ViewAssist](https://dinki.github.io/View-Assist/),
but it's effectively a remotely controllable browser.

The project consists of two components - the Custom Component in [custom_components](/custom_components) and the gui 
app in [application](/application). In order to effectively use RAD, you'll need to install BOTH components. Below are the recommended
methods of installing the application, but for alternatives, see the [alternative installation directions](/docs/alternative_installation_directions.md).

## QuickStart
### Install the Integration With HACS
* Install [HACS](https://hacs.xyz/docs/use/) if you have not already
* Click 
[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.
](https://my.home-assistant.io/badges/hacs_repository.svg)
](https://my.home-assistant.io/redirect/hacs_repository/?owner=michelle-avery&category=integration&repository=remote-assist-display)  
to add this as a custom repository, or add it manually.
* Click "Add" to confirm, and then click "Download" to download and install the integration
* Restart Home Assistant
* After the reboot, add the integration via the integrations dashboard or click here: [![Open](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=remote_assist_display). 

It's possible to set default dashboards on a per-device basis, but if you'd like to use the default dashboard on all of your devices,
you can sest that now from the integration's configuration page. Otherwise, new devices added will default to using the default
lovelace dashboard, and can be individually changed.

### Install the Remote Assist Display GUI Application
The method you using to install the GUI application on your device depends
on the operating system. If your system is running an Android-based operating system (ie, 
Android, Lineage, etc.), use the "From APK" section. If your system is running a 
Linux-based operating system (ie, Ubuntu, raspbian, postmarketos, etc.), use the "From 
Source" section. Once installation is complete, continue to the "Configuration" section.

#### From APK
* From your Android device, download the latest apk from the (releases)[https://github.com/michelle-avery/remote-assist-display/releases] page.
* Install the apk. You may need to enable "Install from Unknown Sources" in your device's settings.

#### From Source
* Install the required dependencies.
  * For debian-based systems:
    `sudo apt-get install pkg-config cmake libcairo2-dev libgirepository1.0-dev python3-gi python3-gi-cairo gir1.2-gtk-3.0 gir1.2-webkit2-4.1 python3-dev git`
  * For Alpine-based systems (including Postmarketos):
    `sudo apk add g++ cmake pkgconf py3-cairo-dev gobject-introspection-dev python3-dev git`
  * For all systems:
    * A Python 3.12+ environment
    * [Pipenv](https://pipenv.pypa.io/en/latest/installation.html) (on many systems, this can easily be installed by installing pipx from your package manager, and then running `pipx install pipenv`)
* Clone this repository to your local machine
  * `cd ~/`
  * `git clone https://github.com/michelle-avery/remote-assist-display.git`
  * `cd remote-assist-display/application/`
* Run `pipenv install` to install the required Python packages
* Run the application with `pipenv run python main.py`. If you just see a white screen when 
the application launches (this will be the  case with  ThinkSmart View devices, and 
potentially others as well), preface the command with `MMESA_GLES_VERSION_OVERRIDE=2.0`
* See [here](/docs/start-rad.sh) for a script that can be used to start the application with the correct parameters.

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