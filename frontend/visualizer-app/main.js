const {app, BrowserWindow, net} = require('electron');
const path = require('path');

function createWindow() {
    const win = new BrowserWindow({
        width: 1000,
        height: 800,
        title: "Naina AI",
        autoHideMenuBar: true,
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: false
        }
    });

    const startUrl = process.env.ELECTRON_START_URL || new URL(`file://${path.join(__dirname, 'out/index.html')}`).toString();
    win.loadURL(startUrl);

    win.webContents.openDevTools();
}

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
    console.log("Intializing graceful shutdown");
    const request = net.request({
        method: 'Post',
      url: 'http://localhost:8000/shutdown'
    });
    request.on('response', (response) => {
        console.log("Shutdown request sent to backend");
        if (process.platform !== 'darwin') {
            app.quit();
        }
    });
    request.on('error', (error) => {
        console.log("request is unreachable to backend")
        if (process.platform !== 'darwin') {
            app.quit();
        }
    });
    request.end();
}); 

