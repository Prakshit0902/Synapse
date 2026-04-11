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
    console.log("Intializing graceful shutdown");
    const request  = net.request({
        method:'Post',
        url : 'http://localhost:8000/shutdown'
    });
    request.on('response',(response) => {
        console.log("Shutdown request sent to backend");
        if(process.platform !== 'darwin') {
            app.quit();
    })
    request.on('error', (error) => {
        console.log("request is unreachable to backend")
        i
    })
}); 

