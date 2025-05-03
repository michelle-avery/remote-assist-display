# Remote Assist Display
This project is meant to be an alternative to browser_mod for building dashboards
controllable from Home Assistant, specifically for use with [ViewAssist](https://dinki.github.io/View-Assist/).

The project consists of two components - the Custom Component in [custom_components](/custom_components) and the gui 
[app](https://github.com/michelle-avery/rad-cross-platform/). In order to effectively use RAD, you'll need to install BOTH components. The application directory still contains an older version of the app which will soon be deprecated. Below are the recommended
methods of installing the Home Assistant integration, but for alternatives, see the [alternative installation directions](/docs/alternative_installation_directions.md). For instructions on installing the application, please refer to that repo.

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


### Configuration
* Once you've installed the application on a device, go to Integrations, find the "Remote Assist Display" integration, and 
click on it. You should see your new device. Click on that device and look for the section at the top that says "Controls", 
with an input box for "Default Dashboard". Type in the name of the default dashboard for that device. It will be saved and 
the device will be updated as soon as that text box loses focus (so click somewhere else on the page, hit tab, etc.).

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