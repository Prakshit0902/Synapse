const { app, BrowserWindow, net } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let backendProcess = null;
let mainWindow = null; // Global reference for IPC communication

function startBackend() {
    let backendExecutable;
    let backendArgs = []; // 👈 Ye array bohot zaroori hai
    let cwd;

    if (app.isPackaged) {
        // 🚀 PRODUCTION MODE: Run packaged main.exe
        backendExecutable = path.join(process.resourcesPath, 'naina_backend', 'main.exe');
        cwd = path.join(process.resourcesPath, 'naina_backend');
        console.log(`[PROD] Starting: ${backendExecutable}`);
   } else {
        // 🛠️ DEVELOPMENT MODE: Run as a Python module with full logs
        const rootDir = path.join(__dirname, '../../'); // Trinetra_Vision root
        backendExecutable = path.join(rootDir, 'python/synapse_env/Scripts/python.exe');
        backendArgs = ['-m', 'python.engine.main'];
        cwd = rootDir;

        // 👇 Ye logs tujhe console me ek-ek cheez clear dikhayenge
        console.log("\n==========================================");
        console.log(`[DEBUG] ROOT DIRECTORY : ${cwd}`);
        console.log(`[DEBUG] PYTHON EXE     : ${backendExecutable}`);
        console.log(`[DEBUG] FULL COMMAND   : ${backendExecutable} ${backendArgs.join(' ')}`);
        console.log("==========================================\n");
    }

    try {
        // 👇 Env var me PYTHONPATH daal diya taaki import error aaye hi na
        const processEnv = { ...process.env, PYTHONPATH: cwd };
        backendProcess = spawn(backendExecutable, backendArgs, { cwd: cwd, env: processEnv });

        backendProcess.stdout.on('data', (data) => {
            const msg = data.toString();
            console.log(`[Backend] ${msg}`);

            // 🍎 MAGIC LOGIC: Tell UI when downloading starts/finishes
            if (mainWindow && !mainWindow.isDestroyed()) {
                const lowerMsg = msg.toLowerCase();
                if (lowerMsg.includes('downloading') || lowerMsg.includes('fetching')) {
                    mainWindow.webContents.send('backend-status', 'Downloading AI Models... Please keep internet ON.');
                }
                if (lowerMsg.includes('model loaded successfully') || lowerMsg.includes('engine initialized')) {
                    mainWindow.webContents.send('backend-status', 'Download Complete! Booting Engine...');
                }
            }
        });

        backendProcess.stderr.on('data', (data) => {
            console.error(`[Backend Error] ${data}`);
        });

        backendProcess.on('close', (code) => {
            console.log(`[Backend] exited with code ${code}`);
        });
    } catch (error) {
        console.error("Failed to start backend process:", error);
    }
}

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1000,
        height: 800,
        title: "Naina AI",
        icon: path.join(__dirname, 'icon.ico'),
        backgroundColor: '#050505',
        show:false,
        autoHideMenuBar: true,
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: false
        }
    });

    mainWindow.once('ready-to-show', () => {
        mainWindow.show();
    });
    const startUrl = process.env.ELECTRON_START_URL || new URL(`file://${path.join(__dirname, 'out/index.html')}`).toString();
    mainWindow.loadURL(startUrl);
}

app.whenReady().then(() => {
    // Window pehle create karo taaki pehle second ke messages miss na ho
    createWindow();
    startBackend();
});

app.on('window-all-closed', () => {
    console.log("Initializing graceful shutdown...");

    const request = net.request({
        method: 'POST',
        url: 'http://localhost:8000/shutdown'
    });

    request.on('response', (response) => {
        console.log("Shutdown request sent to backend successfully.");
        if (backendProcess) backendProcess.kill();
        if (process.platform !== 'darwin') app.quit();
    });

    request.on('error', (error) => {
        console.log("Backend is unreachable, forcing close...");
        if (backendProcess) backendProcess.kill();
        if (process.platform !== 'darwin') app.quit();
    });

    request.end();
});