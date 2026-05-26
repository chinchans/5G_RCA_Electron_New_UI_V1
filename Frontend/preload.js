const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('API', {
    ...(window.API || {}),
    showOpenDirectoryDialog: async (title = 'Select folder') => {
        return await ipcRenderer.invoke('show-open-directory-dialog', { title });
    },
    listFilesInDirectory: async (folderPath) => {
        return await ipcRenderer.invoke('list-files-in-directory', { folderPath });
    },
    launchWifiApp: async () => {
        return await ipcRenderer.invoke('launch-wifi-app');
    }
});
