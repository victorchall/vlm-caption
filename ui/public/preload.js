const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('api', {
  receive: (channel, func) => {
    const validChannels = ['set-api-port', 'update-available', 'update-not-available', 'update-downloaded', 'update-error', 'checking-for-update', 'download-progress'];
    if (validChannels.includes(channel)) {
      // Deliberately strip event as it includes `sender`
      ipcRenderer.on(channel, (event, ...args) => func(...args));
    }
  },
  send: (channel, data) => {
    const validChannels = ['check-for-updates', 'download-update', 'quit-and-install'];
    if (validChannels.includes(channel)) {
      ipcRenderer.send(channel, data);
    }
  },
});
