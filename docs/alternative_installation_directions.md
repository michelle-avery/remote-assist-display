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

## The Remote Assist Display App
### Running the Standalone Executable on the ThinkSmartView with PostmarketOS
### Running the Standalone Executable
Standalone executables for the ThinkSmart View (which theoretically should 
work on any alpine Linux-based arm system) are published with each release. 
These releases take up slightly less disk space and require fewer 
dependencies, but take somewhat longer to start up and are harder to upgrade. 
If, however, hard drive space is a significant constraint, you may want to 
consider this option. TO use it, just download the file, make sure it's 
executable with `chmod +x remote-assist-display-app`, and run it. If you 
encounter any issues, please refer to the troubleshooting section in the documentation.