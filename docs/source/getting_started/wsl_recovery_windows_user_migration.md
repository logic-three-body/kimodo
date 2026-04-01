# WSL Recovery After Windows User Migration

This page documents a recovery workflow for a Windows machine where:

- a WSL distro disappeared after switching from one Windows user profile to another
- the distro data still existed on disk as an `ext4.vhdx`
- VS Code Insiders could reconnect to WSL, but OpenAI/Codex features failed because WSL networking and proxy settings were stale

Although the concrete paths and usernames will vary across machines, the failure pattern is common for Windows user migrations.

## Symptoms

Typical symptoms in this scenario include:

- `wsl -l -v` shows no registered distros for the new Windows user
- the distro data is still present on disk, for example `D:\WSL\Ubuntu-20.04\ext4.vhdx`
- `wsl --import-in-place ... ext4.vhdx` fails with `Wsl/Service/RegisterDistro/MountDisk/HCS/E_ACCESSDENIED`
- Explorer or VS Code can no longer access `/root`
- VS Code Insiders in WSL shows errors such as `stream disconnected before completion`
- WSL networking is broken and `ip addr` shows only `lo`
- requests from inside WSL fail because the proxy inherited from Windows is unreachable

## Root causes

### 1. WSL registration is per Windows user

WSL distro registrations live under the current Windows user's registry hive:

`HKCU\Software\Microsoft\Windows\CurrentVersion\Lxss`

After switching Windows users, the distro may still exist on disk but appear missing because the new user has no registration entry.

### 2. The original VHDX may still belong to the old Windows user

If the on-disk `ext4.vhdx` is still owned by the old Windows user, `wsl --import-in-place` can fail with `E_ACCESSDENIED`.

### 3. `/root` access depends on the Linux default user

Access to `/root` is normal only when the WSL distro is entered as Linux `root`. If the default distro user changes to a non-root user, `\\wsl$\<distro>\root` will appear inaccessible.

### 4. `mirrored` networking can fail on some machines

In this recovery, WSL booted with only a loopback interface and no default route. Kernel logs showed repeated `hv_netvsc ... unable to open channel: -19`, which left the distro without working network access.

### 5. Loopback proxy settings do not always work inside WSL

VS Code remote processes inherited proxy variables such as:

```bash
HTTP_PROXY=http://127.0.0.1:7897
HTTPS_PROXY=http://127.0.0.1:7897
```

That only works when the Windows proxy is reachable from WSL through loopback. If the proxy is bound only to the Windows loopback interface, WSL-side requests can fail even though the proxy works in native Windows apps.

## Recovery procedure

### 1. Verify that the distro data still exists

First confirm that the VHDX is still present and that the current Windows user has no registered distro:

```powershell
Get-ChildItem D:\WSL\Ubuntu-20.04
wsl -l -v
```

If the VHDX exists but the distro list is empty, the data is likely intact and only the registration is missing.

### 2. Re-register the distro

Try the normal in-place import first:

```powershell
wsl --shutdown
wsl --import-in-place Ubuntu-20.04 D:\WSL\Ubuntu-20.04\ext4.vhdx
```

If this fails with `E_ACCESSDENIED`, inspect the VHDX owner. When the file still belongs to the old Windows user and changing ownership is inconvenient, create a copy owned by the current user and import that copy instead:

```powershell
robocopy D:\WSL\Ubuntu-20.04 D:\WSL\Ubuntu-20.04-<new-user> ext4.vhdx /J /COPY:DAT /DCOPY:DAT /R:0 /W:0
wsl --import-in-place Ubuntu-20.04 D:\WSL\Ubuntu-20.04-<new-user>\ext4.vhdx
```

Then verify:

```powershell
wsl -l -v
```

### 3. Restore the expected Linux default user

Check the Linux users inside the restored distro:

```powershell
wsl -d Ubuntu-20.04 -u root -- getent passwd 0
wsl -d Ubuntu-20.04 -u root -- getent passwd 1000
wsl -d Ubuntu-20.04 -u root -- ls /home
```

If the previous workflow lived under `/root`, restore that behavior explicitly:

```powershell
wsl --manage Ubuntu-20.04 --set-default-user root
```

If the workflow should use a normal Linux user instead:

```powershell
wsl --manage Ubuntu-20.04 --set-default-user <linux-user>
```

Optionally make this distro the default:

```powershell
wsl -s Ubuntu-20.04
```

### 4. Recover WSL networking

If WSL only has loopback networking:

```powershell
wsl -d Ubuntu-20.04 -- ip addr
wsl -d Ubuntu-20.04 -- ip route
```

and `dmesg` contains messages like:

```text
hv_netvsc ... unable to open channel: -19
```

switch from mirrored networking to NAT in the Windows-side WSL config:

`C:\Users\<windows-user>\.wslconfig`

```ini
[wsl2]
networkingMode=nat
```

Apply the change:

```powershell
wsl --shutdown
```

After restarting WSL, verify that the distro has a real network interface and a default route:

```powershell
wsl -d Ubuntu-20.04 -- ip addr
wsl -d Ubuntu-20.04 -- ip route
wsl -d Ubuntu-20.04 -- cat /etc/resolv.conf
```

At this point, `eth0` should exist and DNS should be generated again.

### 5. Make the Windows proxy reachable from WSL

When using Clash Verge / Mihomo, enable LAN access so the Windows proxy is reachable from WSL:

- enable `Allow LAN`
- restart the Clash core after changing the setting
- allow the app through Windows Firewall if prompted

The relevant host-side config is usually:

`C:\Users\<windows-user>\AppData\Roaming\io.github.clash-verge-rev.clash-verge-rev\config.yaml`

with:

```yaml
allow-lan: true
```

### 6. Point VS Code Insiders remote sessions at the reachable proxy

If direct outbound requests from WSL time out, but the Windows proxy is working, inject the reachable proxy address into VS Code Server startup.

Create or update:

`~/.vscode-server-insiders/server-env-setup`

```sh
#!/bin/sh
PROXY_URL="http://<windows-host-ip>:7897"
export HTTP_PROXY="$PROXY_URL"
export HTTPS_PROXY="$PROXY_URL"
export ALL_PROXY="$PROXY_URL"
export http_proxy="$PROXY_URL"
export https_proxy="$PROXY_URL"
export all_proxy="$PROXY_URL"
```

Also set the machine-level VS Code remote proxy:

`~/.vscode-server-insiders/data/Machine/settings.json`

```json
{
  "http.proxy": "http://<windows-host-ip>:7897",
  "http.proxySupport": "override"
}
```

Find `<windows-host-ip>` from the active Windows network adapter, for example with `ipconfig`.

### 7. Reconnect VS Code Insiders

Once WSL networking and proxy settings are fixed:

- fully close the current VS Code Insiders WSL window
- reconnect to the WSL distro
- reopen the project directory

Example:

```powershell
code-insiders --remote wsl+Ubuntu-20.04 /root/Project/Kimodo
```

If `code-insiders` is not on `PATH`, use the full path to `code-insiders.cmd`.

## Validation checklist

Use the following checks to confirm the recovery:

```powershell
wsl -l -v
wsl -- whoami
wsl -d Ubuntu-20.04 -- ip addr
wsl -d Ubuntu-20.04 -- getent hosts chatgpt.com
```

Then validate the proxy path from inside WSL:

```bash
curl -I -x http://<windows-host-ip>:7897 https://chatgpt.com/backend-api/codex/responses
```

An HTTP response from that endpoint is a good sign. For example, a `405 Method Not Allowed` response to a `HEAD` request still confirms that the request reached the OpenAI service successfully.

## Notes from this recovery

This specific recovery established the following lessons:

- the restored distro data originated from `D:\WSL\Ubuntu-20.04\ext4.vhdx`
- because the original VHDX was owned by the previous Windows user, the imported disk ultimately came from a copied VHDX owned by the current user
- access to `/root` was restored by setting the distro default Linux user back to `root`
- `networkingMode=mirrored` was unstable on this machine, while `networkingMode=nat` restored `eth0`, routing, and DNS
- the VS Code Insiders OpenAI/Codex integration depended on a proxy that was reachable from WSL, not just from native Windows applications
