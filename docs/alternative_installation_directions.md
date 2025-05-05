# Alternative Installation Directions
## The Remote Assist Display Integration
### Manual Installation
If you prefer not to use HACS, you can manually install the Remote Assist
Display integration by following these directions:

* Copy the contents of [custom_components/remote_assist_display](/custom_components/remote_assist_display) to 
`config/custom_components/remote_assist_display` in your Home Assistant instance
* Restart Home Assistant

### Installing for Development Purposes
If you want to install the Remote Assist Display integration for 
development purposes, in order to contribute to the project, you can do so 
by following these directions:

* Clone this repository to your local machine, and mount the `custom_components/remote_assist_display` directory 
to `config/custom_components/remote_assist_display` in your Home Assistant instance by adding a mount in your 
devcontainer.json file like this (make sure to change the source to match your environment):
```json
  "mounts": [
      "source=${localENV:HOME}/remote-assist-display/custom_components/remote_assist_display,target=${containerWorkspaceFolder}/config/custom_components/remote_assist_display,type=bind"
  ]
```

### Customize the Local Storage ID
By default, each device will store its unique id in the `browser_mod-browser-id` key of the browser's local storage. This is intended for ease of compatibility  with ViewAssist, but if you are also using browser mod, and you wish to change this, you can change this default value as well in the configuration, or on a per-system basis. 