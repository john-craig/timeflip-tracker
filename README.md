# Timeflip Tracker
An open source Python project to record event information from a [TimeFlip2](https://timeflip.io/) device.

## Installation
The preferred method of installation is through Docker. To run this project using Docker, perform the following steps:

    1) Download the `docker-compose.prod.yaml` file and the `config.example.yaml` file from the root of this repository.
    2) Change the host mapping of the volume bind mount for `/etc/timeflip-tracker/config.yaml` to the location of the configuration file in your filesystem.
    3) Change the host mapping of the volume bind mount for `/var/lib/mysql` and the location of persistent storage for the database.
    4) It is also *strongly recommended* to change the MARIADB_PASSWORD environment variables on both containers to something more secure.

Once these steps have been completed you can run the project with `docker compose -f docker-compose.prod.yaml up`.


## Configuration
Configuration for the Timeflip Tracker is done using the `config.yaml` file. See `config.example.yaml` for an example of this file.

### Adapter (Optional)
This is the MAC address of the bluetooth adapter on the host which will be used to connect to the Timeflip device. This is optional, and if it is not specified the first available bluetooth adapter will be selected automatically.

### Devices
This is a list containing mappings for each Timeflip device you wish for the Tracker to connect to. Using multiple devices simultaneously should work, but is untested.

Each device may have the following fields defined:

 **name**: A human-readable name for the device, mandatory
 **mac_address**: The MAC address of the device, mandatory
 **password**: The device password, mandatory. Note, the default password for a Timeflip device is 0000
 **default_color**: The color to set for facets without an explicitly defined color. Optional, defaults to white. May be set to 'disco' for random colors. See 'Color Parsing' for more details.

Finally, each device will have a list of one or more facets.

### Facets
Facets are defined in order 1-indexed, meaning the first facet in the list is set to facet 1 on the Timeflip device.

Each facet may have the following fields defined:

 **value**: A string for the activity assigned to that facet, mandatory.
 **color**: The color to be set for that facet on the Timeflip device. Optional, defaults to the value set for *default_color* on the device. See 'Color Parsing' for more details.

Currently there is not a way to specify the facet number manually, so if you want to define, say, only facet 8 without defining facets 1-7, just add 7 dummy facets to the list.

#### Color Parsing
Timeflip Tracker uses the [colour](https://pypi.org/project/colour/) library to parse colors specified in its configuration file. Per this library, it supports "RBG, HSL, 6-digit hex, 3-digit hex" as ways to specify colors, as well as [W3C color naming](https://www.w3.org/TR/css-color-3/#svg-color) for semantic colors.

## Usage
The intended use-case for this project is to collect activity data from a Timeflip device and store it in a database. From the database, this information may be queried by other applications, such as Grafana (for which there is an example dashboard here). Currently, this project does not support its own UI for displaying Timeflip activity data, nor are there currently any plans to add such a feature, although pull requests are open.


If the Timeflip device is set onto a facet which is not defined in the configuration, the created event as an activity of "unassigned" and a color of white.
