const { app, BrowserWindow } = require('electron');
const path = require('path');

function createWindow () {
  // Yahan win variable ban raha hai
  const win = new BrowserWindow({
    width: 1000,
    height: 800,
    title: "Naina AI",
    autoHideMenuBar: true,
    webPreferences: {
      nodeIntegration: true
    }
  });


  win.loadFile(path.join(__dirname, 'out/index.html'));
}

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});