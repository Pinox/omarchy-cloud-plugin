# Quick local installation

This folder is a local copy of the Cloud plugin. Use these commands to install
it in Omarchy while the upstream pull request is pending.

```bash
PLUGIN_SOURCE="/home/jtm/Cloud/onedrive/Documents/Sync/Omarchy/Cloud Plugin"
PLUGIN_ID="furmware.cloud"
PLUGIN_DIR="$HOME/.config/omarchy/plugins/$PLUGIN_ID"

# Install rclone if it is not already available.
command -v rclone >/dev/null 2>&1 || omarchy pkg add rclone

# Check the copied plugin before putting it in Omarchy's plugin directory.
omarchy plugin validate "$PLUGIN_SOURCE"
mkdir -p "$HOME/.config/omarchy/plugins"

# Keep a timestamped backup if an older local copy is already installed.
if [[ -e "$PLUGIN_DIR" || -L "$PLUGIN_DIR" ]]; then
  omarchy plugin disable "$PLUGIN_ID" 2>/dev/null || true
  mv "$PLUGIN_DIR" "$PLUGIN_DIR.backup.$(date +%Y%m%d-%H%M%S)"
fi

cp -a "$PLUGIN_SOURCE"/. "$PLUGIN_DIR"/
omarchy-shell shell rescanPlugins
omarchy plugin enable "$PLUGIN_ID"
```

After installation, click the Cloud icon in the Omarchy bar to connect or
import a service. The copied plugin includes the current OneDrive recovery,
rclone configuration, import deletion, and duplicate cleanup flows.

To update later, copy the newest plugin files into the same source folder and
repeat the commands above. The previous installed copy is kept as a backup.
