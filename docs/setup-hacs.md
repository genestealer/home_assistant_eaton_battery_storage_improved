# HACS
HACS is an integration that will enable downloading the integration from xStorage Home. A GitHub account is required.

[Click here to install the HACS integration](https://my.home-assistant.io/redirect/supervisor_addon/?addon=cb646a50_get&repository_url=https%3A%2F%2Fgithub.com%2Fhacs%2Faddons)

Click on **Open link** to download the extension into your Home Assistant setup.

![Install](../images/ha-open.png "Install HACS")

## Download and install Get HACS into your Home Assistant

This step will ensure that you can successfully install HACS, which will enable to add the eaton_battery_storage extension.

- Accept the download, when prompted. The modal content might be slightly different based on your setup.

    ![Accept](../images/get-hacs-install-confirmation.png "Accept HACS download")

- Install the Get HACS integration

    ![HACS Installed](../images/hacs-install.png "Get HACS")

- Start the integration, by clicking on **start**

    ![Run](../images/get-hacs-run.png "Run get HACS")

- Navigate to the log tab and make sure the download was completed.
- Restart your Home Assistant, navigate to **Settings** and use the more button (3 dots) on the top right corner:

    ![Restart](../images/ha-restart.png "Home Assistant Restart")

- Clear your browser cache, while Home Assistant is restarting (login required after the operation). **This step is mandatory**.

## Install HACS
In the previous step, you successfully installed the Get HACS extension. Please make sure to read the logs as explained before, in order to be sure to continue.

- Navigate to **Settings** > **Devices & services**. In the bottom right corner, select **+ Add integration**.
- Search for HACS and click on the integration.

    ![Install HACS](../images/hacs-install-integration.png "Install HACS")

- Accept all the disclaimers after carefully reading them.

    ![Disclaimer](../images/hacs-disclaimer.png "Disclaimer")

## Device activation
Please make sure to have a Github account, the basic plan is free for individuals and organizations. This step will ensure you can install the eaton_battery_storage integration in your Home Assistant.

Before being redirected to GitHub, you will see the following information : 

![Device Activation](../images/hacs-github-code.png "Device Activation")

Follow the instructions in the modal.

1. Enter the key provided by Home Assistant before.
    
    ![Activation code](../images/hacs-configuration-device-activation.png "Enter your activation code")

- Click on **Continue**

    ![Continue](../images/hacs-configuration-continue.png "Continue")

- Authorize HACS to access your GitHub account

    ![Restart](../images/hacs-configuration-authorize.png "Home Assistant Restart")

- Congrats, you finished the HACS setup on GitHub!

    ![Success](../images/github-wizard-success.png "Success")

## FInalize HACS installation

Select a zone to add to your HACS integration and click on **Finish**.

![Zone](../images/hacs-configuration-final.png "Zone")

---
Next: [Install and configure eaton_battery_storage integration](setup-eaton-battery-storage-integration.md)