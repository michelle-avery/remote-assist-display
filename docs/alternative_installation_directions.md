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

### Creating a Standalone Executable for the ThinkSmart View for development purposes
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