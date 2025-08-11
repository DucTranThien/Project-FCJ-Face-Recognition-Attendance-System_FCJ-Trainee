---
title: "Install Python"
date: "" 
weight: 1 
chapter: false
pre: " <b> 2.1.1 </b> "
---

#### Download and install Python 3.13.5 for Windows

1. Go to the official [Python download page](https://www.python.org/downloads/windows/)

2. Click the yellow **Download Python 3.13.5** button at the top of the page.

3. After the `.exe` file is downloaded, double-click it to launch the installer.

4. **Important:** Check the box **“Add Python to PATH”** at the bottom of the installer window.

5. Click **Install Now** and wait for the installation to complete.

6. After installation, open **Command Prompt (CMD)** and run:

{{< copycode >}}
python --version
{{< /copycode >}}

Then check pip:

{{< copycode >}}
pip --version
{{< /copycode >}}

Both commands should return the installed versions of Python and pip.
