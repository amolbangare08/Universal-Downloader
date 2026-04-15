const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  startDownload: (args) => ipcRenderer.send('start-download', args),
  stopDownload: () => ipcRenderer.send('stop-download'),
  onPythonOutput: (callback) => {
    ipcRenderer.on('python-output', (_event, msg) => callback(msg));
  },
  onDownloadCanceled: (callback) => {
    ipcRenderer.on('download-canceled', () => callback());
  },
  onDownloadStopped: (callback) => {
    ipcRenderer.on('download-stopped', () => callback());
  },
});
