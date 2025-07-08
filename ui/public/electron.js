const { app, BrowserWindow, dialog } = require('electron');
const { spawn } = require('child_process');
const path = require('path');
const isDev = require('electron-is-dev');
const waitOn = require('wait-on');

let mainWindow;
let backendProcess;
const BACKEND_PORT = 5000;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      enableRemoteModule: false,
      webSecurity: true
    },
    icon: path.join(__dirname, 'icon.ico'),
    show: false
  });

  // Load the React app
  const startUrl = isDev 
    ? 'http://localhost:3000' 
    : `file://${path.join(__dirname, '../build/index.html')}`;
  
  mainWindow.loadURL(startUrl);

  // Show window when ready to prevent visual flash
  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
  });

  // Open DevTools in development
  if (isDev) {
    mainWindow.webContents.openDevTools();
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

function startBackend() {
  return new Promise((resolve, reject) => {
    let backendPath;
    
    if (isDev) {
      // In development, run the Flask app directly
      backendPath = path.join(__dirname, '../../app.py');
      backendProcess = spawn('python', [backendPath], {
        cwd: path.join(__dirname, '../..')
      });
    } else {
      // In production, run the packaged executable
      backendPath = path.join(__dirname, 'backend', 'app.exe');
      backendProcess = spawn(backendPath, [], {
        cwd: path.join(__dirname, 'backend')
      });
    }

    backendProcess.stdout.on('data', (data) => {
      console.log(`Backend stdout: ${data}`);
    });

    backendProcess.stderr.on('data', (data) => {
      console.log(`Backend stderr: ${data}`);
    });

    backendProcess.on('error', (error) => {
      console.error('Failed to start backend:', error);
      reject(error);
    });

    backendProcess.on('close', (code) => {
      console.log(`Backend process exited with code ${code}`);
    });

    // Wait for the backend to be ready
    waitOn({
      resources: [`http://localhost:${BACKEND_PORT}/api/health`],
      delay: 1000,
      interval: 100,
      timeout: 30000
    }).then(() => {
      console.log('Backend is ready');
      resolve();
    }).catch((error) => {
      console.error('Backend failed to start:', error);
      reject(error);
    });
  });
}

function stopBackend() {
  if (backendProcess) {
    console.log('Stopping backend process...');
    backendProcess.kill();
    backendProcess = null;
  }
}

app.whenReady().then(async () => {
  try {
    // Start the backend first
    await startBackend();
    
    // Then create the window
    createWindow();
  } catch (error) {
    console.error('Failed to start application:', error);
    dialog.showErrorBox('Startup Error', 'Failed to start the backend server. Please check the logs.');
    app.quit();
  }

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  stopBackend();
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('before-quit', () => {
  stopBackend();
});

// Handle any unhandled promise rejections
process.on('unhandledRejection', (reason, promise) => {
  console.error('Unhandled Rejection at:', promise, 'reason:', reason);
});
